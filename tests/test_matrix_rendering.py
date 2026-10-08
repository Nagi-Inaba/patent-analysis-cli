from __future__ import annotations

import json
from pathlib import Path

import pytest
from advanced_inventory import ADVANCED_MARKS

from patent_analysis._render_canonical import canonical_json_bytes
from tests.test_matrix_chart_model import MATRIX_RESULT


def test_renderer_registry_exposes_all_completed_closed_marks() -> None:
    from patent_analysis.renderer_registry import (
        get_renderer_definition,
        list_renderer_definitions,
    )

    definitions = list_renderer_definitions()
    assert tuple(definition.mark for definition in definitions) == (
        "ranking-svg.v1",
        "matrix-bubble-svg.v1",
        "matrix-heatmap-svg.v1",
        "series-line-svg.v1",
        "series-stacked-bar-svg.v1",
        "composition-bar-svg.v1",
        "composition-pie-svg.v1",
        "points-bubble-svg.v1",
        *ADVANCED_MARKS,
    )
    assert get_renderer_definition("matrix-bubble-svg.v1").result_variant == "matrix"
    assert get_renderer_definition("matrix-heatmap-svg.v1").result_variant == "matrix"
    assert get_renderer_definition("ranking-svg.v1").result_variant == "ranking"
    assert get_renderer_definition("series-line-svg.v1").result_variant == "series"
    assert get_renderer_definition("series-stacked-bar-svg.v1").result_variant == "series"
    assert get_renderer_definition("composition-bar-svg.v1").result_variant == "composition"
    assert get_renderer_definition("composition-pie-svg.v1").result_variant == "composition"
    with pytest.raises(ValueError):
        get_renderer_definition("caller-echarts-option")


def test_matrix_renderer_resources_are_separate_from_ranking_resources() -> None:
    from patent_analysis.renderer_resources import (
        load_verified_matrix_renderer_resources,
        load_verified_renderer_resources,
    )

    ranking = load_verified_renderer_resources()
    matrix = load_verified_matrix_renderer_resources()

    assert matrix.runtime.render_profile_id == "matrix-svg-ja-jp-node22-echarts6.v1"
    assert matrix.runtime.renderer_build_digest != ranking.runtime.renderer_build_digest
    assert matrix.bootstrap_bytes != ranking.bootstrap_bytes
    assert matrix.bundle_bytes != ranking.bundle_bytes


def test_renderer_response_schemas_are_closed_per_profile() -> None:
    from patent_analysis.renderer_resources import _load_verified_renderer_schema_bytes

    ranking_schema = json.loads(
        _load_verified_renderer_schema_bytes("renderer-response.schema.json")
    )
    matrix_schema = json.loads(
        _load_verified_renderer_schema_bytes("matrix-renderer-response.schema.json")
    )
    ranking_profile = ranking_schema["$defs"]["runtime"]["properties"]["render_profile_id"]
    matrix_profile = matrix_schema["$defs"]["runtime"]["properties"]["render_profile_id"]

    assert ranking_profile == {"const": "ranking-svg-ja-jp-node22-echarts6.v1"}
    assert matrix_profile == {"const": "matrix-svg-ja-jp-node22-echarts6.v1"}


def test_render_analysis_svg_rejects_matrix_overlay_and_unknown_mark(
    tmp_path: Path,
) -> None:
    from patent_analysis.api import render_analysis_svg

    document = canonical_json_bytes(MATRIX_RESULT)
    with pytest.raises(ValueError):
        render_analysis_svg(
            document,
            mark="matrix-bubble-svg.v1",
            overlay={"rows": []},
            output_directory=tmp_path,
        )
    with pytest.raises(ValueError):
        render_analysis_svg(
            document,
            mark="caller-echarts-option",
            output_directory=tmp_path,
        )


def test_public_render_facade_preserves_bounded_input_error(tmp_path: Path) -> None:
    from patent_analysis.api import render_analysis_svg
    from patent_analysis.render_errors import RenderError
    from patent_analysis.rendering import MAX_ANALYSIS_DOCUMENT_BYTES

    with pytest.raises(RenderError) as caught:
        render_analysis_svg(
            b" " * (MAX_ANALYSIS_DOCUMENT_BYTES + 1),
            output_directory=tmp_path,
        )

    assert caught.value.code == "input.invalid"
