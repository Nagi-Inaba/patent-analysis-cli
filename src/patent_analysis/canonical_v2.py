"""Strict-input RFC 8785 canonical JSON for v2 analysis contracts."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from typing import Any, NoReturn

MAX_SAFE_INTEGER = (2**53) - 1
_SURROGATES = re.compile("[\ud800-\udfff]")


class CanonicalizationError(ValueError):
    """Raised when input cannot be represented by the v2 JCS subset."""


def _fail(message: str) -> NoReturn:
    raise CanonicalizationError(message) from None


def _normalize_surrogates(value: str) -> str:
    if _SURROGATES.search(value) is None:
        return value
    output: list[str] = []
    index = 0
    while index < len(value):
        code_point = ord(value[index])
        if 0xD800 <= code_point <= 0xDBFF:
            if index + 1 >= len(value):
                _fail("lone surrogate is not permitted")
            low = ord(value[index + 1])
            if not 0xDC00 <= low <= 0xDFFF:
                _fail("lone surrogate is not permitted")
            scalar = 0x10000 + ((code_point - 0xD800) << 10) + (low - 0xDC00)
            output.append(chr(scalar))
            index += 2
            continue
        if 0xDC00 <= code_point <= 0xDFFF:
            _fail("lone surrogate is not permitted")
        output.append(value[index])
        index += 1
    return "".join(output)


def _parse_integer(token: str) -> int:
    if token == "-0":
        _fail("negative zero is not permitted")
    value = int(token)
    if abs(value) > MAX_SAFE_INTEGER:
        _fail("integer exceeds the safe integer range")
    return value


def _parse_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        _fail("non-finite numbers are not permitted")
    if value == 0.0:
        if token.startswith("-"):
            _fail("negative zero is not permitted")
        return value
    try:
        decimal_value = Decimal(token)
        is_integral_lexeme = decimal_value == decimal_value.to_integral_value()
    except InvalidOperation:
        _fail("number exponent is not supported")
    if is_integral_lexeme and abs(decimal_value) > MAX_SAFE_INTEGER:
        _fail("integer exceeds the safe integer range")
    if value.is_integer() and abs(value) > MAX_SAFE_INTEGER:
        _fail("integer exceeds the safe integer range")
    return value


def _parse_constant(_token: str) -> NoReturn:
    _fail("non-finite numbers are not permitted")


def _object_from_pairs(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for raw_key, value in pairs:
        key = _normalize_surrogates(raw_key)
        if key in output:
            _fail("duplicate key is not permitted")
        output[key] = value
    return output


def _normalize_parsed_strings(value: Any) -> Any:
    if isinstance(value, str):
        return _normalize_surrogates(value)
    if isinstance(value, list):
        return [_normalize_parsed_strings(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize_parsed_strings(item) for key, item in value.items()}
    return value


def parse_strict_json_bytes(raw: bytes) -> object:
    """Parse UTF-8 JSON while retaining duplicate-key and number-lexeme checks."""

    if type(raw) is not bytes:
        _fail("strict JSON input must be bytes")
    try:
        text = raw.decode("utf-8", errors="strict")
        parsed = json.loads(
            text,
            parse_int=_parse_integer,
            parse_float=_parse_float,
            parse_constant=_parse_constant,
            object_pairs_hook=_object_from_pairs,
        )
        return _normalize_parsed_strings(parsed)
    except CanonicalizationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        _fail("input is not strict UTF-8 JSON")


def _escape_string(value: str) -> bytes:
    # String escaping matches JCS; number serialization and UTF-16 key ordering remain
    # explicit below. Keep the existing surrogate-pair normalization/rejection policy.
    return json.dumps(_normalize_surrogates(value), ensure_ascii=False).encode("utf-8")


def _digits_and_exponent(value: float) -> tuple[str, int]:
    representation = repr(value).lower()
    if "e" in representation:
        significand, exponent_text = representation.split("e", 1)
        exponent = int(exponent_text)
    else:
        significand = representation
        exponent = 0
    if "." in significand:
        whole, fraction = significand.split(".", 1)
        digits = whole + fraction
        exponent -= len(fraction)
    else:
        digits = significand
    digits = digits.lstrip("0") or "0"
    while len(digits) > 1 and digits.endswith("0"):
        digits = digits[:-1]
        exponent += 1
    return digits, exponent


def _serialize_float(value: float) -> bytes:
    if not math.isfinite(value):
        _fail("non-finite numbers are not permitted")
    if value == 0.0:
        if math.copysign(1.0, value) < 0:
            _fail("negative zero is not permitted")
        return b"0"
    if value.is_integer() and abs(value) > MAX_SAFE_INTEGER:
        _fail("integer exceeds the safe integer range")

    sign = "-" if value < 0 else ""
    digits, exponent = _digits_and_exponent(abs(value))
    digit_count = len(digits)
    decimal_position = digit_count + exponent

    if digit_count <= decimal_position <= 21:
        body = digits + ("0" * (decimal_position - digit_count))
    elif 0 < decimal_position <= 21:
        body = digits[:decimal_position] + "." + digits[decimal_position:]
    elif -6 < decimal_position <= 0:
        body = "0." + ("0" * -decimal_position) + digits
    else:
        significand = digits[0]
        if digit_count > 1:
            significand += "." + digits[1:]
        scientific_exponent = decimal_position - 1
        exponent_sign = "+" if scientific_exponent >= 0 else "-"
        body = f"{significand}e{exponent_sign}{abs(scientific_exponent)}"
    return f"{sign}{body}".encode("ascii")


def _serialize(value: Any, active_containers: set[int]) -> bytes:
    if value is None:
        return b"null"
    if value is True:
        return b"true"
    if value is False:
        return b"false"
    if type(value) is int:
        if abs(value) > MAX_SAFE_INTEGER:
            _fail("integer exceeds the safe integer range")
        return str(value).encode("ascii")
    if type(value) is float:
        return _serialize_float(value)
    if type(value) is str:
        return _escape_string(value)
    if type(value) not in (list, dict):
        _fail("value is not a JSON value")

    identity = id(value)
    if identity in active_containers:
        _fail("cyclic JSON values are not permitted")
    active_containers.add(identity)
    try:
        if type(value) is list:
            return b"[" + b",".join(_serialize(item, active_containers) for item in value) + b"]"

        keys = list(value)
        if not all(type(key) is str for key in keys):
            _fail("JSON object keys must be strings")
        normalized_keys: list[tuple[str, str]] = []
        seen: set[str] = set()
        for raw_key in keys:
            key = _normalize_surrogates(raw_key)
            if key in seen:
                _fail("duplicate key is not permitted")
            seen.add(key)
            normalized_keys.append((key, raw_key))
        normalized_keys.sort(key=lambda pair: pair[0].encode("utf-16-be"))
        members = (
            _escape_string(key) + b":" + _serialize(value[raw_key], active_containers)
            for key, raw_key in normalized_keys
        )
        return b"{" + b",".join(members) + b"}"
    finally:
        active_containers.remove(identity)


def canonical_json_bytes(value: object) -> bytes:
    """Return RFC 8785 canonical UTF-8 bytes for the strict supported subset."""

    try:
        return _serialize(value, set())
    except CanonicalizationError:
        raise
    except (RecursionError, UnicodeError, ValueError, OverflowError):
        _fail("value cannot be canonicalized")


def canonical_sha256(value: object) -> str:
    """Return the lowercase SHA-256 digest of v2 canonical JSON bytes."""

    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()
