"""Closed neutral chart-model builders for native matrix analyses."""

from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from importlib.resources import files
from typing import Any

from patent_analysis._render_canonical import canonical_json_bytes, sha256_bytes
from patent_analysis.analysis_contracts import StrictDraft202012Validator
from patent_analysis.render_palettes import apply_render_palette
from patent_analysis.v2_contracts import validate_analysis_result_v2

MATRIX_BUBBLE_MARK = "matrix-bubble-svg.v1"
MATRIX_HEATMAP_MARK = "matrix-heatmap-svg.v1"
MATRIX_RENDER_MARKS = (MATRIX_BUBBLE_MARK, MATRIX_HEATMAP_MARK)
MATRIX_RENDER_PROFILE_ID = "matrix-svg-ja-jp-node24-echarts6.v1"


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


def _pie_model(
    data: Mapping[str, Any],
) -> tuple[dict[str, object] | None, dict[str, int]]:
    """The pie legend with stable category ids, and the index each label maps to."""

    pie = data.get("pie")
    cells = data["cells"]
    invalid = ValueError("matrix analysis document is invalid")
    if pie is None:
        if any("slices" in cell for cell in cells):
            raise invalid
        return None, {}
    if not all("slices" in cell for cell in cells):
        raise invalid
    categories = [
        {
            "id": f"p:{index}",
            "index": index,
            "label": item["label"],
            "count": item["count"],
            "is_other": item["is_other"],
        }
        for index, item in enumerate(pie["categories"])
    ]
    index_by_label = {item["label"]: item["index"] for item in categories}
    if len(index_by_label) != len(categories):
        raise invalid
    return {"role": pie["role"], "categories": categories}, index_by_label


def _cell_slices(
    cell: Mapping[str, Any], index_by_label: Mapping[str, int]
) -> list[dict[str, object]]:
    labels = [item["label"] for item in cell["slices"]]
    if len(set(labels)) != len(labels) or any(label not in index_by_label for label in labels):
        raise ValueError("matrix analysis document is invalid")
    return [
        {"index": index_by_label[item["label"]], "label": item["label"], "count": item["count"]}
        for item in cell["slices"]
    ]


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
    pie, index_by_label = _pie_model(data)
    cells = [
        {
            "x_index": item["x_index"],
            "y_index": item["y_index"],
            "x_label": item["x_label"],
            "y_label": item["y_label"],
            "value": item["value"],
            "row_count": item["row_count"],
            **({"slices": _cell_slices(item, index_by_label)} if pie is not None else {}),
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
    if pie is not None:
        model["pie"] = pie
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


MATRIX_VALUE_LABELS = ("hidden", "shown")


def build_matrix_render_spec(
    *,
    mark: str,
    x_count: int,
    y_count: int,
    value_labels: str | None = None,
    palette: str | None = None,
) -> dict[str, object]:
    chart_type = _mark_chart_type(mark)
    if (
        type(x_count) is not int
        or type(y_count) is not int
        or not 0 <= x_count <= 101
        or not 0 <= y_count <= 101
    ):
        raise ValueError("matrix render dimensions are invalid")
    # Only the bubble mark has count labels. "hidden" is the default, so it is left out of the
    # spec: a default render keeps the same spec bytes (and hash) as before the option existed.
    if value_labels is not None and (
        value_labels not in MATRIX_VALUE_LABELS or chart_type != "matrix.bubble"
    ):
        raise ValueError("matrix value labels option is invalid")
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
    if value_labels == "shown":
        spec["value_labels"] = value_labels
    apply_render_palette(spec, palette)
    _validate(spec, "matrix-render-spec-v1.schema.json")
    return deepcopy(spec)


__all__ = (
    "MATRIX_BUBBLE_MARK",
    "MATRIX_HEATMAP_MARK",
    "MATRIX_RENDER_MARKS",
    "MATRIX_RENDER_PROFILE_ID",
    "MATRIX_VALUE_LABELS",
    "build_matrix_chart_model",
    "build_matrix_render_spec",
)
