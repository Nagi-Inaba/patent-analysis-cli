from __future__ import annotations

import pytest

import patent_analysis
from patent_analysis._render_canonical import (
    CanonicalJsonError,
    canonical_json_bytes,
    canonical_sha256,
    parse_canonical_json_bytes,
    sha256_bytes,
    strict_b64decode,
    strict_b64encode,
)
from patent_analysis._render_text import (
    GRAPHEME_RUNTIME_ID,
    RenderTextError,
    grapheme_count,
    graphemes,
    truncate_axis_label,
    truncate_title_dimension,
    validate_safe_text,
)
from patent_analysis._version import PACKAGE_VERSION


def test_package_version_has_one_authoritative_value() -> None:
    assert PACKAGE_VERSION == "0.2.0"
    assert patent_analysis.__version__ == PACKAGE_VERSION


def test_canonical_json_bytes_are_exact_utf8_without_lf() -> None:
    assert canonical_json_bytes({"b": "日本", "a": 1}) == (
        '{"a":1,"b":"日本"}'.encode()
    )


def test_canonical_hashes_are_lowercase_sha256_of_exact_bytes() -> None:
    assert sha256_bytes(b"model") == (
        "9372c470eeadd5ecd9c3c74c2b3cb633f8e2f2fad799250a0f70d652b6b825e4"
    )
    assert canonical_sha256({"a": 1}) == (
        "015abd7f5cc57a2dd94b7590f04ad8084273905ee33ec5cebeae62276a97f862"
    )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), -0.0])
def test_canonical_json_rejects_ambiguous_numbers(value: float) -> None:
    with pytest.raises(CanonicalJsonError):
        canonical_json_bytes({"value": value})


def test_canonical_json_rejects_cycles_nonstring_keys_and_lone_surrogates() -> None:
    cyclic: list[object] = []
    cyclic.append(cyclic)

    for value in (cyclic, {1: "value"}, {"value": "\ud800"}):
        with pytest.raises(CanonicalJsonError):
            canonical_json_bytes(value)


def test_canonical_parser_rejects_duplicate_keys_and_noncanonical_bytes() -> None:
    with pytest.raises(CanonicalJsonError):
        parse_canonical_json_bytes(b'{"a":1,"a":2}', max_bytes=1024)
    with pytest.raises(CanonicalJsonError):
        parse_canonical_json_bytes(b'{"b":2, "a":1}', max_bytes=1024)


def test_canonical_parser_rejects_invalid_utf8_oversize_and_nonobject() -> None:
    with pytest.raises(CanonicalJsonError):
        parse_canonical_json_bytes(b"\xff", max_bytes=1024)
    with pytest.raises(CanonicalJsonError):
        parse_canonical_json_bytes(b'{"a":1}', max_bytes=6)
    with pytest.raises(CanonicalJsonError):
        parse_canonical_json_bytes(b"[]", max_bytes=1024)


def test_canonical_parser_returns_exact_object() -> None:
    raw = '{"a":1,"b":"日本"}'.encode()
    assert parse_canonical_json_bytes(raw, max_bytes=1024) == {
        "a": 1,
        "b": "日本",
    }


def test_strict_base64_round_trip_rejects_whitespace() -> None:
    encoded = strict_b64encode(b"model")
    assert strict_b64decode(encoded, max_decoded_bytes=16) == b"model"
    with pytest.raises(CanonicalJsonError):
        strict_b64decode(encoded + "\n", max_decoded_bytes=16)
    with pytest.raises(CanonicalJsonError):
        strict_b64decode(encoded, max_decoded_bytes=4)


def test_strict_base64_rejects_noncanonical_padding() -> None:
    with pytest.raises(CanonicalJsonError):
        strict_b64decode("bW9kZWw", max_decoded_bytes=16)


def test_grapheme_runtime_and_axis_truncation_are_fixed() -> None:
    assert GRAPHEME_RUNTIME_ID == "regex-2026.4.4-unicode16.0.0"
    assert graphemes("👩‍🔬e\u0301") == ["👩‍🔬", "e\u0301"]
    assert grapheme_count("👩‍🔬e\u0301") == 2
    assert truncate_axis_label("あ" * 28) == "あ" * 28
    assert truncate_axis_label("あ" * 29) == "あ" * 27 + "…"


def test_title_truncation_preserves_256_graphemes_and_shortens_overflow() -> None:
    assert truncate_title_dimension("あ" * 250) == "あ" * 250 + "のランキング"
    assert truncate_title_dimension("あ" * 251) == "あ" * 249 + "…のランキング"


def test_safe_display_text_is_returned_unchanged() -> None:
    assert validate_safe_text("👩‍🔬e\u0301 日本") == "👩‍🔬e\u0301 日本"
    assert validate_safe_text("العربية עברית 👩‍🔬") == "العربية עברית 👩‍🔬"


@pytest.mark.parametrize(
    "value",
    [
        "a\n",
        "a\x7f",
        "a\u061c",
        "a\u200e",
        "a\u200f",
        "a\u202e",
        "a\u2066",
        "a\ud800",
        "a\ufdd0",
        "a\ufffe",
        "a\U0001ffff",
    ],
)
def test_display_text_rejects_forbidden_unicode(value: str) -> None:
    with pytest.raises(RenderTextError):
        validate_safe_text(value)
