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
