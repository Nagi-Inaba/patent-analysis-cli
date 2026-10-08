"""Explicit, bounded representative selection over original scalar CSV fields.

Family identifiers are opaque; they are never tokenized, inferred, or merged.
Dates do not go through the year-only normalization used by analytical roles.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import date

from patent_analysis.analysis_budgets import MAX_ROWS
from patent_analysis.column_resolution import trim_ecmascript_whitespace
from patent_analysis.normalization.pipeline import NormalizedRow

_ISO_DATE = re.compile(r"[0-9]{4}([-/])[0-9]{2}\1[0-9]{2}\Z")


@dataclass(frozen=True, slots=True)
class FamilySelectionReceipt:
    family_role: str
    date_role: str | None
    matched_rows: int
    representative_rows: int
    collapsed_rows: int
    unidentified_rows: int

    def to_dict(self) -> dict[str, object]:
        return {"algorithm_version": "1.0.0", "mode": "earliest", **asdict(self)}


def _date_key(raw: str, source_ordinal: int) -> tuple[bool, int, int]:
    value = trim_ecmascript_whitespace(raw)
    if _ISO_DATE.fullmatch(value):
        try:
            return False, date.fromisoformat(value.replace("/", "-")).toordinal(), source_ordinal
        except ValueError:
            pass
    # Invalid or missing dates are incomparable; use source order for those pairs.
    return True, 0, source_ordinal


def select_family_population(
    rows: tuple[NormalizedRow, ...],
    *,
    family_column: int,
    date_column: int | None = None,
) -> tuple[NormalizedRow, ...]:
    """Select within an already filtered population, preserving first-seen slots.

    Blank identifiers retain their individual rows. Compare calendar dates only
    when both are valid; equal/invalid dates use source ordinal. With no date column,
    the lowest source ordinal wins. Return existing rows, never composite rows.
    """
    if not isinstance(rows, tuple) or len(rows) > MAX_ROWS:
        raise ValueError("family selection exceeds the row limit")
    columns = (family_column,) if date_column is None else (family_column, date_column)
    if any(type(column) is not int or column < 0 for column in columns):
        raise ValueError("family selection columns are invalid")
    representatives: list[NormalizedRow] = []
    by_family: dict[str, tuple[int, tuple[bool, int, int]]] = {}
    for row in rows:
        if not isinstance(row, NormalizedRow) or any(
            column >= len(row.source_fields) for column in columns
        ):
            raise ValueError("family selection columns are unavailable")
        family = trim_ecmascript_whitespace(row.source_fields[family_column])
        if not family:
            representatives.append(row)
            continue
        key = _date_key(
            "" if date_column is None else row.source_fields[date_column],
            row.source_ordinal,
        )
        previous = by_family.get(family)
        if previous is None:
            by_family[family] = len(representatives), key
            representatives.append(row)
        elif (
            key < previous[1]
            if not key[0] and not previous[1][0]
            else key[2] < previous[1][2]
        ):
            slot = previous[0]
            representatives[slot] = row
            by_family[family] = slot, key
    return tuple(representatives)
