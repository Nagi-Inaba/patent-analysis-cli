"""Category membership composition within one explicitly selected matrix cell."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from . import _advanced_common as c

ROLE_KEYS = ("x_role", "y_role", "category_role")
ANALYSIS_ID = "matrix-composition.v1"
VARIANT = "composition"


def validate_parameters(value: object) -> dict[str, Any]:
    p = c.parameters(value, ROLE_KEYS, ("x_value", "y_value"))
    for key in ("x_value", "y_value"):
        p[key] = c.text(p.get(key), key)
    return p


def compute(records: Iterable[c.Record], parameters: Mapping[str, object]) -> dict[str, Any]:
    p = validate_parameters(parameters)
    rows = c.checked_records(records, tuple(p[k] for k in ROLE_KEYS))
    counts = Counter()
    budget = c.Budget()
    cell_rows = visible = 0
    for row in rows:
        if p["x_value"] not in row[p["x_role"]] or p["y_value"] not in row[p["y_role"]]:
            continue
        cell_rows += 1
        labels = row[p["category_role"]]
        if not labels:
            continue
        budget.reserve(len(labels), sum(label not in counts for label in labels))
        visible += 1
        counts.update(labels)
    total = budget.contributions
    items = [
        dict(label=label, count=n, share=n / total)
        for label, n in sorted(counts.items(), key=lambda t: (-t[1], t[0]))[: p["top_n"]]
    ]
    return c.finish(
        ANALYSIS_ID,
        len(rows),
        visible,
        total,
        cell={"x": p["x_value"], "y": p["y_value"]},
        cell_rows=cell_rows,
        category_memberships=total,
        share_basis="category_memberships",
        items=items,
    )


def required_roles(parameters: Mapping[str, object]) -> tuple[str, ...]:
    p = validate_parameters(parameters)
    return tuple(p[key] for key in ROLE_KEYS)


def analyze_matrix_composition(
    population: object, parameters: Mapping[str, object]
) -> dict[str, Any]:
    return c.run_population(population, parameters, required_roles(parameters), compute)


def analyze_matrix_composition_csv(
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
