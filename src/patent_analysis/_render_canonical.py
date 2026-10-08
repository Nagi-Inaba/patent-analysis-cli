from __future__ import annotations

import base64
import binascii
import hashlib
import json
import math
from typing import Any, NoReturn


class CanonicalJsonError(ValueError):
    """Raised when input cannot be represented by the canonical JSON contract."""


def _raise_invalid_json_constant(_value: str) -> NoReturn:
    raise CanonicalJsonError("canonical JSON contains an invalid number")


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CanonicalJsonError("canonical JSON contains a duplicate key")
        result[key] = value
    return result


def _validate_string(value: str) -> None:
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise CanonicalJsonError("canonical JSON contains a lone surrogate")


def _validate_json_value(value: Any, active_containers: set[int]) -> None:
    if isinstance(value, str):
        _validate_string(value)
        return
    if value is None or isinstance(value, (bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value) or (value == 0.0 and math.copysign(1.0, value) < 0):
            raise CanonicalJsonError("canonical JSON contains an ambiguous number")
        return
    if isinstance(value, dict):
        container_id = id(value)
        if container_id in active_containers:
            raise CanonicalJsonError("canonical JSON contains a cycle")
        active_containers.add(container_id)
        try:
            for key, item in value.items():
                if not isinstance(key, str):
                    raise CanonicalJsonError("canonical JSON object keys must be strings")
                _validate_string(key)
                _validate_json_value(item, active_containers)
        finally:
            active_containers.remove(container_id)
        return
    if isinstance(value, (list, tuple)):
        container_id = id(value)
        if container_id in active_containers:
            raise CanonicalJsonError("canonical JSON contains a cycle")
        active_containers.add(container_id)
        try:
            for item in value:
                _validate_json_value(item, active_containers)
        finally:
            active_containers.remove(container_id)
        return
    raise CanonicalJsonError("value is not canonical JSON compatible")


def canonical_json_bytes(value: Any) -> bytes:
    _validate_json_value(value, set())
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise CanonicalJsonError("value is not canonical JSON compatible") from error


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_sha256(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def parse_canonical_json_bytes(raw: bytes, max_bytes: int) -> dict[str, Any]:
    if not isinstance(raw, bytes) or len(raw) > max_bytes:
        raise CanonicalJsonError("canonical JSON bytes are invalid or too large")
    try:
        text = raw.decode("utf-8")
        parsed = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_raise_invalid_json_constant,
        )
    except CanonicalJsonError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as error:
        raise CanonicalJsonError("canonical JSON bytes are invalid") from error
    if not isinstance(parsed, dict):
        raise CanonicalJsonError("canonical JSON must contain a top-level object")
    if canonical_json_bytes(parsed) != raw:
        raise CanonicalJsonError("JSON bytes are not canonical")
    return parsed


def strict_b64encode(raw: bytes) -> str:
    try:
        return base64.b64encode(raw).decode("ascii")
    except (TypeError, UnicodeDecodeError) as error:
        raise CanonicalJsonError("base64 input is invalid") from error


def strict_b64decode(text: str, max_decoded_bytes: int) -> bytes:
    if not isinstance(text, str):
        raise CanonicalJsonError("base64 input is invalid")
    try:
        decoded = base64.b64decode(text, validate=True)
    except (binascii.Error, ValueError) as error:
        raise CanonicalJsonError("base64 input is invalid") from error
    if len(decoded) > max_decoded_bytes or strict_b64encode(decoded) != text:
        raise CanonicalJsonError("base64 input is invalid or too large")
    return decoded
