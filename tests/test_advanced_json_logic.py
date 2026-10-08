"""Arithmetic and boundary tests; inputs are already-normalized role tokens."""

from __future__ import annotations

import importlib
import json
import random
from copy import deepcopy

import pytest

MODULES = (
    "growth_quadrant",
    "entry_exit",
    "citation",
    "matrix_composition",
    "new_entrants",
    "compara",
    "cooccurrence",
    "network",
    "uniqueness",
    "shared_involvement",
)


def row(**values):
    return {
        key: (value,) if isinstance(value, str) else tuple(value) for key, value in values.items()
    }


def compute(name, rows, **parameters):
    return importlib.import_module("patent_analysis.analyses." + name).compute(rows, parameters)


def params(name):
    return {
        "growth_quadrant": dict(
            date_role="year",
            category_role="group",
            long_start_year=2020,
            long_end_year=2023,
            short_start_year=2022,
            short_end_year=2023,
        ),
        "entry_exit": dict(date_role="year", category_role="group"),
        "citation": dict(date_role="year", label_role="group", citation_role="cites"),
        "matrix_composition": dict(
            x_role="x", y_role="y", category_role="item", x_value="X", y_value="Y"
        ),
        "new_entrants": dict(
            date_role="year", applicant_role="group", classification_role="item", as_of_year=2022
        ),
        "compara": dict(x_role="x", y_role="y", group_role="group", group_a="A", group_b="B"),
        "cooccurrence": dict(category_role="item"),
        "network": dict(category_role="group"),
        "uniqueness": dict(group_role="group", item_role="item"),
        "shared_involvement": dict(group_role="group", item_role="item"),
    }[name]


def test_quadrant_splits_spans_and_counts_overlap_once():
    rows = [
        row(year="2020", group="A"),
        row(year="2021", group="A"),
        row(year="2022", group="A"),
    ] + [row(year="2023", group="A")] * 3
    out = compute("growth_quadrant", rows, **params("growth_quadrant"))
    p = out["points"][0]
    assert p["total_count"] == 6
    assert p["long"] == dict(previous=2, recent=4, rate_percent=100.0, state="measured")
    assert p["short"] == dict(previous=1, recent=3, rate_percent=200.0, state="measured")
    assert p["quadrant"] == "sustained_growth"
    assert out["contributions"] == 6


def test_quadrant_zero_base_is_null_not_invented_coordinate():
    out = compute("growth_quadrant", [row(year="2023", group="A")], **params("growth_quadrant"))
    assert out["points"][0]["long"]["rate_percent"] is None
    assert out["points"][0]["quadrant"] == "new"


def test_entry_exit_uses_earliest_latest_and_full_population_cutoff():
    rows = [
        row(year="2018", group=("A", "A")),
        row(year="2020", group="A"),
        row(year="2024", group="B"),
        row(year="2022", group="C"),
        row(year="bad", group="D"),
    ]
    out = compute("entry_exit", rows, top_n=1, **params("entry_exit"))
    assert out["as_of_year"] == 2024
    assert out["active_since_year"] == 2022
    assert out["points"] == [
        dict(label="A", first_year=2018, last_year=2020, count=2, active_recent=False)
    ]
    assert out["population"]["excluded_rows"] == 1


def test_citation_is_record_level_and_preserves_duplicate_labels():
    rows = [
        row(year="2020", group="A", cites="被引用件数: 12"),
        row(year="2019", group="A", cites="1,000"),
        row(year="2022", group="B", cites="0"),
        row(year="2022", group="B", cites="-1"),
        row(year="2022", group="B", cites="NaN"),
    ]
    out = compute("citation", rows, **params("citation"))
    assert [(p["label"], p["year"], p["citation_value"]) for p in out["points"]] == [
        ("A", 2019, 1000),
        ("A", 2020, 12),
        ("B", 2022, 0),
    ]
    assert [p["point_id"] for p in out["points"]] == [1, 2, 3]
    assert out["population"]["excluded_rows"] == 2


def test_matrix_composition_denominator_is_not_top_n_total():
    rows = [
        row(x="X", y="Y", item=("P", "Q")),
        row(x="X", y="Y", item="P"),
        row(x="Z", y="Y", item="Q"),
    ]
    out = compute("matrix_composition", rows, top_n=1, **params("matrix_composition"))
    assert out["items"] == [dict(label="P", count=2, share=pytest.approx(2 / 3))]
    assert out["cell_rows"] == 2
    assert out["category_memberships"] == 3


def test_new_entrants_checks_all_history_and_shares_before_axis_truncation():
    rows = [
        row(year="2010", group="Old", item="P"),
        row(year="2024", group="Old", item="P"),
        row(year="2022", group="New", item=("P", "Q")),
        row(year="2023", group="New", item="P"),
    ]
    out = compute("new_entrants", rows, top_classifications=1, **params("new_entrants"))
    assert [a["label"] for a in out["applicants"]] == ["New"]
    assert out["cells"] == [
        dict(applicant="New", classification="P", count=2, share=pytest.approx(2 / 3))
    ]


def test_compara_sign_and_overlapping_group_membership():
    rows = [
        row(x="X", y="Y", group="A"),
        row(x="X", y="Y", group=("A", "B")),
        row(x="Z", y="Y", group="B"),
        row(x="OUT", y="Y", group="C"),
    ]
    out = compute("compara", rows, **params("compara"))
    by_x = {c["x"]: c for c in out["cells"]}
    assert by_x["X"] == dict(x="X", y="Y", a_count=2, b_count=1, difference=1)
    assert by_x["Z"]["difference"] == -1
    assert "OUT" not in out["x"]


def test_cooccurrence_dedupes_labels_is_symmetric_and_has_zero_diagonal():
    out = compute(
        "cooccurrence",
        [row(item=("A", "A", "B", "C")), row(item=("A", "B"))],
        **params("cooccurrence"),
    )
    counts = {(c["x"], c["y"]): c["count"] for c in out["cells"]}
    assert counts["A", "B"] == counts["B", "A"] == 2
    assert counts["A", "C"] == 1
    assert all(counts[x, x] == 0 for x in out["labels"])
    assert out["contributions"] == 4


def test_network_excludes_singleton_rows_from_node_weights():
    rows = [row(group=("A", "B")), row(group=("A", "B", "C"))] + [row(group="C")] * 9
    out = compute("network", rows, **params("network"))
    assert {n["label"]: n["count"] for n in out["nodes"]} == {"A": 2, "B": 2, "C": 1}
    assert out["edges"][0] == dict(source="A", target="B", count=2)
    assert out["population"]["visible_rows"] == 2


def test_uniqueness_uses_distinct_global_owners_before_top_n():
    rows = [row(group="A", item=("P", "Q")), row(group="A", item="P"), row(group="B", item="Q")]
    out = compute("uniqueness", rows, top_n=1, **params("uniqueness"))
    p = out["groups"][0]
    assert p["group"] == "A"
    assert (p["record_count"], p["total_item_count"], p["unique_item_count"]) == (2, 2, 1)
    assert p["unique_items"] == ["P"]
    assert p["uniqueness_rate"] == 0.5


def test_shared_involvement_counts_each_row_once_not_each_shared_item():
    rows = [
        row(group="A", item=("P", "Q")),
        row(group="B", item=("P", "Q")),
        row(group="A", item="R"),
    ]
    out = compute("shared_involvement", rows, **params("shared_involvement"))
    by_group = {g["group"]: g for g in out["groups"]}
    a = by_group["A"]
    assert (a["record_count"], a["involvement_record_count"], a["shared_item_count"]) == (2, 1, 2)
    assert a["shared_rate"] == pytest.approx(2 / 3)
    out3 = compute("shared_involvement", rows, min_groups=3, **params("shared_involvement"))
    assert all(g["involvement_record_count"] == 0 for g in out3["groups"])


@pytest.mark.parametrize("name", MODULES)
def test_empty_input_is_a_closed_valid_json_result(name):
    out = compute(name, [], **params(name))
    assert out["population"] == dict(input_rows=0, visible_rows=0, excluded_rows=0)
    assert out["contributions"] == 0
    json.dumps(out, allow_nan=False)


@pytest.mark.parametrize("name", MODULES)
def test_unknown_parameter_and_bool_top_n_are_rejected(name):
    with pytest.raises(ValueError):
        compute(name, [], **params(name), arbitrary_expression="exec()")
    with pytest.raises(ValueError):
        compute(name, [], **params(name), top_n=True)


@pytest.mark.parametrize("name", MODULES)
def test_deterministic_under_record_permutation_without_mutation(name):
    rows = [
        row(year="2023", group=("A", "B"), item=("P", "Q"), cites="2", x="X", y="Y"),
        row(year="2020", group="A", item="Q", cites="3", x="Z", y="Y"),
    ]
    before = deepcopy(rows)
    first = compute(name, rows, **params(name))
    second = compute(name, list(reversed(rows)), **params(name))
    assert first == second
    assert rows == before


def test_pair_budget_is_checked_for_actual_expansion(monkeypatch):
    from patent_analysis.analyses import _advanced_common as common

    monkeypatch.setattr(common, "MAX_CONTRIBUTIONS", 3)
    out = compute("cooccurrence", [row(item=("A", "B", "C"))], **params("cooccurrence"))
    assert out["contributions"] == 3
    with pytest.raises(common.AnalysisCapacityError):
        compute(
            "cooccurrence",
            [row(item=("A", "B", "C")), row(item=("A", "B"))],
            **params("cooccurrence"),
        )


def test_quadrant_invalid_spans_and_role_collision():
    p = params("growth_quadrant")
    for update in ({"long_end_year": 2020}, {"short_start_year": True}, {"category_role": "year"}):
        with pytest.raises(ValueError):
            compute("growth_quadrant", [], **{**p, **update})


def test_citation_ambiguous_multivalue_numbers_are_not_summed():
    out = compute("citation", [row(year="2020", group="A", cites=("2", "3"))], **params("citation"))
    assert out["points"] == []
    assert out["population"]["excluded_rows"] == 1


def test_set_ownership_randomized_against_independent_set_oracle():
    rng = random.Random(417)
    for _ in range(30):
        rows = [
            row(
                group=tuple(g for g in "ABC" if rng.randrange(2)),
                item=tuple(i for i in "PQR" if rng.randrange(2)),
            )
            for _ in range(12)
        ]
        owners = {i: {g for r in rows if i in r["item"] for g in r["group"]} for i in "PQR"}
        for name, key, rate in [
            ("uniqueness", "unique_item_count", "uniqueness_rate"),
            ("shared_involvement", "shared_item_count", "shared_rate"),
        ]:
            out = compute(name, rows, **params(name))
            for group in out["groups"]:
                items = {i for r in rows if group["group"] in r["group"] for i in r["item"]}
                expected = sum(
                    len(owners[i]) == 1 if name == "uniqueness" else len(owners[i]) >= 2
                    for i in items
                )
                assert group[key] == expected
                assert group[rate] == expected / len(items)


@pytest.mark.parametrize("name", MODULES)
def test_each_schema_accepts_result_and_rejects_unknown_fields(name):
    from pathlib import Path

    from jsonschema import Draft202012Validator

    mod = importlib.import_module("patent_analysis.analyses." + name)
    root = Path(__file__).resolve().parents[1] / "src/patent_analysis/schemas"
    slug = mod.ANALYSIS_ID.removesuffix(".v1")
    schema = json.loads(
        (root / (slug + "-result-v1.schema.json")).read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(schema)
    for rows in (
        [],
        [row(year="2023", group=("A", "B"), item=("P", "Q"), cites="2", x="X", y="Y")],
    ):
        result = mod.compute(rows, params(name))
        validator.validate(result)
        assert list(validator.iter_errors({**result, "unreviewed_field": 1}))
    spec_schema = json.loads(
        (root / (slug + "-parameters-v1.schema.json")).read_text(encoding="utf-8")
    )
    spec = dict(
        analysis_contract_version="2.0.0",
        analysis_id=mod.ANALYSIS_ID,
        resolution={"bindings": {}},
        normalization={"profiles": []},
        population={"filters": [], "selection_sets": [], "family_mode": "records"},
        parameters=params(name),
    )
    Draft202012Validator(spec_schema).validate(spec)
    spec["parameters"] = {**spec["parameters"], "arbitrary_expression": "x+1"}
    assert list(Draft202012Validator(spec_schema).iter_errors(spec))


def test_literal_pair_budget_boundary_and_plus_one():
    rows = [row(item=tuple(str(i) for i in range(100)))] * 202 + [row(item=("0", "1"))] * 100
    out = compute("cooccurrence", rows, **params("cooccurrence"))
    assert out["contributions"] == 1_000_000
    with pytest.raises(ValueError):
        compute("cooccurrence", rows + [row(item=("0", "1"))], **params("cooccurrence"))


def test_serialized_label_exact_boundary_and_one_over():
    accepted = "a" * 4094  # JSON quotes are included in the 4096-byte label budget.
    compute("entry_exit", [row(year="2024", group=accepted)], **params("entry_exit"))
    with pytest.raises(ValueError):
        compute("entry_exit", [row(year="2024", group=accepted + "a")], **params("entry_exit"))


def test_top_n_does_not_hide_oversized_offscreen_label():
    rows = [row(year="2024", group="A")] * 2 + [row(year="2024", group="z" * 4095)]
    with pytest.raises(ValueError):
        compute("entry_exit", rows, top_n=1, **params("entry_exit"))


def test_preflight_estimators_and_normalized_input_budget(monkeypatch):
    from patent_analysis.analyses import _advanced_common as c

    assert c.preflight_pair_size(100) == 4950
    assert c.preflight_cartesian_size(100, 100, 2) == 20000
    with pytest.raises(ValueError):
        c.preflight_pair_size(True)
    monkeypatch.setattr(c, "MAX_INPUT_TOKENS", 3)
    assert len(c.checked_records([row(a=("A", "B"), b="C")], ("a", "b"))) == 1
    with pytest.raises(ValueError):
        c.checked_records([row(a=("A", "B"), b=("C", "D"))], ("a", "b"))


def test_semantic_registration_reuses_calculation_parameter_validation():
    from patent_analysis.analyses._advanced_registration import validate_parameters

    validate_parameters("entry-exit.v1", params("entry_exit"))
    # Existing analyses are deliberately outside this supplementary validator.
    validate_parameters("growth.v1", None)
    with pytest.raises(ValueError):
        validate_parameters("compara.v1", {**params("compara"), "group_b": "A"})


def test_shared_and_unique_item_samples_do_not_change_complete_counts():
    items = tuple(f"item-{i:02d}" for i in range(25))
    one = compute("uniqueness", [row(group="A", item=items)], **params("uniqueness"))["groups"][0]
    assert one["unique_item_count"] == 25
    assert len(one["unique_items"]) == 20 and one["items_truncated"] is True
    assert one["uniqueness_rate"] == 1.0
    shared = compute(
        "shared_involvement", [row(group=("A", "B"), item=items)], **params("shared_involvement")
    )
    assert all(
        g["shared_item_count"] == 25
        and g["involvement_record_count"] == 1
        and len(g["shared_items"]) == 20
        and g["items_truncated"]
        for g in shared["groups"]
    )
