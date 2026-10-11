"""Native public-core tests. No Node/Windows guard is bypassed in these cases."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
from advanced_inventory import ADVANCED_MARKS

from patent_analysis import api
from patent_analysis.advanced_presentation import ADVANCED_PRESENTATIONS, get_advanced_presentation
from patent_analysis.advanced_renderer_build import ADVANCED_BUILD
from patent_analysis.canonical_v2 import canonical_json_bytes
from patent_analysis.chart_models.advanced import (
    build_advanced_chart_model,
    build_advanced_render_spec,
)
from patent_analysis.render_errors import RenderError

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "advanced"


def analysis(analysis_id: str):
    if analysis_id.startswith("inventor-") and analysis_id != "inventor-tracking.v1":
        examples = ROOT / "examples" / "inventor-analysis"
        spec = (examples / f"{analysis_id}.json").read_bytes()
        return api.run_analysis("patents.json", spec, allowed_root=examples)
    spec = (EXAMPLES / f"{analysis_id.removesuffix('.v1')}.json").read_bytes()
    return api.run_analysis_csv("patents.csv", spec, allowed_root=EXAMPLES)


@pytest.mark.parametrize("analysis_id", tuple(ADVANCED_PRESENTATIONS))
def test_native_result_builds_fixed_matching_chart_model(analysis_id):
    result = analysis(analysis_id)
    before = deepcopy(result)
    model, receipt = build_advanced_chart_model(result, analysis_id=analysis_id)
    again = build_advanced_chart_model(result, analysis_id=analysis_id)
    assert (model, receipt) == again
    assert result == before
    definition = get_advanced_presentation(analysis_id)
    assert model["mark"] == definition.mark
    assert model["projection"]["kind"] == definition.kind
    assert model["population"] == result["population"]
    assert api.get_public_schema("advanced-chart-model-v1.schema.json")["type"] == "object"
    assert (
        build_advanced_render_spec()["render_profile_id"] == "advanced-svg-ja-jp-node22-echarts6.v1"
    )


@pytest.mark.parametrize("analysis_id", tuple(ADVANCED_PRESENTATIONS))
def test_public_render_rejects_incompatible_mark_and_overlay_before_launch(tmp_path, analysis_id):
    document = canonical_json_bytes(analysis(analysis_id))
    for kwargs in ({"mark": "ranking-svg.v1"}, {"overlay": b'{"labels":[]}'}):
        with pytest.raises(RenderError) as error:
            api.render_analysis_svg(document, output_directory=tmp_path, **kwargs)
        assert error.value.code == "render.invalid"
    assert list(tmp_path.iterdir()) == []


def test_unknown_advanced_mark_cannot_render_legacy_result(tmp_path):
    with pytest.raises(RenderError) as error:
        api.render_analysis_svg(
            b'{"analysis_id":"ranking.v1"}', mark="citation-svg.v1", output_directory=tmp_path
        )
    assert error.value.code == "render.invalid"


def test_unbuilt_distribution_advertises_no_advanced_svg_capability():
    definitions = {d["analysis_id"]: d for d in api.describe_capabilities()["analyses"]}
    built_marks = (
        () if ADVANCED_BUILD is None else ADVANCED_BUILD.get("built_marks", ADVANCED_MARKS)
    )
    for analysis_id, expected in ADVANCED_PRESENTATIONS.items():
        assert definitions[analysis_id]["render_marks"] == (
            [expected.mark] if expected.mark in built_marks else []
        )


@pytest.mark.parametrize("bad", ["\u202e", "\x01", "e\u0301"])
def test_chart_model_rejects_unsafe_or_noncanonical_labels(bad):
    result = analysis("citation.v1")
    result["data"]["points"][0]["label"] = bad
    with pytest.raises(ValueError):
        build_advanced_chart_model(result, analysis_id="citation.v1")


def test_population_inconsistency_is_rejected_before_publication():
    result = analysis("citation.v1")
    result["population"]["input_rows"] += 1
    with pytest.raises(ValueError):
        build_advanced_chart_model(result, analysis_id="citation.v1")
