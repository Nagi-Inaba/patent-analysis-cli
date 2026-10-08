"""Explicit group A minus group B count matrices, with no automatic group choice."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from . import _advanced_common as c

ROLE_KEYS = ("x_role", "y_role", "group_role")
ANALYSIS_ID = "compara.v1"
VARIANT = "matrix"


def validate_parameters(value: object) -> dict[str, Any]:
    p = c.parameters(value, ROLE_KEYS, ("group_a", "group_b", "top_x", "top_y"))
    for key in ("group_a", "group_b"):
        p[key] = c.text(p.get(key), key)
    if p["group_a"] == p["group_b"]:
        raise ValueError("comparison groups must differ")
    p["top_x"] = c.integer(p.get("top_x", p["top_n"]), "top_x", 1, 20)
    p["top_y"] = c.integer(p.get("top_y", p["top_n"]), "top_y", 1, 20)
    return p


def compute(records: Iterable[c.Record], parameters: Mapping[str, object]) -> dict[str, Any]:
    p = validate_parameters(parameters)
    rows = c.checked_records(records, tuple(p[k] for k in ROLE_KEYS))
    x_counts, y_counts = Counter(), Counter()
    counts = {}
    budget = c.Budget()
    visible = 0
    for row in rows:
        xs, ys, groups = row[p["x_role"]], row[p["y_role"]], row[p["group_role"]]
        indexes = tuple(i for i, g in enumerate((p["group_a"], p["group_b"])) if g in groups)
        if not xs or not ys or not indexes:
            continue
        amount = c.preflight_cartesian_size(len(xs), len(ys), len(indexes))
        new = sum(
            (x, y) not in counts or counts[x, y][i] == 0 for x in xs for y in ys for i in indexes
        )
        budget.reserve(amount, new)
        visible += 1
        x_counts.update(xs)
        y_counts.update(ys)
        for x in xs:
            for y in ys:
                bucket = counts.setdefault((x, y), [0, 0])
                for i in indexes:
                    bucket[i] += 1
    x_axis = sorted(x_counts, key=lambda x: (-x_counts[x], x))[: p["top_x"]]
    y_axis = sorted(y_counts, key=lambda y: (-y_counts[y], y))[: p["top_y"]]
    cells = []
    for y in y_axis:
        for x in x_axis:
            a, b = counts.get((x, y), (0, 0))
            cells.append(dict(x=x, y=y, a_count=a, b_count=b, difference=a - b))
    return c.finish(
        ANALYSIS_ID,
        len(rows),
        visible,
        budget.contributions,
        groups={"a": p["group_a"], "b": p["group_b"]},
        x=x_axis,
        y=y_axis,
        cells=cells,
    )


def required_roles(parameters: Mapping[str, object]) -> tuple[str, ...]:
    p = validate_parameters(parameters)
    return tuple(p[key] for key in ROLE_KEYS)


def analyze_compara(population: object, parameters: Mapping[str, object]) -> dict[str, Any]:
    return c.run_population(population, parameters, required_roles(parameters), compute)


def analyze_compara_csv(
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
