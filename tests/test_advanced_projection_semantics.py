"""Cross-field presentation validation must reject schema-valid contradictions."""
from __future__ import annotations

import json
from copy import deepcopy
from importlib.resources import files

import pytest
from jsonschema import Draft202012Validator
from test_advanced_compara_projection_regressions import _result as compara_result

from patent_analysis.advanced_projection import project_advanced_data
from patent_analysis.analyses import entry_exit, growth_quadrant


def _assert_valid_shape(data: dict) -> None:
    name = data["analysis_id"].removesuffix(".v1")
    schema = json.loads(files("patent_analysis").joinpath(
        f"schemas/{name}-result-v1.schema.json"
    ).read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(data)


def _growth() -> dict:
    return growth_quadrant.compute(
        [{"year": (str(y),), "owner": ("A",)} for y in (2020, 2022, 2023)],
        {"date_role": "year", "category_role": "owner", "long_start_year": 2020,
         "long_end_year": 2023, "short_start_year": 2022, "short_end_year": 2023},
    )


@pytest.mark.parametrize(("side", "field", "value"), [
    ("long", "rate_percent", -100), ("long", "rate_percent", None),
    ("long", "state", "empty"), ("long", "previous", 0),
    ("short", "rate_percent", 10), ("short", "rate_percent", None),
    ("short", "state", "new"), ("short", "recent", 0),
])
def test_growth_rejects_contradictory_derived_fields(side, field, value):
    data = _growth()
    data["points"][0][side][field] = value
    _assert_valid_shape(data)
    original = deepcopy(data)
    with pytest.raises(ValueError, match="Growth"):
        project_advanced_data(data["analysis_id"], data)
    assert data == original


@pytest.mark.parametrize("quadrant", ["new", "recovery", "slowing", "decline"])
def test_growth_rejects_a_quadrant_that_disagrees_with_rates(quadrant):
    data = _growth()
    data["points"][0]["quadrant"] = quadrant
    _assert_valid_shape(data)
    with pytest.raises(ValueError, match="Growth"):
        project_advanced_data(data["analysis_id"], data)


@pytest.mark.parametrize(("previous", "recent", "rate", "state", "category"), [
    (1, 2, 100, "measured", "sustained_growth"),
    (2, 1, -50, "measured", "decline"),
    (1, 0, -100, "measured", "decline"),
    (1, 1, 0, "measured", "sustained_growth"),
    (0, 0, 0, "empty", "sustained_growth"),
    (0, 1, None, "new", "new"),
])
def test_growth_preserves_valid_zero_and_undefined_rate_semantics(
    previous, recent, rate, state, category,
):
    data = _growth()
    # Equal half-counts on both axes require matching spans for this rate fixture.
    data["short_span"] = deepcopy(data["long_span"])
    point = data["points"][0]
    point.update(total_count=previous + recent, quadrant=category)
    for side in ("long", "short"):
        point[side] = dict(previous=previous, recent=recent, rate_percent=rate, state=state)
    _assert_valid_shape(data)
    original = deepcopy(data)
    projection = project_advanced_data(data["analysis_id"], data)
    if rate is None:
        assert projection["points"] == []
        assert len(projection["unplottable"]) == 1
    else:
        assert projection["points"][0]["x"] == rate
        assert projection["points"][0]["y"] == rate
        assert projection["points"][0]["category"] == category
    assert data == original


def _entry() -> dict:
    return entry_exit.compute(
        [{"year": ("2020",), "owner": ("A",)},
         {"year": ("2025",), "owner": ("B",)}],
        {"date_role": "year", "category_role": "owner"},
    )


@pytest.mark.parametrize(("label", "wrong_flag"), [("A", True), ("B", False)])
def test_entry_exit_rejects_inconsistent_recent_activity(label, wrong_flag):
    data = _entry()
    next(p for p in data["points"] if p["label"] == label)["active_recent"] = wrong_flag
    _assert_valid_shape(data)
    original = deepcopy(data)
    with pytest.raises(ValueError, match="Entry"):
        project_advanced_data(data["analysis_id"], data)
    assert data == original


@pytest.mark.parametrize(("field", "value"), [
    ("active_since_year", None), ("active_since_year", 2022), ("as_of_year", None),
])
def test_entry_exit_rejects_inconsistent_cutoff_metadata(field, value):
    data = _entry()
    data[field] = value
    _assert_valid_shape(data)
    with pytest.raises(ValueError, match="Entry"):
        project_advanced_data(data["analysis_id"], data)


def test_entry_exit_keeps_inclusive_cutoff_and_does_not_mutate():
    data = entry_exit.compute(
        [{"year": (str(y),), "owner": (str(y),)} for y in (2022, 2023, 2025)],
        {"date_role": "year", "category_role": "owner"},
    )
    original = deepcopy(data)
    p = project_advanced_data(data["analysis_id"], data)
    assert {v["label"]: v["category"] for v in p["points"]} == {
        "2022": "inactive", "2023": "active", "2025": "active",
    }
    assert data == original


def test_entry_exit_empty_population_retains_null_cutoff():
    data = entry_exit.compute([], {"date_role": "year", "category_role": "owner"})
    _assert_valid_shape(data)
    assert project_advanced_data(data["analysis_id"], data)["points"] == []


@pytest.mark.parametrize("remove_all", [False, True])
def test_compara_missing_cells_are_not_treated_as_zero_differences(remove_all):
    data = compara_result(5, 1, 4)
    if remove_all:
        data["cells"] = []
    else:
        data["x"].append("Z")
    _assert_valid_shape(data)
    original = deepcopy(data)
    with pytest.raises(ValueError, match="Compara"):
        project_advanced_data(data["analysis_id"], data)
    assert data == original
