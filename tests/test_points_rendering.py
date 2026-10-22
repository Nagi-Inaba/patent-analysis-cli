from __future__ import annotations

import json
from pathlib import Path

import pytest

LIFECYCLE_RESULT = {
    "analysis_id": "lifecycle.v1",
    "algorithm_version": "1.0.0",
    "result_variant": "points",
    "population": {"input_rows": 1, "analyzed_rows": 1, "excluded_rows": 0},
    "data": {
        "schema_version": "1.0.0",
        "analysis_id": "lifecycle.v1",
        "algorithm_version": "1.0.0",
        "window": {"start_year": 2020, "end_year": 2024, "years": 5},
        "points": [
            {"label": "X分類", "x": 2022, "y": 18.9, "size": 1, "stage": "growth"}
        ],
        "population": {
            "input_rows": 1,
            "visible_rows": 1,
            "invalid_year_rows": 0,
            "blank_category_rows": 0,
            "excluded_rows": 0,
        },
        "contributions": 1,
        "limits": {
            "max_top_n": 20,
            "max_output_points": 20,
            "max_distinct_buckets": 100000,
            "max_expanded_contributions": 1000000,
        },
    },
    "warnings": [],
}


def _document() -> bytes:
    return json.dumps(
        LIFECYCLE_RESULT,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode()


def test_points_renderer_registry_uses_separate_closed_resource_family() -> None:
    from patent_analysis.renderer_registry import get_renderer_definition

    definition = get_renderer_definition("points-bubble-svg.v1")
    assert definition.result_variant == "points"
    assert definition.resource_family == "points"
    assert definition.render_profile_id == "points-svg-ja-jp-node22-echarts6.v1"


def test_points_resources_are_independently_pinned() -> None:
    from patent_analysis.renderer_resources import load_verified_points_renderer_resources

    resources = load_verified_points_renderer_resources()
    assert resources.runtime.render_profile_id == "points-svg-ja-jp-node22-echarts6.v1"
    assert resources.runtime.node_version == "22.23.4"
    assert resources.runtime.echarts_version == "6.1.0"
    assert resources.bundle_bytes
    assert resources.bootstrap_bytes


def test_points_renderer_rejects_unknown_mark_before_platform_access(tmp_path: Path) -> None:
    from patent_analysis.rendering import render_points_svg

    with pytest.raises(ValueError, match="unknown points renderer mark"):
        render_points_svg(
            _document(),
            mark="entry-exit-bubble-svg.v1",
            output_directory=tmp_path,
        )
