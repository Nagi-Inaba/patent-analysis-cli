"""Long/short span half-period count changes; undefined rates remain null."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from . import _advanced_common as c

ROLE_KEYS = ("date_role", "category_role")
ANALYSIS_ID = "growth-quadrant.v1"
VARIANT = "quadrant"


def validate_parameters(value: object) -> dict[str, Any]:
    p = c.parameters(
        value, ROLE_KEYS, ("long_start_year", "long_end_year", "short_start_year", "short_end_year")
    )
    c.year_span(p, "long_start_year", "long_end_year")
    c.year_span(p, "short_start_year", "short_end_year")
    return p


def _rate(counts, start, end):
    midpoint = (start + end) // 2
    previous = sum(n for y, n in counts.items() if start <= y <= midpoint)
    recent = sum(n for y, n in counts.items() if midpoint < y <= end)
    rate = (recent - previous) / previous * 100 if previous else None if recent else 0.0
    return dict(
        previous=previous,
        recent=recent,
        rate_percent=rate,
        state="new" if previous == 0 and recent else "measured" if previous else "empty",
    )


def compute(records: Iterable[c.Record], parameters: Mapping[str, object]) -> dict[str, Any]:
    p = validate_parameters(parameters)
    rows = c.checked_records(records, tuple(p[k] for k in ROLE_KEYS))
    long = c.year_span(p, "long_start_year", "long_end_year")
    short = c.year_span(p, "short_start_year", "short_end_year")
    counts = {}
    budget = c.Budget()
    visible = 0
    for row in rows:
        y = c.year(row, p["date_role"])
        labels = row[p["category_role"]]
        if y is None or not labels or not (long[0] <= y <= long[1] or short[0] <= y <= short[1]):
            continue
        budget.reserve(
            len(labels), sum(label not in counts or y not in counts[label] for label in labels)
        )
        visible += 1
        for label in labels:
            counts.setdefault(label, Counter())[y] += 1
    points = []
    for label in sorted(counts, key=lambda x: (-sum(counts[x].values()), x))[: p["top_n"]]:
        a, b = _rate(counts[label], *long), _rate(counts[label], *short)
        x, y = a["rate_percent"], b["rate_percent"]
        quadrant = (
            "new"
            if x is None or y is None
            else (
                "sustained_growth"
                if x >= 0 and y >= 0
                else "recovery"
                if x < 0 <= y
                else "slowing"
                if y < 0 <= x
                else "decline"
            )
        )
        points.append(
            dict(
                label=label,
                total_count=sum(counts[label].values()),
                long=a,
                short=b,
                quadrant=quadrant,
            )
        )
    return c.finish(
        ANALYSIS_ID,
        len(rows),
        visible,
        budget.contributions,
        points=points,
        long_span={"start_year": long[0], "end_year": long[1]},
        short_span={"start_year": short[0], "end_year": short[1]},
    )


def required_roles(parameters: Mapping[str, object]) -> tuple[str, ...]:
    p = validate_parameters(parameters)
    return tuple(p[key] for key in ROLE_KEYS)


def analyze_growth_quadrant(population: object, parameters: Mapping[str, object]) -> dict[str, Any]:
    return c.run_population(population, parameters, required_roles(parameters), compute)


def analyze_growth_quadrant_csv(
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
