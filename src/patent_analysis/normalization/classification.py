"""Generic patent-classification normalization and hierarchy projection."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from typing import Literal

from patent_analysis.normalization.multi_value import stable_dedupe

ClassificationLevel = Literal["full", "class", "subclass", "main_group", "subgroup"]
CLASSIFICATION_LEVELS = frozenset(
    {"full", "class", "subclass", "main_group", "subgroup"}
)
_SYMBOL_PATTERN = re.compile(
    r"^(?P<section>[A-HY])\s*(?P<class>\d{2})\s*(?P<subclass>[A-Z])"
    r"(?:[\s-]*(?P<group>\d{1,4})"
    r"(?:\s*/\s*(?P<subgroup>\d{1,6}))?)?"
    r"(?P<tail>.*)$",
    re.IGNORECASE,
)
_DASHES = re.compile(r"[－ー―–—]")


def _normalized_text(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).replace("\u00a0", " ")
    text = _DASHES.sub("-", text).strip().upper()
    return re.sub(r"\s+", " ", text)


def _attach_tail(base: str, tail: str) -> str:
    if not tail:
        return base
    return f"{base}{tail}" if tail.startswith("@") else f"{base} {tail}"


def format_classification(value: str, level: str = "full") -> str:
    """Project one IPC/FI-like symbol to a closed canonical hierarchy level."""

    if level not in CLASSIFICATION_LEVELS:
        raise ValueError("unsupported classification level")
    if not isinstance(value, str):
        raise ValueError("classification value is invalid")
    text = _normalized_text(value)
    if not text:
        return ""
    match = _SYMBOL_PATTERN.fullmatch(text)
    if match is None:
        return text

    class_code = f"{match.group('section').upper()}{match.group('class')}"
    subclass_code = f"{class_code}{match.group('subclass').upper()}"
    group = match.group("group")
    subgroup = match.group("subgroup")
    tail = (match.group("tail") or "").strip()

    if level == "class":
        return class_code
    if level == "subclass":
        return subclass_code
    if group is None:
        return _attach_tail(subclass_code, tail) if level == "full" else subclass_code

    main_group = f"{subclass_code} {int(group)}/00"
    subgroup_code = (
        main_group
        if subgroup is None
        else f"{subclass_code} {int(group)}/{subgroup}"
    )
    if level == "main_group":
        return main_group
    if level == "subgroup":
        return subgroup_code
    return _attach_tail(subgroup_code, tail)


def derive_classification_values(
    values: Iterable[str],
    *,
    level: str,
) -> tuple[str, ...]:
    """Project and stable-deduplicate a classification value sequence."""

    if level not in CLASSIFICATION_LEVELS:
        raise ValueError("unsupported classification level")
    return stable_dedupe(format_classification(value, level) for value in values)
