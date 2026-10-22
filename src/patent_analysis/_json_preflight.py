"""Bound JSON structure before materializing untrusted document objects."""

from __future__ import annotations

import json

_MAX_JSON_DEPTH = 64
_MAX_JSON_TOKENS = 250_000
_MAX_JSON_NUMERIC_LEXEME_BYTES = 128
_MAX_JSON_DECODED_STRING_CODE_POINTS = 2_000_000


class JsonPreflightError(ValueError):
    pass


def _scan_utf8_code_point(raw: bytes, index: int) -> int:
    first = raw[index]
    if 0xC2 <= first <= 0xDF:
        length = 2
        second_min, second_max = 0x80, 0xBF
    elif first == 0xE0:
        length = 3
        second_min, second_max = 0xA0, 0xBF
    elif 0xE1 <= first <= 0xEC or 0xEE <= first <= 0xEF:
        length = 3
        second_min, second_max = 0x80, 0xBF
    elif first == 0xED:
        length = 3
        second_min, second_max = 0x80, 0x9F
    elif first == 0xF0:
        length = 4
        second_min, second_max = 0x90, 0xBF
    elif 0xF1 <= first <= 0xF3:
        length = 4
        second_min, second_max = 0x80, 0xBF
    elif first == 0xF4:
        length = 4
        second_min, second_max = 0x80, 0x8F
    else:
        raise JsonPreflightError
    if index + length > len(raw) or not second_min <= raw[index + 1] <= second_max:
        raise JsonPreflightError
    if any(not 0x80 <= value <= 0xBF for value in raw[index + 2 : index + length]):
        raise JsonPreflightError
    return index + length


def _scan_input_json_string(raw: bytes, start: int) -> tuple[int, int]:
    index = start + 1
    decoded_code_points = 0
    while index < len(raw):
        current = raw[index]
        if current == 0x22:
            return index + 1, decoded_code_points
        if current < 0x20:
            raise JsonPreflightError
        if current >= 0x80:
            index = _scan_utf8_code_point(raw, index)
            decoded_code_points += 1
            continue
        if current != 0x5C:
            decoded_code_points += 1
            index += 1
            continue
        if index + 1 >= len(raw):
            raise JsonPreflightError
        escaped = raw[index + 1]
        if escaped in b'"\\/bfnrt':
            decoded_code_points += 1
            index += 2
            continue
        if escaped != ord("u") or index + 6 > len(raw):
            raise JsonPreflightError
        digits = raw[index + 2 : index + 6]
        if any(value not in b"0123456789abcdefABCDEF" for value in digits):
            raise JsonPreflightError
        code_unit = int(digits, 16)
        if code_unit == 0:
            raise JsonPreflightError
        if 0xD800 <= code_unit <= 0xDBFF:
            if index + 12 > len(raw) or raw[index + 6 : index + 8] != b"\\u":
                raise JsonPreflightError
            low_digits = raw[index + 8 : index + 12]
            if any(value not in b"0123456789abcdefABCDEF" for value in low_digits):
                raise JsonPreflightError
            low_unit = int(low_digits, 16)
            if not 0xDC00 <= low_unit <= 0xDFFF:
                raise JsonPreflightError
            decoded_code_points += 1
            index += 12
            continue
        if 0xDC00 <= code_unit <= 0xDFFF:
            raise JsonPreflightError
        decoded_code_points += 1
        index += 6
    raise JsonPreflightError


def _decode_input_key(raw: bytes, start: int, end: int) -> str:
    try:
        decoded = json.loads(raw[start:end].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        raise JsonPreflightError from None
    if not isinstance(decoded, str):
        raise JsonPreflightError
    return decoded


def preflight_json_bytes(raw: bytes) -> None:
    if type(raw) is not bytes or not raw or b"\x00" in raw:
        raise JsonPreflightError

    stack: list[dict[str, object]] = []
    root_seen = False
    root_closed = False
    decoded_string_code_points = 0
    token_count = 0
    index = 0

    def add_token() -> None:
        nonlocal token_count
        token_count += 1
        if token_count > _MAX_JSON_TOKENS:
            raise JsonPreflightError

    while index < len(raw):
        current = raw[index]
        if current in b" \t\r\n":
            index += 1
            continue
        if root_closed:
            raise JsonPreflightError
        if current in (ord("{"), ord("[")):
            if not stack:
                if root_seen or current != ord("{"):
                    raise JsonPreflightError
                root_seen = True
            stack.append(
                {
                    "kind": current,
                    "keys": set() if current == ord("{") else None,
                }
            )
            if len(stack) > _MAX_JSON_DEPTH:
                raise JsonPreflightError
            add_token()
            index += 1
            continue
        if current in (ord("}"), ord("]")):
            expected = ord("{") if current == ord("}") else ord("[")
            if not stack or stack[-1]["kind"] != expected:
                raise JsonPreflightError
            stack.pop()
            if not stack:
                root_closed = True
            index += 1
            continue
        if current == ord('"'):
            end, decoded_length = _scan_input_json_string(raw, index)
            decoded_string_code_points += decoded_length
            if decoded_string_code_points > _MAX_JSON_DECODED_STRING_CODE_POINTS:
                raise JsonPreflightError
            probe = end
            while probe < len(raw) and raw[probe] in b" \t\r\n":
                probe += 1
            if (
                stack
                and stack[-1]["kind"] == ord("{")
                and probe < len(raw)
                and raw[probe] == ord(":")
            ):
                key = _decode_input_key(raw, index, end)
                keys = stack[-1]["keys"]
                if not isinstance(keys, set) or key in keys:
                    raise JsonPreflightError
                keys.add(key)
            add_token()
            index = end
            continue
        if current == ord("-") or ord("0") <= current <= ord("9"):
            end = index + 1
            while end < len(raw) and raw[end] in b"0123456789eE+-.":
                end += 1
            if end - index > _MAX_JSON_NUMERIC_LEXEME_BYTES:
                raise JsonPreflightError
            add_token()
            index = end
            continue
        literal = next(
            (
                candidate
                for candidate in (b"true", b"false", b"null")
                if raw.startswith(candidate, index)
            ),
            None,
        )
        if literal is not None:
            add_token()
            index += len(literal)
            continue
        if current in (ord(":"), ord(",")):
            index += 1
            continue
        raise JsonPreflightError
    if stack or not root_seen or not root_closed:
        raise JsonPreflightError
