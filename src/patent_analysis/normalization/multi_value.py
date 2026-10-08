"""Source-independent patent multi-value cell semantics."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

MAX_NORMALIZED_VALUES_PER_CELL = 1000
_GENERAL_SPLIT = re.compile(r"[|;；、，\r\n]+")
_CLASSIFICATION_SPLIT = re.compile(r"[|,;；、，\r\n]+")
_CLASSIFICATION_ROLES = frozenset(
    {
        "classification",
        "ipc",
        "main_ipc",
        "cpc",
        "fi",
        "f_term",
        "fterm",
        "ftm",
        "pcl",
        "ipc分類",
        "cpc分類",
        "fi分類",
        "fターム",
        "特許分類",
        "分類コード",
    }
)


def stable_dedupe(
    values: Iterable[str],
    *,
    keys: Iterable[str] | None = None,
) -> tuple[str, ...]:
    """Return non-empty values in first-seen order using optional comparison keys."""

    pairs = (
        ((value, value) for value in values)
        if keys is None
        else zip(values, keys, strict=True)
    )
    output: list[str] = []
    seen: set[str] = set()
    for value, key in pairs:
        if not value or key in seen:
            continue
        seen.add(key)
        output.append(value)
    return tuple(output)


def _role_key(role: str) -> str:
    normalized = unicodedata.normalize("NFKC", role).strip().casefold()
    return re.sub(r"[\s-]+", "_", normalized)


def is_classification_role(role: str) -> bool:
    """Return whether a semantic role uses classification comma splitting."""

    if not isinstance(role, str) or not role.strip():
        return False
    return _role_key(role) in _CLASSIFICATION_ROLES


def split_patent_values(value: str, *, role: str) -> tuple[str, ...]:
    """Split one patent cell with role-aware, stable-deduplicated semantics."""

    if not isinstance(value, str) or not isinstance(role, str) or not role.strip():
        raise ValueError("patent multi-value input is invalid")
    text = value.strip()
    if not text or text == "(空白)":
        return ()
    pattern = _CLASSIFICATION_SPLIT if is_classification_role(role) else _GENERAL_SPLIT
    values = tuple(part.strip() for part in pattern.split(text) if part.strip())
    if len(values) > MAX_NORMALIZED_VALUES_PER_CELL:
        raise ValueError("normalized value limit exceeded")
    return stable_dedupe(values)


def split_multi_value(
    value: str,
    *,
    classification: bool = False,
) -> tuple[str, ...]:
    """Compatibility wrapper for internal callers using an explicit classification flag."""

    return split_patent_values(
        value,
        role="classification" if classification else "value",
    )
