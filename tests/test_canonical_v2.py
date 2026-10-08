from __future__ import annotations

import json

import pytest

from patent_analysis.canonical_v2 import (
    CanonicalizationError,
    canonical_json_bytes,
    canonical_sha256,
    parse_strict_json_bytes,
)


def test_v2_canonical_orders_utf16_keys_and_normalizes_number_values() -> None:
    assert canonical_json_bytes({"b": 1.0, "a": 1}) == b'{"a":1,"b":1}'


def test_v2_canonical_uses_utf16_order_for_bmp_and_surrogate_pair_keys() -> None:
    value = {"\ue000": 1, "\U00010000": 2}
    assert canonical_json_bytes(value) == b'{"\xf0\x90\x80\x80":2,"\xee\x80\x80":1}'


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (333333333.33333329, b"333333333.3333333"),
        (4.50, b"4.5"),
        (2e-3, b"0.002"),
        (1e-27, b"1e-27"),
        (1.2345e-30, b"1.2345e-30"),
        (1e-6, b"0.000001"),
        (1e-7, b"1e-7"),
        (5e-324, b"5e-324"),
    ],
)
def test_v2_canonical_matches_jcs_number_serialization_vectors(
    value: float, expected: bytes
) -> None:
    assert canonical_json_bytes(value) == expected


def test_v2_canonical_matches_jcs_string_escaping_vector() -> None:
    value = "\u20ac$\u000f\nA'B\"\\\"/"
    assert canonical_json_bytes(value) == "\"€$\\u000f\\nA'B\\\"\\\\\\\"/\"".encode()


def test_canonical_string_digest_preserves_all_unicode_scalars():
    # Golden produced by the original serializer, including every control/escape boundary.
    value = "".join(chr(i) for i in range(0x110000) if not 0xD800 <= i <= 0xDFFF)
    assert canonical_sha256(value) == (
        "57e981f64bd97f179471154328d2c7c9202ce92fa5503814073aaff388c877f2")


@pytest.mark.parametrize("value", [-0.0, float("nan"), float("inf"), float("-inf")])
def test_v2_canonical_rejects_forbidden_numbers(value: float) -> None:
    with pytest.raises(CanonicalizationError):
        canonical_json_bytes({"value": value})


@pytest.mark.parametrize("value", [2**53, -(2**53)])
def test_v2_canonical_rejects_unsafe_integer_values(value: int) -> None:
    with pytest.raises(CanonicalizationError, match="safe integer"):
        canonical_json_bytes(value)


@pytest.mark.parametrize(
    "value",
    [
        9007199254740992.0,
        -9007199254740992.0,
        1e20,
        1e30,
        1.7976931348623157e308,
    ],
)
def test_v2_canonical_rejects_unsafe_integer_valued_floats(value: float) -> None:
    with pytest.raises(CanonicalizationError, match="safe integer"):
        canonical_json_bytes(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (9007199254740991.0, b"9007199254740991"),
        (-9007199254740991.0, b"-9007199254740991"),
    ],
)
def test_v2_canonical_accepts_safe_boundary_integer_valued_floats(
    value: float, expected: bytes
) -> None:
    assert canonical_json_bytes(value) == expected


def test_strict_parser_rejects_duplicate_keys_before_object_construction() -> None:
    with pytest.raises(CanonicalizationError, match="duplicate key"):
        parse_strict_json_bytes(b'{"analysis_id":"a","analysis_id":"b"}')


@pytest.mark.parametrize(
    "raw",
    [
        b'"\\ud800"',
        b'"\\udc00"',
        b'{"\\ud800":1}',
        b"NaN",
        b"Infinity",
        b"-Infinity",
        b"-0",
        b"-0.0",
        b"-0e10",
        b"9007199254740992",
        b"-9007199254740992",
        b"9007199254740992.0",
        b"-9007199254740992.0",
        b"9007199254740993.0",
        b"9007199254740992.1",
        b"9.007199254740992e15",
        b"1e30",
    ],
)
def test_strict_parser_rejects_invalid_jcs_subset_inputs(raw: bytes) -> None:
    with pytest.raises(CanonicalizationError):
        parse_strict_json_bytes(raw)


def test_strict_parser_accepts_a_valid_escaped_surrogate_pair() -> None:
    value = parse_strict_json_bytes(b'{"emoji":"\\ud83d\\ude00"}')
    assert value == {"emoji": "\U0001f600"}
    assert canonical_json_bytes(value) == '{"emoji":"😀"}'.encode()


@pytest.mark.parametrize(
    "raw",
    [b"9007199254740991.0", b"-9007199254740991.0", b"9.007199254740991e15"],
)
def test_strict_parser_accepts_safe_boundary_float_lexemes(raw: bytes) -> None:
    value = parse_strict_json_bytes(raw)
    assert canonical_json_bytes(value) in {b"9007199254740991", b"-9007199254740991"}


@pytest.mark.parametrize(
    "raw",
    [
        b"1e999999999999999999999999999999999999",
        b"-1e999999999999999999999999999999999999",
        b"-1e-999999999999999999999999999999999999",
    ],
)
def test_strict_parser_closes_extreme_exponent_errors(raw: bytes) -> None:
    with pytest.raises(CanonicalizationError):
        parse_strict_json_bytes(raw)


def test_strict_parser_returns_supported_zero_for_positive_extreme_underflow() -> None:
    value = parse_strict_json_bytes(b"1e-999999999999999999999999999999999999")
    assert value == 0.0
    assert canonical_json_bytes(value) == b"0"


def test_canonical_sha256_hashes_the_canonical_bytes() -> None:
    assert canonical_sha256({"b": 1.0, "a": 1}) == (
        "4dad51ac41eb73862fce375fae85ba13711fd19f1b26d8e4b1f9fa405c3d5adf"
    )


def test_value_only_canonicalizer_does_not_accept_non_json_containers() -> None:
    with pytest.raises(CanonicalizationError, match="JSON value"):
        canonical_json_bytes((1, 2))


def test_strict_parser_round_trips_canonical_json() -> None:
    raw = b'{"z":1.2345e-30,"a":[true,null,"text"]}'
    value = parse_strict_json_bytes(raw)
    assert json.loads(canonical_json_bytes(value)) == json.loads(raw)
