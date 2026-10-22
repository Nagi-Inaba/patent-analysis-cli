"""Closed, byte-bounded contracts for the optional MCP adapter."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from patent_analysis._json_preflight import JsonPreflightError, preflight_json_bytes
from patent_analysis.analysis_budgets import MAX_MCP_SERIALIZED_RESPONSE_BYTES
from patent_analysis.canonical_v2 import (
    CanonicalizationError,
    canonical_json_bytes,
    parse_strict_json_bytes,
)

MAX_TOOL_ARGUMENT_BYTES = 1024 * 1024
MAX_STDIO_MESSAGE_BYTES = 2 * 1024 * 1024
MAX_REQUEST_ID_BYTES = 1024
MAX_TOOL_RESPONSE_BYTES = MAX_MCP_SERIALIZED_RESPONSE_BYTES - 16 * 1024
MAX_JSON_DEPTH = 64
MAX_JSON_NODES = 250_000
MAX_DECODED_STRING_CODE_POINTS = 1_000_000
MAX_SINGLE_STRING_BYTES = 512 * 1024
MAX_LIST_ITEMS = 100_000

FAILURE_MESSAGES = MappingProxyType(
    {
        "input.invalid": "Tool input is invalid",
        "input.too_large": "Tool input is too large",
        "schema.unknown": "Public schema is unavailable",
        "analysis.unknown": "Analysis is unavailable",
        "response.too_large": "Tool response is too large",
        "renderer.unavailable": "Trusted local renderer is unavailable",
        "output.conflict": "Render output conflicts with an existing artifact",
        "internal.failed": "Internal MCP adapter failure",
    }
)

_FORBIDDEN_RESPONSE_KEYS = frozenset(
    {
        "raw_rows",
        "source_fields",
        "traceback",
        "stderr",
        "environment",
        "secrets",
        "absolute_path",
    }
)


class McpContractError(ValueError):
    """One stable adapter failure that never includes caller-controlled text."""

    def __init__(self, code: str) -> None:
        if code not in FAILURE_MESSAGES:
            raise ValueError("unknown MCP failure code")
        self.code = code
        super().__init__(FAILURE_MESSAGES[code])


def _validate_json_value(
    value: object,
    *,
    depth: int,
    seen: set[int],
    counters: list[int],
    reject_unsafe_keys: bool,
    failure_code: str,
) -> None:
    counters[0] += 1
    if depth > MAX_JSON_DEPTH or counters[0] > MAX_JSON_NODES:
        raise McpContractError(failure_code)
    if value is None or isinstance(value, (bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise McpContractError(failure_code)
        return
    if isinstance(value, str):
        try:
            encoded = value.encode("utf-8")
        except UnicodeError:
            raise McpContractError(failure_code) from None
        if len(encoded) > MAX_SINGLE_STRING_BYTES:
            raise McpContractError(failure_code)
        counters[1] += len(value)
        if counters[1] > MAX_DECODED_STRING_CODE_POINTS:
            raise McpContractError(failure_code)
        return
    if isinstance(value, Mapping):
        identity = id(value)
        if identity in seen:
            raise McpContractError(failure_code)
        seen.add(identity)
        try:
            for key, item in value.items():
                if not isinstance(key, str):
                    raise McpContractError(failure_code)
                _validate_json_value(
                    key,
                    depth=depth + 1,
                    seen=seen,
                    counters=counters,
                    reject_unsafe_keys=False,
                    failure_code=failure_code,
                )
                if reject_unsafe_keys and key.casefold() in _FORBIDDEN_RESPONSE_KEYS:
                    raise McpContractError(failure_code)
                _validate_json_value(
                    item,
                    depth=depth + 1,
                    seen=seen,
                    counters=counters,
                    reject_unsafe_keys=reject_unsafe_keys,
                    failure_code=failure_code,
                )
        finally:
            seen.remove(identity)
        return
    if isinstance(value, (list, tuple)):
        if len(value) > MAX_LIST_ITEMS:
            raise McpContractError(failure_code)
        identity = id(value)
        if identity in seen:
            raise McpContractError(failure_code)
        seen.add(identity)
        try:
            for item in value:
                _validate_json_value(
                    item,
                    depth=depth + 1,
                    seen=seen,
                    counters=counters,
                    reject_unsafe_keys=reject_unsafe_keys,
                    failure_code=failure_code,
                )
        finally:
            seen.remove(identity)
        return
    raise McpContractError(failure_code)


def _canonical_clone(
    value: object,
    *,
    maximum_bytes: int,
    invalid_code: str,
    too_large_code: str,
    reject_unsafe_keys: bool,
    schema_numbers: bool = False,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise McpContractError(invalid_code)
    _validate_json_value(
        value,
        depth=0,
        seen=set(),
        counters=[0, 0],
        reject_unsafe_keys=reject_unsafe_keys,
        failure_code=invalid_code,
    )
    try:
        # JSON Schema bounds may legitimately exceed canonical result integers.
        # This exception is used only for an explicitly resolved public schema;
        # the same finite/depth/key/size validation still runs above and below.
        encoded = (
            json.dumps(
                value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
            if schema_numbers
            else canonical_json_bytes(value)
        )
    except (CanonicalizationError, TypeError, ValueError, RecursionError, UnicodeError):
        raise McpContractError(invalid_code) from None
    if len(encoded) > maximum_bytes:
        raise McpContractError(too_large_code)
    try:
        cloned = json.loads(encoded)
    except (UnicodeError, json.JSONDecodeError):
        raise McpContractError(invalid_code) from None
    if not isinstance(cloned, dict):
        raise McpContractError(invalid_code)
    return cloned


def decode_stdio_message(raw: bytes) -> dict[str, Any]:
    """Reject ambiguous or over-budget wire JSON before the SDK can interpret it."""
    if type(raw) is not bytes or len(raw) > MAX_STDIO_MESSAGE_BYTES:
        raise McpContractError("input.invalid")
    try:
        preflight_json_bytes(raw)
        value = parse_strict_json_bytes(raw)
    except (JsonPreflightError, CanonicalizationError):
        raise McpContractError("input.invalid") from None
    if not isinstance(value, dict):
        raise McpContractError("input.invalid")
    _validate_json_value(
        value,
        depth=0,
        seen=set(),
        counters=[0, 0],
        reject_unsafe_keys=False,
        failure_code="input.invalid",
    )
    request_id = value.get("id")
    if request_id is not None and (
        type(request_id) not in (str, int)
        or (isinstance(request_id, str) and len(request_id.encode("utf-8")) > MAX_REQUEST_ID_BYTES)
    ):
        raise McpContractError("input.invalid")
    return value


def decode_tool_arguments(
    raw: object,
    *,
    maximum_bytes: int = MAX_TOOL_ARGUMENT_BYTES,
) -> dict[str, Any]:
    if type(maximum_bytes) is not int or maximum_bytes <= 0:
        raise McpContractError("input.invalid")
    return _canonical_clone(
        raw,
        maximum_bytes=maximum_bytes,
        invalid_code="input.invalid",
        too_large_code="input.too_large",
        reject_unsafe_keys=False,
    )


def to_mcp_safe_result(
    value: object,
    *,
    maximum_bytes: int = MAX_TOOL_RESPONSE_BYTES,
) -> dict[str, Any]:
    if type(maximum_bytes) is not int or maximum_bytes <= 0:
        raise McpContractError("internal.failed")
    return _canonical_clone(
        value,
        maximum_bytes=maximum_bytes,
        invalid_code="internal.failed",
        too_large_code="response.too_large",
        reject_unsafe_keys=True,
    )


def success_envelope(
    value: object,
    *,
    maximum_bytes: int = MAX_TOOL_RESPONSE_BYTES,
) -> dict[str, object]:
    return {"ok": True, "content": to_mcp_safe_result(value, maximum_bytes=maximum_bytes)}


def schema_success_envelope(
    value: object, *, maximum_bytes: int = MAX_TOOL_RESPONSE_BYTES
) -> dict[str, object]:
    """Preserve trusted public JSON Schema bounds without relaxing analysis results."""
    if (
        type(maximum_bytes) is not int
        or maximum_bytes <= 0
        or not isinstance(value, Mapping)
        or set(value) != {"schema_name", "schema"}
        or not isinstance(value["schema_name"], str)
        or not isinstance(value["schema"], Mapping)
    ):
        raise McpContractError("internal.failed")
    content = _canonical_clone(
        value,
        maximum_bytes=maximum_bytes,
        invalid_code="internal.failed",
        too_large_code="response.too_large",
        reject_unsafe_keys=True,
        schema_numbers=True,
    )
    return {"ok": True, "content": content}


def failure_envelope(error: Exception) -> dict[str, object]:
    candidate = getattr(error, "code", None)
    if candidate in {
        "schema.unknown",
        "analysis.unknown",
        "input.too_large",
        "response.too_large",
    }:
        code = str(candidate)
    elif candidate in {"input.invalid", "analysis.invalid", "render.invalid"}:
        code = "input.invalid"
    elif candidate in {"renderer.unavailable", "output.conflict"}:
        code = str(candidate)
    else:
        code = "internal.failed"
    return {
        "ok": False,
        "error": {"code": code, "message": FAILURE_MESSAGES[code]},
    }


__all__ = (
    "FAILURE_MESSAGES",
    "MAX_STDIO_MESSAGE_BYTES",
    "MAX_TOOL_ARGUMENT_BYTES",
    "MAX_TOOL_RESPONSE_BYTES",
    "McpContractError",
    "decode_tool_arguments",
    "failure_envelope",
    "schema_success_envelope",
    "success_envelope",
    "to_mcp_safe_result",
)
