"""Nested analysis populations must agree without discarding valid filtering."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from advanced_inventory import ADVANCED_IDS

from patent_analysis import api
from patent_analysis.chart_models._common import coerce_analysis_result
from patent_analysis.chart_models.advanced import build_advanced_chart_model

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "advanced"


def _result(analysis_id: str) -> dict:
    spec = (EXAMPLES / f"{analysis_id[:-3]}.json").read_bytes()
    return api.run_analysis_csv("patents.csv", spec, allowed_root=EXAMPLES)


@pytest.mark.parametrize("analysis_id", ADVANCED_IDS)
@pytest.mark.parametrize("mutation", ["zero_outer", "wrong_visible", "oversize_inner", "sum"])
def test_schema_valid_population_contradictions_are_rejected(analysis_id, mutation):
    result = _result(analysis_id)
    inner, outer = result["data"]["population"], result["population"]
    assert inner["visible_rows"] > 0
    if mutation == "zero_outer":
        outer.update(input_rows=0, analyzed_rows=0, excluded_rows=0)
    elif mutation == "wrong_visible":
        inner.update(visible_rows=0, excluded_rows=inner["input_rows"])
    elif mutation == "oversize_inner":
        inner["input_rows"] = outer["input_rows"] + 1
        inner["excluded_rows"] = inner["input_rows"] - inner["visible_rows"]
    else:
        inner["excluded_rows"] += 1
    # All mutations satisfy both existing structural schemas. The missing
    # relationship checks, rather than a malformed fixture, must reject them.
    coerce_analysis_result(
        result, analysis_id=analysis_id, result_variant=result["result_variant"],
        result_schema=f"{analysis_id[:-3]}-result-v1.schema.json",
    )
    before = deepcopy(result)
    with pytest.raises(ValueError, match="population"):
        build_advanced_chart_model(result, analysis_id=analysis_id)
    assert result == before


@pytest.mark.parametrize("analysis_id", ADVANCED_IDS)
def test_empty_native_populations_remain_valid(analysis_id, tmp_path):
    header = (EXAMPLES / "patents.csv").read_bytes().splitlines(keepends=True)[0]
    (tmp_path / "empty.csv").write_bytes(header)
    spec = (EXAMPLES / f"{analysis_id[:-3]}.json").read_bytes()
    result = api.run_analysis_csv("empty.csv", spec, allowed_root=tmp_path)
    before = deepcopy(result)
    model, receipt = build_advanced_chart_model(result, analysis_id=analysis_id)
    assert model["population"] == {"input_rows": 0, "analyzed_rows": 0, "excluded_rows": 0}
    assert receipt["analysis_result_sha256"] == model["analysis_result_sha256"]
    assert result == before and (tmp_path / "empty.csv").read_bytes() == header


@pytest.mark.parametrize("year, included, visible", [(2020, 1, 1), (2024, 5, 4), (2010, 0, 0)])
def test_filtered_rows_are_not_required_to_equal_the_source_population(year, included, visible):
    spec = json.loads((EXAMPLES / "entry-exit.json").read_bytes())
    spec["population"]["filters"] = [
        {"role": "year", "match": "year_range", "start_year": year, "end_year": year,
         "effect": "include"},
    ]
    result = api.run_analysis_csv("patents.csv", json.dumps(spec).encode(), allowed_root=EXAMPLES)
    before = deepcopy(result)
    assert result["data"]["population"] == {
        "input_rows": included, "visible_rows": visible, "excluded_rows": included - visible,
    }
    model, _ = build_advanced_chart_model(result, analysis_id="entry-exit.v1")
    assert model["population"] == {
        "input_rows": 10, "analyzed_rows": visible, "excluded_rows": 10 - visible,
    }
    assert result == before
