"""Dictionary-free conservative applicant-name normalization."""

from __future__ import annotations

import re
import unicodedata

_JAPANESE_LEGAL_MARKER = (
    r"(?:株式会社|\(株\)|有限会社|\(有\)|合同会社|\(同\)|合資会社|合名会社)"
)
_ENGLISH_LEGAL_PREFIX_MARKER = (
    r"(?:CO\.?\s*,?\s*LTD\.?|CORPORATION|CORP\.?|INCORPORATED|"
    r"INC\.?|LIMITED|LTD\.?|LLC|GMBH|K\.?\s*K\.?|KK)"
)
_ENGLISH_LEGAL_SUFFIX_MARKER = rf"(?:{_ENGLISH_LEGAL_PREFIX_MARKER}|SE)"
_PREFIX_PATTERNS = (
    re.compile(rf"^\s*{_JAPANESE_LEGAL_MARKER}\s*", re.IGNORECASE),
    re.compile(
        rf"^[\s,.;:()]*{_ENGLISH_LEGAL_PREFIX_MARKER}(?:[\s,.;:()]+|$)",
        re.IGNORECASE,
    ),
)
_SUFFIX_PATTERNS = (
    re.compile(rf"\s*{_JAPANESE_LEGAL_MARKER}\s*$", re.IGNORECASE),
    re.compile(
        rf"(?:^|[\s,.;:()]+){_ENGLISH_LEGAL_SUFFIX_MARKER}[\s,.;:()]*$",
        re.IGNORECASE,
    ),
)
_EDGE_SYMBOLS = re.compile(r"^[\s,.;:・、。]+|[\s,.;:・、。]+$")
_MULTI_SPACE = re.compile(r"\s+")


def _clean(value: str) -> str:
    text = unicodedata.normalize("NFKC", value)
    text = _MULTI_SPACE.sub(" ", text)
    return _EDGE_SYMBOLS.sub("", text).strip()


def normalize_applicant(value: str) -> str:
    """Remove only closed legal-form markers while preserving the source identity."""

    if not isinstance(value, str):
        raise ValueError("applicant value is invalid")
    original = _clean(value)
    if not original:
        return ""
    current = original
    while True:
        before = current
        for pattern in _PREFIX_PATTERNS:
            current = pattern.sub("", current)
        for pattern in _SUFFIX_PATTERNS:
            current = pattern.sub("", current)
        current = _clean(current)
        if current == before:
            break
    return current or original


def applicant_key(value: str) -> str:
    """Return a locale-independent comparison key for a normalized applicant."""

    return normalize_applicant(value).casefold()
