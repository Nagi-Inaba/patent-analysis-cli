from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from patent_analysis import describe_capabilities, get_public_schema, run_analysis_csv
from patent_analysis.analyses import matrix as matrix_module
from patent_analysis.analyses.matrix import (
    MatrixBudgetError,
    analyze_matrix,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/cli/matrix"


@dataclass(frozen=True)
class Row:
    source_ordinal: int
    values: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True)
class Population:
    rows: tuple[Row, ...]


def population(*rows: Mapping[str, tuple[str, ...]]) -> Population:
    return Population(tuple(Row(index, value) for index, value in enumerate(rows, start=1)))


def data_from_result(value):
    if hasattr(value, "payload"):
        value = value.payload
    if isinstance(value, bytes):
        value = json.loads(value)
    if hasattr(value, "to_dict") and not isinstance(value, dict):
        value = value.to_dict()
    if not isinstance(value, dict):
        value = dict(value)
    if value.get("ok") is False:
        raise AssertionError(value)
    return value.get("data", value)


def test_matrix_cartesian_pairing_and_cell_order() -> None:
    result = analyze_matrix(
        population(
            {"x": ("A", "B"), "y": ("1", "2")},
            {"x": ("A",), "y": ("1",)},
        ),
        {
            "x_role": "x",
            "y_role": "y",
            "x_limit": 10,
            "y_limit": 10,
            "include_axis_other": False,
            "measure": "count",
        },
    )

    assert [item["label"] for item in result["x_axis"]["categories"]] == [
        "A",
        "B",
    ]
    assert [item["label"] for item in result["y_axis"]["categories"]] == [
        "1",
        "2",
    ]
    assert [
        (cell["x_index"], cell["y_index"], cell["value"], cell["row_count"])
        for cell in result["cells"]
    ] == [
        (0, 0, 2, 2),
        (1, 0, 1, 1),
        (0, 1, 1, 1),
        (1, 1, 1, 1),
    ]


def test_axis_ranking_is_row_occurrence_then_codepoint_order() -> None:
    result = analyze_matrix(
        population(
            {"x": ("B", "B", "A"), "y": ("Y",)},
            {"x": ("B", "A"), "y": ("Y",)},
        ),
        {
            "x_role": "x",
            "y_role": "y",
            "x_limit": 10,
            "y_limit": 10,
            "include_axis_other": False,
            "measure": "count",
        },
    )

    assert result["x_axis"]["categories"] == [
        {"label": "A", "count": 2, "is_other": False},
        {"label": "B", "count": 2, "is_other": False},
    ]


def test_other_projection_is_fixed_deduped_and_only_added_when_used() -> None:
    result = analyze_matrix(
        population(
            {"x": ("A", "B", "C"), "y": ("1",)},
            {"x": ("A",), "y": ("1",)},
        ),
        {
            "x_role": "x",
            "y_role": "y",
            "x_limit": 1,
            "y_limit": 1,
            "include_axis_other": True,
            "measure": "count",
        },
    )

    assert [item["label"] for item in result["x_axis"]["categories"]] == [
        "A",
        "その他（上位外）",
    ]
    assert result["cells"] == [
        {
            "x_index": 0,
            "y_index": 0,
            "x_label": "A",
            "y_label": "1",
            "value": 2,
            "row_count": 2,
        },
        {
            "x_index": 1,
            "y_index": 0,
            "x_label": "その他（上位外）",
            "y_label": "1",
            "value": 1,
            "row_count": 1,
        },
    ]
    assert result["population"]["axis_other_rows"] == 1


def test_blank_axis_rows_are_excluded_and_counted() -> None:
    result = analyze_matrix(
        population(
            {"x": (), "y": ("1",)},
            {"x": ("A",), "y": ()},
            {"x": ("A",), "y": ("1",)},
        ),
        {
            "x_role": "x",
            "y_role": "y",
            "x_limit": 10,
            "y_limit": 10,
            "include_axis_other": False,
            "measure": "count",
        },
    )

    assert result["population"] == {
        "input_rows": 3,
        "visible_rows": 1,
        "blank_axis_rows": 2,
        "axis_other_rows": 0,
        "excluded_rows": 2,
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("measure", "sum"),
        ("x_limit", 0),
        ("y_limit", 101),
        ("x_role", ""),
    ],
)
def test_matrix_rejects_unsupported_parameters(field: str, value: object) -> None:
    parameters = {
        "x_role": "x",
        "y_role": "y",
        "x_limit": 10,
        "y_limit": 10,
        "include_axis_other": False,
        "measure": "count",
    }
    parameters[field] = value

    with pytest.raises(ValueError):
        analyze_matrix(population({"x": ("A",), "y": ("1",)}), parameters)


def test_matrix_pair_budget_is_incremental(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(matrix_module, "MAX_EXPANDED_CONTRIBUTIONS", 3)

    with pytest.raises(MatrixBudgetError, match="expanded contributions"):
        analyze_matrix(
            population({"x": ("A", "B"), "y": ("1", "2")}),
            {
                "x_role": "x",
                "y_role": "y",
                "x_limit": 10,
                "y_limit": 10,
                "include_axis_other": False,
                "measure": "count",
            },
        )


def test_visible_cell_budget_is_closed() -> None:
    x_values = tuple(f"X{index:02d}" for index in range(21))
    y_values = tuple(f"Y{index:02d}" for index in range(20))

    with pytest.raises(MatrixBudgetError, match="visible cells"):
        analyze_matrix(
            population({"x": x_values, "y": y_values}),
            {
                "x_role": "x",
                "y_role": "y",
                "x_limit": 21,
                "y_limit": 20,
                "include_axis_other": False,
                "measure": "count",
            },
        )


def test_matrix_schemas_are_public_and_closed() -> None:
    for name in (
        "matrix-parameters-v1.schema.json",
        "matrix-result-v1.schema.json",
    ):
        schema = get_public_schema(name)
        Draft202012Validator.check_schema(schema)
        assert schema.get("additionalProperties") is False or "oneOf" in schema


def test_matrix_is_registered_with_renderers_but_without_mcp_exposure() -> None:
    definitions = {item["analysis_id"]: item for item in describe_capabilities()["analyses"]}
    matrix = definitions["matrix.v1"]
    assert matrix["result_variant"] == "matrix"
    assert matrix["render_marks"] == [
        "matrix-bubble-svg.v1",
        "matrix-heatmap-svg.v1",
    ]
    assert matrix["mcp_public"] is True
    assert matrix["limits"]["max_visible_cells"] == 400


def test_matrix_fixture_runs_through_shared_public_api() -> None:
    result = run_analysis_csv(
        FIXTURE / "input.csv",
        (FIXTURE / "spec.json").read_bytes(),
        allowed_root=FIXTURE,
    )
    data = data_from_result(result)
    expected = json.loads((FIXTURE / "expected.json").read_text(encoding="utf-8"))

    assert data["analysis_id"] == expected["analysis_id"]
    assert [item["label"] for item in data["x_axis"]["categories"]] == expected["x_labels"]
    assert [item["label"] for item in data["y_axis"]["categories"]] == expected["y_labels"]
    assert data["population"]["blank_axis_rows"] == expected["blank_axis_rows"]


# --- pie slices inside bubbles -------------------------------------------------------------

PIE_BASE = {
    "x_role": "x",
    "y_role": "y",
    "x_limit": 10,
    "y_limit": 10,
    "include_axis_other": False,
    "measure": "count",
}


def pie_parameters(**overrides: object) -> dict[str, object]:
    return {**PIE_BASE, "pie_role": "z", **overrides}


def test_matrix_without_a_pie_role_keeps_the_result_shape() -> None:
    result = analyze_matrix(population({"x": ("A",), "y": ("1",), "z": ("P",)}), PIE_BASE)

    assert "pie" not in result
    assert all("slices" not in cell for cell in result["cells"])


def test_pie_slices_count_each_pie_value_per_cell_in_legend_order() -> None:
    result = analyze_matrix(
        population(
            {"x": ("A",), "y": ("1",), "z": ("P",)},
            {"x": ("A",), "y": ("1",), "z": ("P", "Q")},
            {"x": ("A",), "y": ("1",), "z": ()},
            {"x": ("B",), "y": ("1",), "z": ("Q",)},
        ),
        pie_parameters(),
    )

    assert result["pie"] == {
        "role": "z",
        "categories": [
            {"label": "P", "count": 2, "is_other": False},
            {"label": "Q", "count": 2, "is_other": False},
            {"label": "(空白)", "count": 1, "is_other": False},
        ],
    }
    by_label = {(cell["x_label"], cell["y_label"]): cell for cell in result["cells"]}
    # A multi-valued pie row is counted once per value, so slices can exceed the row count.
    assert by_label[("A", "1")]["value"] == by_label[("A", "1")]["row_count"] == 3
    assert by_label[("A", "1")]["slices"] == [
        {"label": "P", "count": 2},
        {"label": "Q", "count": 1},
        {"label": "(空白)", "count": 1},
    ]
    assert by_label[("B", "1")]["slices"] == [{"label": "Q", "count": 1}]


def test_pie_limit_folds_the_rest_into_one_other_slice() -> None:
    result = analyze_matrix(
        population(
            {"x": ("A",), "y": ("1",), "z": ("P",)},
            {"x": ("A",), "y": ("1",), "z": ("Q",)},
            {"x": ("A",), "y": ("1",), "z": ("R",)},
            {"x": ("A",), "y": ("1",), "z": ("R", "S")},
        ),
        pie_parameters(pie_limit=2),
    )

    assert [item["label"] for item in result["pie"]["categories"]] == [
        "R",
        "P",
        "その他（上位外）",
    ]
    assert result["pie"]["categories"][-1] == {
        "label": "その他（上位外）",
        "count": 2,
        "is_other": True,
    }
    # Row 4 has two values outside the kept two, yet counts once in the other slice.
    assert result["cells"][0]["slices"] == [
        {"label": "R", "count": 2},
        {"label": "P", "count": 1},
        {"label": "その他（上位外）", "count": 2},
    ]


def test_pie_other_label_never_reuses_a_source_label() -> None:
    result = analyze_matrix(
        population(
            {"x": ("A",), "y": ("1",), "z": ("その他（上位外）",)},
            {"x": ("A",), "y": ("1",), "z": ("P",)},
            {"x": ("A",), "y": ("1",), "z": ("Q",)},
        ),
        pie_parameters(pie_limit=2),
    )

    labels = [item["label"] for item in result["pie"]["categories"]]
    assert len(labels) == len(set(labels))
    assert result["pie"]["categories"][-1]["is_other"] is True


def test_pie_only_counts_rows_that_reach_a_cell() -> None:
    result = analyze_matrix(
        population(
            {"x": ("A",), "y": ("1",), "z": ("P",)},
            {"x": (), "y": ("1",), "z": ("Q",)},
            {"x": ("A",), "y": ("1", "2"), "z": ("P",)},
        ),
        pie_parameters(y_limit=1),
    )

    assert result["pie"]["categories"] == [{"label": "P", "count": 2, "is_other": False}]
    assert result["cells"][0]["slices"] == [{"label": "P", "count": 2}]


@pytest.mark.parametrize(
    "overrides",
    [
        {"pie_limit": 1},
        {"pie_limit": 9},
        {"pie_limit": True},
        {"pie_limit": "5"},
        {"pie_role": ""},
        {"pie_role": 3},
        {"pie_classification_level": "bogus"},
    ],
)
def test_pie_rejects_unsupported_parameters(overrides: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        analyze_matrix(
            population({"x": ("A",), "y": ("1",), "z": ("P",)}),
            pie_parameters(**overrides),
        )


@pytest.mark.parametrize("option", ["pie_limit", "pie_classification_level"])
def test_pie_options_require_a_pie_role(option: str) -> None:
    value = 3 if option == "pie_limit" else "subclass"

    with pytest.raises(ValueError, match="pie_role"):
        analyze_matrix(
            population({"x": ("A",), "y": ("1",)}),
            {**PIE_BASE, option: value},
        )


def test_pie_classification_level_may_not_conflict_with_an_axis_on_the_same_role() -> None:
    with pytest.raises(ValueError, match="two classification levels"):
        analyze_matrix(
            population({"x": ("A",), "y": ("1",)}),
            pie_parameters(
                pie_role="x", x_classification_level="class", pie_classification_level="subclass"
            ),
        )


def test_pie_expansion_has_its_own_closed_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(matrix_module, "MAX_EXPANDED_CONTRIBUTIONS", 3)

    with pytest.raises(MatrixBudgetError, match="pie"):
        analyze_matrix(
            population({"x": ("A",), "y": ("1",), "z": ("P", "Q", "R", "S")}),
            pie_parameters(),
        )


def test_pie_result_and_parameters_validate_against_the_public_schemas() -> None:
    result = analyze_matrix(
        population(
            {"x": ("A",), "y": ("1",), "z": ("P",)},
            {"x": ("A",), "y": ("1",), "z": ("Q",)},
            {"x": ("A",), "y": ("1",), "z": ("R",)},
        ),
        pie_parameters(pie_limit=2),
    )
    assert result["pie"]["categories"][-1]["is_other"] is True
    Draft202012Validator(get_public_schema("matrix-result-v1.schema.json")).validate(result)

    spec = json.loads((FIXTURE / "spec.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(get_public_schema("matrix-parameters-v1.schema.json"))
    validator.validate(
        {**spec, "parameters": {**spec["parameters"], "pie_role": "p", "pie_limit": 4}}
    )
    for bad in (
        {"pie_limit": 4},
        {"pie_role": "p", "pie_limit": 9},
        {"pie_classification_level": "full"},
    ):
        assert not validator.is_valid({**spec, "parameters": {**spec["parameters"], **bad}})


def test_pie_runs_through_the_shared_public_api() -> None:
    spec = json.loads((FIXTURE / "spec.json").read_text(encoding="utf-8"))
    spec["parameters"].update({"pie_role": "yr", "pie_limit": 2})
    spec["resolution"]["bindings"]["yr"] = "year"

    result = run_analysis_csv(
        FIXTURE / "input.csv", json.dumps(spec).encode("utf-8"), allowed_root=FIXTURE
    )
    data = data_from_result(result)

    assert [item["label"] for item in data["pie"]["categories"]] == [
        "2020",
        "2021",
        "その他（上位外）",
    ]
    assert {
        (cell["x_label"], cell["y_label"]): cell["slices"] for cell in data["cells"]
    } == {
        ("A社", "G06F"): [{"label": "2020", "count": 1}],
        ("A社", "H04L"): [
            {"label": "2020", "count": 1},
            {"label": "その他（上位外）", "count": 1},
        ],
        ("B社", "G06F"): [{"label": "2021", "count": 1}],
        ("その他（上位外）", "H04L"): [{"label": "その他（上位外）", "count": 1}],
    }
