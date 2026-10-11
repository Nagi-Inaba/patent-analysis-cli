from __future__ import annotations

import regex


class RenderTextError(ValueError):
    """Raised when text is unsafe or the fixed grapheme runtime is unavailable."""


REGEX_VERSION = "2026.4.4"
UNICODE_VERSION = "16.0.0"
GRAPHEME_RUNTIME_ID = f"regex-{REGEX_VERSION}-unicode{UNICODE_VERSION}"
TITLE_SUFFIX = "のランキング"

if (
    regex.__version__ != REGEX_VERSION
    or regex._regex_core.unicodedata.unidata_version != UNICODE_VERSION
):
    raise RenderTextError("render text runtime is incompatible")


def _is_forbidden_code_point(code_point: int) -> bool:
    return (
        code_point <= 0x1F
        or 0x7F <= code_point <= 0x9F
        or 0xD800 <= code_point <= 0xDFFF
        or 0xFDD0 <= code_point <= 0xFDEF
        or code_point & 0xFFFF in (0xFFFE, 0xFFFF)
        or code_point == 0x061C
        or 0x200E <= code_point <= 0x200F
        or 0x202A <= code_point <= 0x202E
        or 0x2066 <= code_point <= 0x2069
    )


def validate_safe_text(value: str) -> str:
    if not isinstance(value, str) or any(_is_forbidden_code_point(ord(char)) for char in value):
        raise RenderTextError("render text contains a forbidden character")
    return value


def graphemes(value: str) -> list[str]:
    if not isinstance(value, str):
        raise RenderTextError("render text must be a string")
    return regex.findall(r"\X", value)


def grapheme_count(value: str) -> int:
    return len(graphemes(value))


def truncate_axis_label(value: str) -> str:
    clusters = graphemes(value)
    if len(clusters) <= 28:
        return value
    return "".join(clusters[:27]) + "…"


def truncate_title_dimension(value: str) -> str:
    clusters = graphemes(value)
    if len(clusters) + grapheme_count(TITLE_SUFFIX) <= 256:
        return value + TITLE_SUFFIX
    return "".join(clusters[:249]) + "…" + TITLE_SUFFIX
