"""Closed chart-model construction for the approved advanced analyses."""

from __future__ import annotations

import unicodedata
from copy import deepcopy
from typing import Any

from patent_analysis._render_canonical import canonical_json_bytes, sha256_bytes
from patent_analysis._render_text import grapheme_count, validate_safe_text
from patent_analysis.advanced_presentation import (
    ADVANCED_RENDER_PROFILE_ID,
    MAX_ADVANCED_MODEL_BYTES,
    get_advanced_presentation,
)
from patent_analysis.advanced_projection import project_advanced_data
from patent_analysis.chart_models._common import (
    build_receipt,
    coerce_analysis_result,
    fixed_render_spec,
    validate_schema,
)


def _validate_text_and_population(model: dict[str, Any]) -> None:
    stack: list[object] = [model]
    count = 0
    while stack:
        value = stack.pop()
        if isinstance(value, str):
            validate_safe_text(value)
            if unicodedata.normalize("NFC", value) != value:
                raise ValueError("render text must be NFC")
            count += grapheme_count(value)
            if count > 20_000:
                raise ValueError("render text exceeds grapheme budget")
        elif isinstance(value, dict):
            stack.extend(value.values())
        elif isinstance(value, list):
            stack.extend(value)
    p = model["population"]
    if p["input_rows"] != p["analyzed_rows"] + p["excluded_rows"]:
        raise ValueError("presentation population counters are inconsistent")


def build_advanced_chart_model(
    analysis_result: object, *, analysis_id: str, mark: str | None = None
) -> tuple[dict[str, Any], dict[str, object]]:
    definition = get_advanced_presentation(analysis_id, mark)
    result = coerce_analysis_result(
        analysis_result,
        analysis_id=analysis_id,
        result_variant=definition.result_variant,
        result_schema=f"{analysis_id.removesuffix('.v1')}-result-v1.schema.json",
    )
    if result.get("algorithm_version") != "1.0.0":
        raise ValueError("unsupported analytical algorithm version")
    data = result["data"]
    inner, outer = data["population"], result["population"]
    # The inner population is after selection filters; it may be smaller than
    # the original CSV. Both layers must describe the same analyzed rows.
    if (
        inner["visible_rows"] != outer["analyzed_rows"]
        or inner["input_rows"] > outer["input_rows"]
        or inner["input_rows"] != inner["visible_rows"] + inner["excluded_rows"]
    ):
        raise ValueError("inner and outer presentation population counters are inconsistent")
    projection = project_advanced_data(analysis_id, data)
    model = {
        "chart_model_contract_version": "1.0.0",
        "chart_type": "advanced.svg",
        "analysis_id": analysis_id,
        "mark": definition.mark,
        "title": definition.title,
        "analysis_result_sha256": sha256_bytes(canonical_json_bytes(result)),
        "projection": projection,
        "population": deepcopy(result["population"]),
        "warnings": list(result["warnings"]),
    }
    validate_schema(projection, "advanced-projection-v1.schema.json")
    validate_schema(model, "advanced-chart-model-v1.schema.json")
    _validate_text_and_population(model)
    if len(canonical_json_bytes(model)) > MAX_ADVANCED_MODEL_BYTES:
        raise ValueError("advanced chart model exceeds its byte limit")
    receipt = build_receipt(result, data, model, mark=definition.mark)
    return model, receipt


def build_advanced_render_spec() -> dict[str, object]:
    spec = fixed_render_spec(
        renderer_kind="advanced.svg", render_profile_id=ADVANCED_RENDER_PROFILE_ID
    )
    validate_schema(spec, "advanced-render-spec-v1.schema.json")
    return spec
