from __future__ import annotations

import json
import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from jsonschema.exceptions import SchemaError, ValidationError

from patent_analysis._render_canonical import (
    CanonicalJsonError,
    canonical_json_bytes,
    sha256_bytes,
    strict_b64decode,
    strict_b64encode,
)
from patent_analysis._render_contracts import (
    RenderContractError,
    get_chart_model_build_receipt_schema,
    validate_chart_model,
    validate_label_overlay_pack,
    validate_render_spec,
)
from patent_analysis._render_text import RenderTextError, truncate_title_dimension
from patent_analysis._version import PACKAGE_VERSION
from patent_analysis.analysis import _canonical_sha256 as existing_result_sha256
from patent_analysis.analysis_contracts import (
    AnalysisContractError,
    StrictDraft202012Validator,
    validate_analysis_result,
)
from patent_analysis.render_palettes import apply_render_palette

T = TypeVar("T")

_ENVELOPE_FIELDS = {"analysis_contract_version", "ok", "result", "receipt"}
_RECEIPT_FIELDS = {
    "algorithm_id",
    "package_version",
    "input_sha256",
    "spec_sha256",
    "result_sha256",
}
_LOWERCASE_HEX = frozenset("0123456789abcdef")
_MAX_ENVELOPE_DEPTH = 64
_MAX_ENVELOPE_NODES = 250_000
_MAX_ENVELOPE_STRING_CODE_POINTS = 2_000_000
_MAX_RENDER_ROWS = 101
_MAX_RENDER_WARNINGS = 32
_MAX_RENDER_SOURCE_CODE_POINTS = 4096

KNOWN_CALLER_FAILURES = (
    AnalysisContractError,
    CanonicalJsonError,
    RenderTextError,
    json.JSONDecodeError,
    ValidationError,
    SchemaError,
    TypeError,
    ValueError,
    RecursionError,
)


@dataclass(frozen=True)
class _ValidatedChartInputs:
    result: dict[str, Any]
    analysis_result_sha256: str
    overlay: dict[str, Any] | None
    label_overlay_sha256: str | None


def _translate_contract_failure(operation: Callable[[], T]) -> T:
    failed = False
    try:
        return operation()
    except RenderContractError:
        raise
    except KNOWN_CALLER_FAILURES:
        failed = True
    if failed:
        del operation
        raise RenderContractError()
    raise AssertionError("unreachable contract translation state")


def _is_lowercase_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in _LOWERCASE_HEX for character in value)
    )


def _preflight_analyze_envelope(value: Any) -> None:
    node_count = 0
    string_code_points = 0
    active_containers: set[int] = set()
    stack: list[tuple[str, Any, int]] = [("visit", value, 0)]

    while stack:
        action, current, depth = stack.pop()
        if action == "exit":
            active_containers.remove(id(current))
            continue
        if action == "dict_items":
            try:
                key, item = next(current)
            except StopIteration:
                continue
            if not isinstance(key, str):
                raise ValueError
            node_count += 1
            string_code_points += len(key)
            if (
                node_count > _MAX_ENVELOPE_NODES
                or string_code_points > _MAX_ENVELOPE_STRING_CODE_POINTS
                or any(0xD800 <= ord(character) <= 0xDFFF for character in key)
            ):
                raise ValueError
            stack.append(("dict_items", current, depth))
            stack.append(("visit", item, depth + 1))
            continue
        if action == "list_items":
            try:
                item = next(current)
            except StopIteration:
                continue
            stack.append(("list_items", current, depth))
            stack.append(("visit", item, depth + 1))
            continue

        if depth > _MAX_ENVELOPE_DEPTH:
            raise ValueError
        node_count += 1
        if node_count > _MAX_ENVELOPE_NODES:
            raise ValueError
        if isinstance(current, str):
            string_code_points += len(current)
            if string_code_points > _MAX_ENVELOPE_STRING_CODE_POINTS or any(
                0xD800 <= ord(character) <= 0xDFFF for character in current
            ):
                raise ValueError
            continue
        if current is None or isinstance(current, (bool, int)):
            continue
        if isinstance(current, float):
            if not math.isfinite(current):
                raise ValueError
            continue
        if isinstance(current, dict):
            container_id = id(current)
            if container_id in active_containers:
                raise ValueError
            active_containers.add(container_id)
            stack.append(("exit", current, depth))
            stack.append(("dict_items", iter(current.items()), depth))
            continue
        if isinstance(current, list):
            container_id = id(current)
            if container_id in active_containers:
                raise ValueError
            active_containers.add(container_id)
            stack.append(("exit", current, depth))
            stack.append(("list_items", iter(current), depth))
            continue
        raise ValueError


def _preflight_render_boundary(value: Any) -> None:
    if not isinstance(value, dict):
        return
    result = value.get("result")
    if not isinstance(result, dict):
        return

    dimension = result.get("dimension")
    if isinstance(dimension, str) and len(dimension) > _MAX_RENDER_SOURCE_CODE_POINTS:
        raise ValueError
    measure = result.get("measure")
    if isinstance(measure, dict):
        column = measure.get("column")
        if isinstance(column, str) and len(column) > _MAX_RENDER_SOURCE_CODE_POINTS:
            raise ValueError

    rows = result.get("rows")
    if isinstance(rows, list):
        if len(rows) > _MAX_RENDER_ROWS:
            raise ValueError
        for row in rows:
            if not isinstance(row, dict):
                continue
            label = row.get("label")
            if isinstance(label, str) and len(label) > _MAX_RENDER_SOURCE_CODE_POINTS:
                raise ValueError

    warnings = result.get("warnings")
    if isinstance(warnings, list):
        if len(warnings) > _MAX_RENDER_WARNINGS:
            raise ValueError
        if any(
            isinstance(warning, str)
            and len(warning) > _MAX_RENDER_SOURCE_CODE_POINTS
            for warning in warnings
        ):
            raise ValueError


def _validate_envelope(analyze_success_envelope: Any) -> tuple[dict[str, Any], str]:
    _preflight_analyze_envelope(analyze_success_envelope)
    _preflight_render_boundary(analyze_success_envelope)
    if (
        not isinstance(analyze_success_envelope, dict)
        or set(analyze_success_envelope) != _ENVELOPE_FIELDS
        or analyze_success_envelope["analysis_contract_version"] != "1.0.0"
        or analyze_success_envelope["ok"] is not True
    ):
        raise ValueError

    receipt = analyze_success_envelope["receipt"]
    if (
        not isinstance(receipt, dict)
        or set(receipt) != _RECEIPT_FIELDS
        or receipt["algorithm_id"] != "ranking.v1"
        or receipt["package_version"] != PACKAGE_VERSION
        or not all(
            _is_lowercase_sha256(receipt[field])
            for field in ("input_sha256", "spec_sha256", "result_sha256")
        )
    ):
        raise ValueError

    result = validate_analysis_result(analyze_success_envelope["result"])
    analysis_result_sha256 = existing_result_sha256(result)
    if receipt["result_sha256"] != analysis_result_sha256:
        raise ValueError
    return result, analysis_result_sha256


def _validate_overlay_binding(
    result: dict[str, Any],
    analysis_result_sha256: str,
    overlay: Any,
) -> tuple[dict[str, Any], str]:
    validated_overlay = validate_label_overlay_pack(overlay)
    result_rows = result["rows"]
    overlay_rows = validated_overlay["rows"]
    if (
        validated_overlay["analysis_result_sha256"] != analysis_result_sha256
        or validated_overlay["dimension"]["source_label"] != result["dimension"]
        or len(overlay_rows) != len(result_rows)
    ):
        raise ValueError

    for index, (result_row, overlay_row) in enumerate(
        zip(result_rows, overlay_rows, strict=True)
    ):
        if (
            overlay_row["index"] != index
            or overlay_row["row_kind"] != result_row["row_kind"]
            or overlay_row["source_label"] != result_row["label"]
        ):
            raise ValueError

    overlay_sha256 = sha256_bytes(canonical_json_bytes(validated_overlay))
    return validated_overlay, overlay_sha256


def _resolve_chart_inputs_impl(
    analyze_success_envelope: Any,
    overlay: Any,
) -> _ValidatedChartInputs:
    result, analysis_result_sha256 = _validate_envelope(analyze_success_envelope)
    if overlay is None:
        return _ValidatedChartInputs(
            result=result,
            analysis_result_sha256=analysis_result_sha256,
            overlay=None,
            label_overlay_sha256=None,
        )

    validated_overlay, overlay_sha256 = _validate_overlay_binding(
        result,
        analysis_result_sha256,
        overlay,
    )
    return _ValidatedChartInputs(
        result=result,
        analysis_result_sha256=analysis_result_sha256,
        overlay=validated_overlay,
        label_overlay_sha256=overlay_sha256,
    )


def _resolve_chart_inputs(
    analyze_success_envelope: Any,
    overlay: Any,
) -> _ValidatedChartInputs:
    return _translate_contract_failure(
        lambda: _resolve_chart_inputs_impl(analyze_success_envelope, overlay)
    )


def _build_ranking_chart_model_impl(
    analyze_success_envelope: Any,
    overlay: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    inputs = _resolve_chart_inputs(analyze_success_envelope, overlay)
    result = inputs.result
    dimension_overlay = inputs.overlay["dimension"] if inputs.overlay is not None else None
    row_overlays = inputs.overlay["rows"] if inputs.overlay is not None else None

    dimension_source_label = result["dimension"]
    dimension_display_label = (
        dimension_overlay["display_label"]
        if dimension_overlay is not None
        else dimension_source_label
    )
    rows = []
    for index, source_row in enumerate(result["rows"]):
        row_overlay = row_overlays[index] if row_overlays is not None else None
        rows.append(
            {
                "index": index,
                "row_kind": source_row["row_kind"],
                "source_label": source_row["label"],
                "display_label": (
                    row_overlay["display_label"]
                    if row_overlay is not None
                    else source_row["label"]
                ),
                "description": row_overlay["description"] if row_overlay is not None else None,
                "semantic_label": (
                    "データ中の分類値"
                    if source_row["row_kind"] == "dimension_value"
                    else "上位表示外の合計"
                ),
                "value": source_row["value"],
                "count": source_row["count"],
                "share": source_row["share"],
            }
        )

    model = validate_chart_model(
        {
            "chart_model_contract_version": "1.0.0",
            "chart_type": "ranking.horizontal_bar",
            "analysis_result_sha256": inputs.analysis_result_sha256,
            "label_overlay_sha256": inputs.label_overlay_sha256,
            "title": truncate_title_dimension(dimension_display_label),
            "dimension": {
                "source_label": dimension_source_label,
                "display_label": dimension_display_label,
                "description": (
                    dimension_overlay["description"] if dimension_overlay is not None else None
                ),
            },
            "measure": {
                "mode": result["measure"]["mode"],
                "column": result["measure"]["column"],
            },
            "population": {
                "input_rows": result["population"]["input_rows"],
                "analyzed_rows": result["population"]["analyzed_rows"],
            },
            "rows": rows,
            "warnings": list(result["warnings"]),
        }
    )

    model_bytes = canonical_json_bytes(model)
    model_sha256 = sha256_bytes(model_bytes)
    receipt = {
        "chart_model_build_receipt_version": "1.0.0",
        "analysis_result_sha256": inputs.analysis_result_sha256,
        "label_overlay_sha256": inputs.label_overlay_sha256,
        "chart_model_sha256": model_sha256,
        "chart_model_bytes": strict_b64encode(model_bytes),
        "row_count": len(model["rows"]),
        "builder_id": "patent-analysis.ranking-chart-model-builder",
        "builder_version": PACKAGE_VERSION,
    }
    receipt_schema = get_chart_model_build_receipt_schema()
    if next(StrictDraft202012Validator(receipt_schema).iter_errors(receipt), None) is not None:
        raise ValueError
    receipt_bytes = strict_b64decode(
        receipt["chart_model_bytes"],
        max_decoded_bytes=2 * 1024 * 1024,
    )
    if (
        receipt_bytes != model_bytes
        or receipt["chart_model_sha256"] != model_sha256
        or receipt["analysis_result_sha256"] != inputs.analysis_result_sha256
        or receipt["analysis_result_sha256"] != model["analysis_result_sha256"]
        or receipt["label_overlay_sha256"] != inputs.label_overlay_sha256
        or receipt["label_overlay_sha256"] != model["label_overlay_sha256"]
        or receipt["row_count"] != len(model["rows"])
    ):
        raise ValueError
    return model, dict(receipt)


def build_ranking_chart_model(
    analyze_success_envelope: Any,
    *,
    overlay: Any = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    return _translate_contract_failure(
        lambda: _build_ranking_chart_model_impl(analyze_success_envelope, overlay)
    )


def _build_ranking_render_spec_impl(
    *, row_count: int, palette: str | None = None
) -> dict[str, Any]:
    if isinstance(row_count, bool) or not isinstance(row_count, int) or not 0 <= row_count <= 101:
        raise ValueError
    spec = {
        "render_spec_contract_version": "1.0.0",
        "renderer_kind": "ranking.horizontal_bar.svg",
        "locale": "ja-JP",
        "timezone": "UTC",
        "width": 1200,
        "height": max(675, 160 + 36 * row_count),
        "font_family": "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif",
        "animation": False,
        "axis_label_max_graphemes": 28,
        "echarts_version": "6.1.0",
        "render_profile_id": "ranking-svg-ja-jp-node24-echarts6.v1",
    }
    apply_render_palette(spec, palette)
    return validate_render_spec(spec, row_count=row_count)


def build_ranking_render_spec(*, row_count: int, palette: str | None = None) -> dict[str, Any]:
    return _translate_contract_failure(
        lambda: _build_ranking_render_spec_impl(row_count=row_count, palette=palette)
    )
