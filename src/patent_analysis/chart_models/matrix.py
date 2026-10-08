"""Closed neutral chart-model builders for native matrix analyses."""

from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from importlib.resources import files
from typing import Any

from patent_analysis._render_canonical import canonical_json_bytes, sha256_bytes
from patent_analysis.analysis_contracts import StrictDraft202012Validator
from patent_analysis.v2_contracts import validate_analysis_result_v2

MATRIX_BUBBLE_MARK = "matrix-bubble-svg.v1"
MATRIX_HEATMAP_MARK = "matrix-heatmap-svg.v1"
MATRIX_RENDER_MARKS = (MATRIX_BUBBLE_MARK, MATRIX_HEATMAP_MARK)
MATRIX_RENDER_PROFILE_ID = "matrix-svg-ja-jp-node22-echarts6.v1"


def _schema(name: str) -> dict[str, Any]:
    try:
        value = json.loads(
            files("patent_analysis")
            .joinpath("schemas", name)
            .read_text(encoding="utf-8")
        )
    except (FileNotFoundError, json.JSONDecodeError, UnicodeError):
        raise ValueError("matrix renderer schema is unavailable") from None
    if not isinstance(value, dict):
        raise ValueError("matrix renderer schema is invalid")
    return value


def _validate(value: object, schema_name: str) -> None:
    errors = sorted(
        StrictDraft202012Validator(_schema(schema_name)).iter_errors(value),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        raise ValueError("matrix renderer contract is invalid")


def _coerce_result(value: object) -> dict[str, Any]:
    if type(value) is bytes:
        try:
            value = json.loads(value.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("matrix analysis document is invalid") from None
    if not isinstance(value, Mapping):
        raise ValueError("matrix analysis document is invalid")
    try:
        result = validate_analysis_result_v2(dict(value))
    except Exception:
        raise ValueError("matrix analysis document is invalid") from None
    if result.get("analysis_id") != "matrix.v1" or result.get("result_variant") != "matrix":
        raise ValueError("matrix analysis document is incompatible")
    _validate(result.get("data"), "matrix-result-v1.schema.json")
    return result


def _mark_chart_type(mark: str) -> str:
    if mark == MATRIX_BUBBLE_MARK:
        return "matrix.bubble"
    if mark == MATRIX_HEATMAP_MARK:
        return "matrix.heatmap"
    raise ValueError("unknown matrix renderer mark")


def build_matrix_chart_model(
    analysis_result: object,
    *,
    mark: str,
) -> tuple[dict[str, object], dict[str, object]]:
    """Build a fixed neutral model without changing axis or sparse-cell order."""

    chart_type = _mark_chart_type(mark)
    result = _coerce_result(analysis_result)
    data = result["data"]
    assert isinstance(data, dict)

    x_source = data["x_axis"]
    y_source = data["y_axis"]
    assert isinstance(x_source, dict) and isinstance(y_source, dict)
    x_categories = [
        {
            "id": f"x:{index}",
            "index": index,
            "label": item["label"],
            "count": item["count"],
            "is_other": item["is_other"],
        }
        for index, item in enumerate(x_source["categories"])
    ]
    y_categories = [
        {
            "id": f"y:{index}",
            "index": index,
            "label": item["label"],
            "count": item["count"],
            "is_other": item["is_other"],
        }
        for index, item in enumerate(y_source["categories"])
    ]
    cells = [
        {
            "x_index": item["x_index"],
            "y_index": item["y_index"],
            "x_label": item["x_label"],
            "y_label": item["y_label"],
            "value": item["value"],
            "row_count": item["row_count"],
        }
        for item in data["cells"]
    ]
    analysis_bytes = canonical_json_bytes(result)
    data_bytes = canonical_json_bytes(data)
    model: dict[str, object] = {
        "chart_model_contract_version": "1.0.0",
        "chart_type": chart_type,
        "mark": mark,
        "analysis_result_sha256": sha256_bytes(analysis_bytes),
        "title": f"{x_source['role']} × {y_source['role']}",
        "x_axis": {
            "role": x_source["role"],
            "categories": x_categories,
        },
        "y_axis": {
            "role": y_source["role"],
            "categories": y_categories,
        },
        "cells": cells,
        "population": deepcopy(result["population"]),
        "warnings": list(result["warnings"]),
    }
    _validate(model, "matrix-chart-model-v1.schema.json")
    model_bytes = canonical_json_bytes(model)
    receipt: dict[str, object] = {
        "matrix_chart_model_build_receipt_version": "1.0.0",
        "analysis_result_sha256": model["analysis_result_sha256"],
        "result_data_sha256": sha256_bytes(data_bytes),
        "chart_model_sha256": sha256_bytes(model_bytes),
        "mark": mark,
    }
    _validate(receipt, "matrix-chart-model-build-receipt.schema.json")
    return deepcopy(model), deepcopy(receipt)


def build_matrix_render_spec(
    *,
    mark: str,
    x_count: int,
    y_count: int,
) -> dict[str, object]:
    chart_type = _mark_chart_type(mark)
    if (
        type(x_count) is not int
        or type(y_count) is not int
        or not 0 <= x_count <= 101
        or not 0 <= y_count <= 101
    ):
        raise ValueError("matrix render dimensions are invalid")
    spec: dict[str, object] = {
        "render_spec_contract_version": "1.0.0",
        "renderer_kind": (
            "matrix.bubble.svg" if chart_type == "matrix.bubble" else "matrix.heatmap.svg"
        ),
        "locale": "ja-JP",
        "timezone": "UTC",
        "width": 1200,
        "height": 675,
        "font_family": "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif",
        "animation": False,
        "axis_label_max_graphemes": 28,
        "echarts_version": "6.1.0",
        "render_profile_id": MATRIX_RENDER_PROFILE_ID,
    }
    _validate(spec, "matrix-render-spec-v1.schema.json")
    return deepcopy(spec)


__all__ = (
    "MATRIX_BUBBLE_MARK",
    "MATRIX_HEATMAP_MARK",
    "MATRIX_RENDER_MARKS",
    "MATRIX_RENDER_PROFILE_ID",
    "build_matrix_chart_model",
    "build_matrix_render_spec",
)
