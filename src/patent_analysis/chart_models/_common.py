"""Shared closed helpers for v2 neutral chart-model builders."""

from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from importlib.resources import files
from typing import Any

from patent_analysis._render_canonical import canonical_json_bytes, sha256_bytes
from patent_analysis.analysis_contracts import (
    AnalysisContractError,
    StrictDraft202012Validator,
)
from patent_analysis.v2_contracts import validate_analysis_result_v2


def load_schema(name: str) -> dict[str, Any]:
    """Load one packaged chart-model schema without allowing path traversal."""

    if not isinstance(name, str) or not name or "/" in name or "\\" in name or ".." in name:
        raise ValueError("chart-model schema name is invalid")
    try:
        value = json.loads(
            files("patent_analysis").joinpath("schemas", name).read_text(encoding="utf-8")
        )
    except (FileNotFoundError, json.JSONDecodeError, UnicodeError):
        raise ValueError("chart-model schema is unavailable") from None
    if not isinstance(value, dict):
        raise ValueError("chart-model schema is invalid")
    return value


def validate_schema(value: object, schema_name: str) -> None:
    """Validate a value against a closed packaged schema."""

    errors = sorted(
        StrictDraft202012Validator(load_schema(schema_name)).iter_errors(value),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        raise ValueError("chart-model contract is invalid")


def coerce_analysis_result(
    value: object,
    *,
    analysis_id: str,
    result_variant: str,
    result_schema: str,
) -> dict[str, Any]:
    """Validate and copy one compatible neutral AnalysisResultV2 document."""

    if type(value) is bytes:
        try:
            value = json.loads(value.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("analysis document is invalid") from None
    if not isinstance(value, Mapping):
        raise ValueError("analysis document is invalid")
    try:
        result = validate_analysis_result_v2(dict(value))
    except AnalysisContractError:
        raise ValueError("analysis document is invalid") from None
    if result.get("analysis_id") != analysis_id or result.get("result_variant") != result_variant:
        raise ValueError("analysis document is incompatible")
    validate_schema(result.get("data"), result_schema)
    return deepcopy(result)


def build_receipt(
    result: Mapping[str, object],
    data: object,
    model: Mapping[str, object],
    *,
    mark: str,
) -> dict[str, object]:
    """Build the canonical receipt shared by new neutral chart-model families."""

    return {
        "chart_model_build_receipt_version": "1.0.0",
        "analysis_result_sha256": sha256_bytes(canonical_json_bytes(result)),
        "result_data_sha256": sha256_bytes(canonical_json_bytes(data)),
        "chart_model_sha256": sha256_bytes(canonical_json_bytes(model)),
        "mark": mark,
    }


def fixed_render_spec(*, renderer_kind: str, render_profile_id: str) -> dict[str, object]:
    """Return the immutable trusted-local renderer settings for a closed mark."""

    return {
        "render_spec_contract_version": "1.0.0",
        "renderer_kind": renderer_kind,
        "locale": "ja-JP",
        "timezone": "UTC",
        "width": 1200,
        "height": 675,
        "font_family": "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif",
        "animation": False,
        "axis_label_max_graphemes": 28,
        "echarts_version": "6.1.0",
        "render_profile_id": render_profile_id,
    }


__all__ = (
    "build_receipt",
    "coerce_analysis_result",
    "fixed_render_spec",
    "load_schema",
    "validate_schema",
)
