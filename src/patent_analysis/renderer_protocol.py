from __future__ import annotations

import json
import re
import struct
from json.decoder import scanstring
from typing import Any, NoReturn

from patent_analysis._render_canonical import (
    CanonicalJsonError,
    canonical_json_bytes,
    sha256_bytes,
    strict_b64decode,
)
from patent_analysis.analysis_contracts import StrictDraft202012Validator
from patent_analysis.renderer_resources import (
    MAX_RENDERER_BUNDLE_BYTES,
    RendererProtocolError,
    RendererRuntimeBinding,
    _load_verified_renderer_schema_bytes,
)

RENDERER_FRAME_MAGIC = b"PARSVG01"
RENDERER_FRAME_VERSION = 1
RENDERER_FRAME_HEADER_BYTES = 20
MAX_RENDERER_REQUEST_JSON_BYTES = 3 * 1024 * 1024
MAX_RENDERER_FRAME_BYTES = 7 * 1024 * 1024
MAX_RENDERER_STDOUT_BYTES = 12 * 1024 * 1024
MAX_RENDERER_SVG_BYTES = 8 * 1024 * 1024

_MAX_RENDERER_JSON_DEPTH = 64
_MAX_RENDERER_JSON_TOKENS = 250_000
_MAX_RENDERER_NUMERIC_LEXEME_BYTES = 128
_MAX_RENDERER_DECODED_STRING_CODE_POINTS = 2_000_000
_MAX_RENDERER_SVG_B64_BYTES = 11_184_812
_CANONICAL_BASE64_BYTES = re.compile(
    rb"^(?:[A-Za-z0-9+/]{4})*"
    rb"(?:[A-Za-z0-9+/][AQgw]==|[A-Za-z0-9+/]{2}[AEIMQUYcgkosw048]=)?$"
)

_MAX_CHART_MODEL_BYTES = 2 * 1024 * 1024
_MAX_RENDER_SPEC_BYTES = 16 * 1024
_REQUEST_FIELDS = {
    "protocol_version",
    "chart_model_b64",
    "chart_model_sha256",
    "render_spec_b64",
    "render_spec_sha256",
}
_FAILURE_PAIRS = {
    "protocol.invalid": "Renderer protocol is invalid",
    "payload.too_large": "Renderer payload is too large",
    "digest.mismatch": "Renderer payload digest does not match",
    "schema.invalid": "Renderer input was rejected",
    "runtime.mismatch": "Renderer runtime does not match",
    "render.failed": "Renderer failed",
}
_DECLARED_ERROR_TOKEN = object()


class RendererDeclaredError(ValueError):
    """A renderer-declared error restricted to the approved fixed pairs."""

    def __init__(
        self,
        code: str,
        safe_message: str,
        *,
        _token: object | None = None,
    ) -> None:
        if _token is not _DECLARED_ERROR_TOKEN or _FAILURE_PAIRS.get(code) != safe_message:
            raise RendererProtocolError() from None
        super().__init__(safe_message)
        self.code = code
        self.safe_message = safe_message
        self.__suppress_context__ = True


class _ProtocolViolation(ValueError):
    pass


def _validated_declared_error(code: str, message: str) -> RendererDeclaredError:
    if _FAILURE_PAIRS.get(code) != message:
        raise RendererProtocolError() from None
    return RendererDeclaredError(code, message, _token=_DECLARED_ERROR_TOKEN)


def _reject_constant(_value: str) -> NoReturn:
    raise _ProtocolViolation


def _closed_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _ProtocolViolation
        result[key] = value
    return result


def _load_schema(name: str) -> dict[str, Any]:
    raw = _load_verified_renderer_schema_bytes(name)
    schema = json.loads(raw.decode("utf-8"))
    if not isinstance(schema, dict):
        raise _ProtocolViolation
    return schema


def _schema_valid(value: object, name: str) -> None:
    schema = _load_schema(name)
    if next(StrictDraft202012Validator(schema).iter_errors(value), None) is not None:
        raise _ProtocolViolation


def _encode_frame_parts(bundle: bytes, request_bytes: bytes) -> bytes:
    if type(bundle) is not bytes or type(request_bytes) is not bytes:
        raise RendererProtocolError() from None
    bundle_length = len(bundle)
    request_length = len(request_bytes)
    total_length = RENDERER_FRAME_HEADER_BYTES + bundle_length + request_length
    if (
        bundle_length > MAX_RENDERER_BUNDLE_BYTES
        or request_length > MAX_RENDERER_REQUEST_JSON_BYTES
        or total_length > MAX_RENDERER_FRAME_BYTES
    ):
        raise RendererProtocolError() from None
    try:
        header = struct.pack(
            ">8sIII",
            RENDERER_FRAME_MAGIC,
            RENDERER_FRAME_VERSION,
            bundle_length,
            request_length,
        )
    except (OverflowError, struct.error):
        raise RendererProtocolError() from None
    return header + bundle + request_bytes


def _encode_renderer_frame_impl(bundle: bytes, request: dict[str, object]) -> bytes:
    if type(bundle) is not bytes or type(request) is not dict or set(request) != _REQUEST_FIELDS:
        raise _ProtocolViolation
    _schema_valid(request, "renderer-request.schema.json")
    chart = strict_b64decode(request["chart_model_b64"], _MAX_CHART_MODEL_BYTES)  # type: ignore[arg-type]
    render_spec = strict_b64decode(request["render_spec_b64"], _MAX_RENDER_SPEC_BYTES)  # type: ignore[arg-type]
    if (
        sha256_bytes(chart) != request["chart_model_sha256"]
        or sha256_bytes(render_spec) != request["render_spec_sha256"]
    ):
        raise _ProtocolViolation
    request_bytes = canonical_json_bytes(
        {
            "protocol_version": request["protocol_version"],
            "chart_model_b64": request["chart_model_b64"],
            "chart_model_sha256": request["chart_model_sha256"],
            "render_spec_b64": request["render_spec_b64"],
            "render_spec_sha256": request["render_spec_sha256"],
        }
    )
    return _encode_frame_parts(bundle, request_bytes)


def encode_renderer_frame(bundle: bytes, request: dict[str, object]) -> bytes:
    frame: bytes | None = None
    failed = False
    try:
        frame = _encode_renderer_frame_impl(bundle, request)
    except (
        _ProtocolViolation,
        CanonicalJsonError,
        RendererProtocolError,
        OSError,
        TypeError,
        ValueError,
        OverflowError,
        RecursionError,
    ):
        failed = True
    if failed or frame is None:
        raise RendererProtocolError() from None
    return frame


def _runtime_object(runtime: RendererRuntimeBinding) -> dict[str, str]:
    return {
        "node_version": runtime.node_version,
        "echarts_version": runtime.echarts_version,
        "renderer_build_digest": runtime.renderer_build_digest,
        "render_profile_id": runtime.render_profile_id,
    }


def _serialize_closed_response(value: dict[str, Any]) -> bytes:
    runtime = value["runtime"]
    ordered: dict[str, Any] = {
        "protocol_version": value["protocol_version"],
        "ok": value["ok"],
        "runtime": {
            "node_version": runtime["node_version"],
            "echarts_version": runtime["echarts_version"],
            "renderer_build_digest": runtime["renderer_build_digest"],
            "render_profile_id": runtime["render_profile_id"],
        },
    }
    if value["ok"] is True:
        ordered["svg_b64"] = value["svg_b64"]
    else:
        ordered["error"] = {
            "code": value["error"]["code"],
            "message": value["error"]["message"],
        }
    return json.dumps(ordered, ensure_ascii=True, separators=(",", ":")).encode("ascii") + b"\n"


def _scan_json_string(raw: bytes, start: int) -> tuple[int, int]:
    index = start + 1
    decoded_code_points = 0
    while index < len(raw):
        current = raw[index]
        if current == 0x22:
            return index + 1, decoded_code_points
        if current < 0x20 or current > 0x7F:
            raise _ProtocolViolation
        if current != 0x5C:
            decoded_code_points += 1
            index += 1
            continue
        if index + 1 >= len(raw):
            raise _ProtocolViolation
        escaped = raw[index + 1]
        if escaped in b'"\\/bfnrt':
            decoded_code_points += 1
            index += 2
            continue
        if escaped != ord("u") or index + 6 > len(raw):
            raise _ProtocolViolation
        digits = raw[index + 2 : index + 6]
        if any(value not in b"0123456789abcdefABCDEF" for value in digits):
            raise _ProtocolViolation
        code_unit = int(digits, 16)
        if 0xD800 <= code_unit <= 0xDBFF:
            if index + 12 > len(raw) or raw[index + 6 : index + 8] != b"\\u":
                raise _ProtocolViolation
            low_digits = raw[index + 8 : index + 12]
            if any(value not in b"0123456789abcdefABCDEF" for value in low_digits):
                raise _ProtocolViolation
            low_unit = int(low_digits, 16)
            if not 0xDC00 <= low_unit <= 0xDFFF:
                raise _ProtocolViolation
            decoded_code_points += 1
            index += 12
            continue
        if 0xDC00 <= code_unit <= 0xDFFF:
            raise _ProtocolViolation
        decoded_code_points += 1
        index += 6
    raise _ProtocolViolation


def _decoded_json_key(raw: bytes, start: int, end: int) -> str:
    try:
        token = raw[start:end].decode("ascii")
        decoded, consumed = scanstring(token, 1, True)
    except (UnicodeDecodeError, ValueError):
        raise _ProtocolViolation from None
    if consumed != len(token):
        raise _ProtocolViolation
    return decoded


def _preflight_renderer_json(raw: bytes) -> None:
    if type(raw) is not bytes or not raw or b"\x00" in raw:
        raise _ProtocolViolation
    try:
        raw.decode("ascii")
    except UnicodeDecodeError:
        raise _ProtocolViolation from None
    if raw[:1] != b"{" or raw[-1:] != b"}":
        raise _ProtocolViolation

    stack: list[dict[str, Any]] = []
    root_seen = False
    root_ok_true = False
    decoded_string_code_points = 0
    token_count = 0
    last_significant: int | None = None
    index = 0

    def add_token() -> None:
        nonlocal token_count
        token_count += 1
        if token_count > _MAX_RENDERER_JSON_TOKENS:
            raise _ProtocolViolation

    while index < len(raw):
        current = raw[index]
        if current in b" \t\r\n":
            index += 1
            continue
        if current in (ord("{"), ord("[")):
            if not stack:
                if root_seen or current != ord("{"):
                    raise _ProtocolViolation
                root_seen = True
            stack.append(
                {
                    "kind": current,
                    "keys": set() if current == ord("{") else None,
                    "last_key": None,
                    "last_key_raw": None,
                }
            )
            if len(stack) > _MAX_RENDERER_JSON_DEPTH:
                raise _ProtocolViolation
            add_token()
            last_significant = current
            index += 1
            continue
        if current in (ord("}"), ord("]")):
            expected = ord("{") if current == ord("}") else ord("[")
            if not stack or stack[-1]["kind"] != expected:
                raise _ProtocolViolation
            stack.pop()
            if not stack and index != len(raw) - 1:
                raise _ProtocolViolation
            last_significant = current
            index += 1
            continue
        if current == ord('"'):
            end, decoded_length = _scan_json_string(raw, index)
            probe = end
            while probe < len(raw) and raw[probe] in b" \t\r\n":
                probe += 1
            is_key = bool(
                stack
                and stack[-1]["kind"] == ord("{")
                and probe < len(raw)
                and raw[probe] == ord(":")
            )
            is_svg_payload = False
            if is_key:
                key = _decoded_json_key(raw, index, end)
                keys = stack[-1]["keys"]
                if key in keys:
                    raise _ProtocolViolation
                keys.add(key)
                stack[-1]["last_key"] = key
                stack[-1]["last_key_raw"] = raw[index:end]
            elif (
                len(stack) == 1
                and stack[-1]["kind"] == ord("{")
                and stack[-1]["last_key"] == "svg_b64"
                and stack[-1]["last_key_raw"] == b'"svg_b64"'
                and last_significant == ord(":")
                and root_ok_true
            ):
                encoded = raw[index + 1 : end - 1]
                if (
                    len(encoded) > _MAX_RENDERER_SVG_B64_BYTES
                    or _CANONICAL_BASE64_BYTES.fullmatch(encoded) is None
                ):
                    raise _ProtocolViolation
                is_svg_payload = True
            if not is_svg_payload:
                decoded_string_code_points += decoded_length
                if decoded_string_code_points > _MAX_RENDERER_DECODED_STRING_CODE_POINTS:
                    raise _ProtocolViolation
            add_token()
            last_significant = ord('"')
            index = end
            continue
        if current == ord("-") or ord("0") <= current <= ord("9"):
            end = index + 1
            while end < len(raw) and raw[end] in b"0123456789eE+-.":
                end += 1
            if end - index > _MAX_RENDERER_NUMERIC_LEXEME_BYTES:
                raise _ProtocolViolation
            add_token()
            last_significant = raw[end - 1]
            index = end
            continue
        literal = None
        for candidate in (b"true", b"false", b"null"):
            if raw.startswith(candidate, index):
                literal = candidate
                break
        if literal is not None:
            if (
                len(stack) == 1
                and stack[-1]["kind"] == ord("{")
                and stack[-1]["last_key"] == "ok"
                and last_significant == ord(":")
            ):
                root_ok_true = literal == b"true"
            add_token()
            last_significant = literal[-1]
            index += len(literal)
            continue
        if current in (ord(":"), ord(",")):
            last_significant = current
            index += 1
            continue
        raise _ProtocolViolation
    if stack or not root_seen:
        raise _ProtocolViolation


def _parse_response(raw: bytes, schema_name: str) -> dict[str, Any]:
    if type(raw) is not bytes or not 1 <= len(raw) <= MAX_RENDERER_STDOUT_BYTES:
        raise _ProtocolViolation
    if not raw.endswith(b"\n") or raw.endswith(b"\r\n") or b"\n" in raw[:-1]:
        raise _ProtocolViolation
    payload = raw[:-1]
    _preflight_renderer_json(payload)
    try:
        text = payload.decode("ascii")
        value = json.loads(
            text,
            object_pairs_hook=_closed_object,
            parse_constant=_reject_constant,
        )
    except (
        _ProtocolViolation,
        UnicodeDecodeError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ):
        raise _ProtocolViolation from None
    if not isinstance(value, dict):
        raise _ProtocolViolation
    _schema_valid(value, schema_name)
    if _serialize_closed_response(value) != raw:
        raise _ProtocolViolation
    return value


def _decode_renderer_response_impl(
    raw: bytes, expected_runtime: RendererRuntimeBinding
) -> tuple[bytes | None, tuple[str, str] | None]:
    if not isinstance(expected_runtime, RendererRuntimeBinding):
        raise _ProtocolViolation
    profile = expected_runtime.render_profile_id
    if profile == "ranking-svg-ja-jp-node24-echarts6.v1":
        schema_name = "renderer-response.schema.json"
    elif profile == "matrix-svg-ja-jp-node24-echarts6.v1":
        schema_name = "matrix-renderer-response.schema.json"
    elif profile == "categorical-svg-ja-jp-node24-echarts6.v1":
        schema_name = "categorical-renderer-response.schema.json"
    elif profile == "points-svg-ja-jp-node24-echarts6.v1":
        schema_name = "points-renderer-response.schema.json"
    elif profile == "advanced-svg-ja-jp-node24-echarts6.v1":
        schema_name = "advanced-renderer-response.schema.json"
    else:
        raise _ProtocolViolation
    value = _parse_response(raw, schema_name)
    if value["runtime"] != _runtime_object(expected_runtime):
        raise _ProtocolViolation
    if value["ok"] is True:
        svg = strict_b64decode(value["svg_b64"], MAX_RENDERER_SVG_BYTES)
        return bytes(svg), None
    error = value["error"]
    code = error["code"]
    message = error["message"]
    if _FAILURE_PAIRS.get(code) != message:
        raise _ProtocolViolation
    return None, (code, message)


def decode_renderer_response(raw: bytes, expected_runtime: RendererRuntimeBinding) -> bytes:
    svg: bytes | None = None
    declared: tuple[str, str] | None = None
    failed = False
    try:
        svg, declared = _decode_renderer_response_impl(raw, expected_runtime)
    except (
        _ProtocolViolation,
        CanonicalJsonError,
        RendererProtocolError,
        OSError,
        TypeError,
        ValueError,
        OverflowError,
        RecursionError,
    ):
        failed = True
    if failed:
        raise RendererProtocolError() from None
    if declared is not None:
        raise _validated_declared_error(*declared) from None
    if svg is None:
        raise RendererProtocolError() from None
    return svg
