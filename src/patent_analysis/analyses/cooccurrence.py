"""Symmetric cooccurrence counts; each distinct unordered pair counts once per row."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from . import _advanced_common as c
from ._pair_counts import accumulate

ROLE_KEYS = ("category_role",)
ANALYSIS_ID = "cooccurrence.v1"
VARIANT = "matrix"


def validate_parameters(value: object) -> dict[str, Any]:
    return c.parameters(value, ROLE_KEYS)


def compute(records: Iterable[c.Record], parameters: Mapping[str, object]) -> dict[str, Any]:
    p = validate_parameters(parameters)
    rows = c.checked_records(records, tuple(p[k] for k in ROLE_KEYS))
    nodes, counts, visible, budget = accumulate(rows, p["category_role"], include_singletons=True)
    labels = sorted(nodes, key=lambda x: (-nodes[x], x))[: p["top_n"]]
    selected = set(labels)
    cells = [
        dict(x=x, y=y, count=0 if x == y else counts[tuple(sorted((x, y)))])
        for y in labels
        for x in labels
    ]
    pairs = [
        dict(source=a, target=b, count=n)
        for (a, b), n in sorted(counts.items(), key=lambda t: (-t[1], t[0]))
        if a in selected and b in selected
    ]
    return c.finish(
        ANALYSIS_ID,
        len(rows),
        visible,
        budget.contributions,
        labels=labels,
        label_counts=[dict(label=x, count=nodes[x]) for x in labels],
        cells=cells,
        pairs=pairs,
    )


def required_roles(parameters: Mapping[str, object]) -> tuple[str, ...]:
    p = validate_parameters(parameters)
    return tuple(p[key] for key in ROLE_KEYS)


def analyze_cooccurrence(population: object, parameters: Mapping[str, object]) -> dict[str, Any]:
    return c.run_population(population, parameters, required_roles(parameters), compute)


def analyze_cooccurrence_csv(
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
