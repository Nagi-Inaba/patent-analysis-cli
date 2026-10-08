"""Shared deterministic aggregation primitives for registered v2 analyses."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from patent_analysis.normalization import NormalizedRow

MEASURE_MODES = frozenset({"count", "sum", "average", "max", "min"})


def stable_unique(values: Iterable[object]) -> tuple[str, ...]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        output.append(text)
    return tuple(output)


def unique_aggregate_label(base: str, source_labels: Iterable[str]) -> str:
    """Name a generated bucket without reusing any source label."""

    used = set(source_labels)
    label = base
    suffix = 2
    while label in used:
        label = f"{base} [{suffix}]"
        suffix += 1
    return label


def canonical_year(values: Iterable[object]) -> int | None:
    """Return the first already-normalized Gregorian year in the closed range."""

    for value in stable_unique(values):
        if len(value) == 4 and value.isascii() and value.isdigit():
            year = int(value)
            if 1800 <= year <= 2199:
                return year
    return None


def row_values(row: NormalizedRow, role: str) -> tuple[str, ...]:
    if not isinstance(row, NormalizedRow):
        raise ValueError("analysis row must be canonically normalized")
    if not isinstance(role, str) or not role:
        raise ValueError("analysis role is invalid")
    return stable_unique(row.values(role))


def parse_number(value: str) -> float | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().replace(",", "")
    if not normalized:
        return None
    try:
        parsed = float(normalized)
    except ValueError:
        return None
    if parsed != parsed or parsed in {float("inf"), float("-inf")}:
        return None
    return parsed


def row_number(row: NormalizedRow, role: str) -> float | None:
    for value in row_values(row, role):
        parsed = parse_number(value)
        if parsed is not None:
            return parsed
    return None


def validate_measure(parameters: Mapping[str, object]) -> tuple[str, str | None]:
    if not isinstance(parameters, Mapping):
        raise ValueError("measure parameters must be an object")
    mode = parameters.get("measure", "count")
    if not isinstance(mode, str) or mode not in MEASURE_MODES:
        raise ValueError("unsupported measure")
    measure_role = parameters.get("measure_role")
    if mode == "count":
        if measure_role is not None:
            raise ValueError("measure_role is not allowed for count")
        return mode, None
    if not isinstance(measure_role, str) or not measure_role.strip():
        raise ValueError("measure_role is required for numeric measures")
    return mode, measure_role.strip()


def measure_rows(
    rows: Iterable[NormalizedRow],
    *,
    mode: str,
    measure_role: str | None,
) -> float | int:
    materialized = tuple(rows)
    if not all(isinstance(row, NormalizedRow) for row in materialized):
        raise ValueError("analysis row must be canonically normalized")
    if mode == "count":
        return len(materialized)
    if measure_role is None:
        raise ValueError("measure_role is required for numeric measures")
    values = tuple(
        value for row in materialized if (value := row_number(row, measure_role)) is not None
    )
    if not values:
        return 0
    if mode == "sum":
        result = sum(values)
    elif mode == "average":
        result = sum(values) / len(values)
    elif mode == "max":
        result = max(values)
    elif mode == "min":
        result = min(values)
    else:
        raise ValueError("unsupported measure")
    return int(result) if float(result).is_integer() else result


def dedupe_rows(rows: Iterable[NormalizedRow]) -> tuple[NormalizedRow, ...]:
    seen: set[int] = set()
    output: list[NormalizedRow] = []
    for row in rows:
        if not isinstance(row, NormalizedRow):
            raise ValueError("analysis row must be canonically normalized")
        if row.source_ordinal in seen:
            continue
        seen.add(row.source_ordinal)
        output.append(row)
    return tuple(output)
