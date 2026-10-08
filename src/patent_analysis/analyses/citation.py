"""Bounded record-level citation ranking, never implicit applicant aggregation."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any

from . import _advanced_common as c

ROLE_KEYS = ("date_role", "label_role", "citation_role")
ANALYSIS_ID = "citation.v1"
VARIANT = "points"
MAX_CITATION_VALUE = 1_000_000_000_000
_CITATION = re.compile(
    r"(?:(?:被引用(?:件数|数|回数)?|引用(?:件数|数|回数)?|cited\s*by|"
    r"citation\s*count|citations?|forward\s*citations?)\s*[:：]\s*)?"
    r"((?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)",
    re.IGNORECASE,
)


def validate_parameters(value: object) -> dict[str, Any]:
    return c.parameters(value, ROLE_KEYS)


def parse_citation_count(value: object) -> int | float | None:
    if not isinstance(value, str) or len(value) > 128:
        return None
    match = _CITATION.fullmatch(value.strip())
    if match is None:
        return None
    # Validate grouping before removing commas, and enforce the decimal bound
    # before float conversion can round an out-of-range input onto the limit.
    exact = Decimal(match[1].replace(",", ""))
    if not 0 <= exact <= MAX_CITATION_VALUE:
        return None
    number = float(exact)
    return int(number) if number.is_integer() else number


def compute(records: Iterable[c.Record], parameters: Mapping[str, object]) -> dict[str, Any]:
    p = validate_parameters(parameters)
    rows = c.checked_records(records, tuple(p[k] for k in ROLE_KEYS))
    candidates = []
    budget = c.Budget()
    for row in rows:
        y = c.year(row, p["date_role"])
        labels, values = row[p["label_role"]], row[p["citation_role"]]
        # Multiple numeric values are ambiguous, not a request to sum citations.
        n = parse_citation_count(values[0]) if len(values) == 1 else None
        if y is None or len(labels) != 1 or n is None:
            continue
        budget.reserve(1, 1)
        candidates.append((labels[0], y, n))
    candidates.sort(key=lambda x: (-x[2], x[1], x[0]))
    points = [
        dict(point_id=i + 1, label=label, year=y, citation_value=n)
        for i, (label, y, n) in enumerate(candidates[: p["top_n"]])
    ]
    return c.finish(ANALYSIS_ID, len(rows), len(candidates), budget.contributions, points=points)


def required_roles(parameters: Mapping[str, object]) -> tuple[str, ...]:
    p = validate_parameters(parameters)
    return tuple(p[key] for key in ROLE_KEYS)


def analyze_citation(population: object, parameters: Mapping[str, object]) -> dict[str, Any]:
    return c.run_population(population, parameters, required_roles(parameters), compute)


def analyze_citation_csv(
    source: str | Path, spec: Mapping[str, object], *, allowed_root: str | Path
) -> dict[str, Any]:
    return c.run_csv(
        source,
        spec,
        allowed_root=allowed_root,
        analysis_id=ANALYSIS_ID,
        variant=VARIANT,
        validator=validate_parameters,
        role_keys=ROLE_KEYS,
        compute=compute,
    )
