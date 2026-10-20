"""Closed neutral chart-model builders for lifecycle points results."""

from __future__ import annotations

from copy import deepcopy

from patent_analysis._render_canonical import canonical_json_bytes, sha256_bytes
from patent_analysis.chart_models._common import (
    build_receipt,
    coerce_analysis_result,
    fixed_render_spec,
    validate_schema,
)

POINTS_BUBBLE_MARK = "points-bubble-svg.v1"
POINTS_RENDER_MARKS = (POINTS_BUBBLE_MARK,)
POINTS_RENDER_PROFILE_ID = "points-svg-ja-jp-node22-echarts6.v1"


def build_points_chart_model(
    analysis_result: object,
    *,
    mark: str,
) -> tuple[dict[str, object], dict[str, object]]:
    if mark != POINTS_BUBBLE_MARK:
        raise ValueError("unknown points renderer mark")
    result = coerce_analysis_result(
        analysis_result,
        analysis_id="lifecycle.v1",
        result_variant="points",
        result_schema="lifecycle-result-v1.schema.json",
    )
    data = result["data"]
    assert isinstance(data, dict)
    labels = [point["label"] for point in data["points"]]
    if len(set(labels)) != len(labels):
        raise ValueError("points labels must be unique")
    model: dict[str, object] = {
        "chart_model_contract_version": "1.0.0",
        "chart_type": "points.bubble",
        "mark": POINTS_BUBBLE_MARK,
        "analysis_result_sha256": sha256_bytes(canonical_json_bytes(result)),
        "title": "技術ライフサイクル",
        "x_axis": {"label": "ピーク年", "value_kind": "year"},
        "y_axis": {"label": "CAGR（%）", "value_kind": "number"},
        "size_axis": {"label": "総件数", "value_kind": "count"},
        "points": deepcopy(data["points"]),
        "population": deepcopy(result["population"]),
        "warnings": list(result["warnings"]),
    }
    validate_schema(model, "points-chart-model-v1.schema.json")
    receipt = build_receipt(result, data, model, mark=mark)
    return deepcopy(model), deepcopy(receipt)


def build_points_render_spec(
    *, mark: str, point_count: int, palette: str | None = None
) -> dict[str, object]:
    if mark != POINTS_BUBBLE_MARK:
        raise ValueError("unknown points renderer mark")
    if type(point_count) is not int or not 0 <= point_count <= 20:
        raise ValueError("points render dimensions are invalid")
    spec = fixed_render_spec(
        renderer_kind="points.bubble.svg",
        render_profile_id=POINTS_RENDER_PROFILE_ID,
        palette=palette,
    )
    validate_schema(spec, "points-render-spec-v1.schema.json")
    return deepcopy(spec)


__all__ = (
    "POINTS_BUBBLE_MARK",
    "POINTS_RENDER_MARKS",
    "POINTS_RENDER_PROFILE_ID",
    "build_points_chart_model",
    "build_points_render_spec",
)
