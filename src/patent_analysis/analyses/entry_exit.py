"""First/last observed years; recent activity is not a real-world exit verdict."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from . import _advanced_common as c

ROLE_KEYS = ("date_role", "category_role")
ANALYSIS_ID = "entry-exit.v1"
VARIANT = "points"


def validate_parameters(value: object) -> dict[str, Any]:
    return c.parameters(value, ROLE_KEYS)


def compute(records: Iterable[c.Record], parameters: Mapping[str, object]) -> dict[str, Any]:
    p = validate_parameters(parameters)
    rows = c.checked_records(records, tuple(p[k] for k in ROLE_KEYS))
    buckets = {}
    maximum = None
    visible = 0
    budget = c.Budget()
    for row in rows:
        y, labels = c.year(row, p["date_role"]), row[p["category_role"]]
        if y is None or not labels:
            continue
        budget.reserve(len(labels), sum(label not in buckets for label in labels))
        maximum = y if maximum is None else max(maximum, y)
        visible += 1
        for label in labels:
            b = buckets.setdefault(label, [y, y, 0])
            b[0], b[1], b[2] = min(b[0], y), max(b[1], y), b[2] + 1
    cutoff = None if maximum is None else maximum - 2
    points = [
        dict(label=label, first_year=b[0], last_year=b[1], count=b[2], active_recent=b[1] >= cutoff)
        for label, b in sorted(buckets.items(), key=lambda v: (-v[1][2], v[0]))[: p["top_n"]]
    ]
    return c.finish(
        ANALYSIS_ID,
        len(rows),
        visible,
        budget.contributions,
        as_of_year=maximum,
        active_since_year=cutoff,
        points=points,
    )


def required_roles(parameters: Mapping[str, object]) -> tuple[str, ...]:
    p = validate_parameters(parameters)
    return tuple(p[key] for key in ROLE_KEYS)


def analyze_entry_exit(population: object, parameters: Mapping[str, object]) -> dict[str, Any]:
    return c.run_population(population, parameters, required_roles(parameters), compute)


def analyze_entry_exit_csv(
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
