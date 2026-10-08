"""Bounded collaboration nodes and links, without layout or rendering code."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from . import _advanced_common as c
from ._pair_counts import accumulate

ROLE_KEYS = ("category_role",)
ANALYSIS_ID = "collaboration-network.v1"
VARIANT = "network"


def validate_parameters(value: object) -> dict[str, Any]:
    p = c.parameters(value, ROLE_KEYS, ("top_nodes",), top_max=80)
    p["top_nodes"] = c.integer(p.get("top_nodes", 50), "top_nodes", 1, 50)
    return p


def compute(records: Iterable[c.Record], parameters: Mapping[str, object]) -> dict[str, Any]:
    p = validate_parameters(parameters)
    rows = c.checked_records(records, tuple(p[k] for k in ROLE_KEYS))
    counts, pairs, visible, budget = accumulate(rows, p["category_role"], include_singletons=False)
    selected = set(sorted(counts, key=lambda x: (-counts[x], x))[: p["top_nodes"]])
    top_pairs = sorted(pairs.items(), key=lambda t: (-t[1], t[0]))[: p["top_n"]]
    edges = [
        dict(source=a, target=b, count=n)
        for (a, b), n in top_pairs
        if a in selected and b in selected
    ]
    linked = {e[k] for e in edges for k in ("source", "target")}
    nodes = [dict(label=a, count=counts[a]) for a in sorted(linked, key=lambda x: (-counts[x], x))]
    return c.finish(ANALYSIS_ID, len(rows), visible, budget.contributions, nodes=nodes, edges=edges)


def required_roles(parameters: Mapping[str, object]) -> tuple[str, ...]:
    p = validate_parameters(parameters)
    return tuple(p[key] for key in ROLE_KEYS)


def analyze_network(population: object, parameters: Mapping[str, object]) -> dict[str, Any]:
    return c.run_population(population, parameters, required_roles(parameters), compute)


def analyze_network_csv(
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
