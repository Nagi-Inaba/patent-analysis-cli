from __future__ import annotations

import json
from importlib.resources import files

import pytest

from patent_analysis.analysis_contracts import StrictDraft202012Validator

LIFECYCLE_RESULT = {
    "analysis_id": "lifecycle.v1",
    "algorithm_version": "1.0.0",
    "result_variant": "points",
    "population": {"input_rows": 6, "analyzed_rows": 6, "excluded_rows": 0},
    "data": {
        "schema_version": "1.0.0",
        "analysis_id": "lifecycle.v1",
        "algorithm_version": "1.0.0",
        "window": {"start_year": 2020, "end_year": 2024, "years": 5},
        "points": [
            {
                "label": "X分類",
                "x": 2022,
                "y": 18.920711500272102,
                "size": 6,
                "stage": "growth",
            }
        ],
        "population": {
            "input_rows": 6,
            "visible_rows": 6,
            "invalid_year_rows": 0,
            "blank_category_rows": 0,
            "excluded_rows": 0,
        },
        "contributions": 6,
        "limits": {
            "max_top_n": 20,
            "max_output_points": 20,
            "max_distinct_buckets": 100000,
            "max_expanded_contributions": 1000000,
        },
    },
    "warnings": [],
}


def _schema(name: str) -> dict[str, object]:
    value = json.loads(
        files("patent_analysis").joinpath("schemas", name).read_text(encoding="utf-8")
    )
    assert isinstance(value, dict)
    StrictDraft202012Validator.check_schema(value)
    return value


def test_points_chart_model_is_closed_to_lifecycle_bubble() -> None:
    from patent_analysis.chart_models.points import (
        build_points_chart_model,
        build_points_render_spec,
    )

    model, receipt = build_points_chart_model(
        LIFECYCLE_RESULT,
        mark="points-bubble-svg.v1",
    )
    assert model["chart_type"] == "points.bubble"
    assert model["mark"] == "points-bubble-svg.v1"
    assert model["title"] == "技術ライフサイクル"
    assert model["points"] == LIFECYCLE_RESULT["data"]["points"]
    assert model["x_axis"] == {"label": "ピーク年", "value_kind": "year"}
    assert model["y_axis"] == {"label": "CAGR（%）", "value_kind": "number"}
    assert model["size_axis"] == {"label": "総件数", "value_kind": "count"}
    assert receipt["mark"] == "points-bubble-svg.v1"
    assert "option" not in model

    spec = build_points_render_spec(mark="points-bubble-svg.v1", point_count=1)
    assert spec["renderer_kind"] == "points.bubble.svg"
    assert spec["render_profile_id"] == "points-svg-ja-jp-node22-echarts6.v1"


def test_points_chart_model_and_render_spec_schemas_are_valid_and_exact() -> None:
    from patent_analysis.chart_models.points import (
        build_points_chart_model,
        build_points_render_spec,
    )

    model, _ = build_points_chart_model(
        LIFECYCLE_RESULT,
        mark="points-bubble-svg.v1",
    )
    spec = build_points_render_spec(mark="points-bubble-svg.v1", point_count=1)
    assert next(
        StrictDraft202012Validator(_schema("points-chart-model-v1.schema.json")).iter_errors(
            model
        ),
        None,
    ) is None
    assert next(
        StrictDraft202012Validator(_schema("points-render-spec-v1.schema.json")).iter_errors(
            spec
        ),
        None,
    ) is None

    invalid = dict(model)
    invalid["mark"] = "matrix-bubble-svg.v1"
    assert next(
        StrictDraft202012Validator(_schema("points-chart-model-v1.schema.json")).iter_errors(
            invalid
        ),
        None,
    ) is not None


def test_points_chart_model_rejects_other_analyses_and_marks() -> None:
    from patent_analysis.chart_models.points import build_points_chart_model

    with pytest.raises(ValueError):
        build_points_chart_model(LIFECYCLE_RESULT, mark="matrix-bubble-svg.v1")
    wrong = dict(LIFECYCLE_RESULT)
    wrong["analysis_id"] = "entry-exit.v1"
    with pytest.raises(ValueError):
        build_points_chart_model(wrong, mark="points-bubble-svg.v1")
