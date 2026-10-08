"""Global shared-item membership and record-level involvement counts."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from . import _advanced_common as c
from ._item_ownership import ownership

ROLE_KEYS = ("group_role", "item_role")
ANALYSIS_ID = "shared-involvement.v1"
VARIANT = "grouped-metrics"


def validate_parameters(value: object) -> dict[str, Any]:
    p = c.parameters(value, ROLE_KEYS, ("min_groups",))
    p["min_groups"] = c.integer(p.get("min_groups", 2), "min_groups", 2, 100_000)
    return p


def compute(records: Iterable[c.Record], parameters: Mapping[str, object]) -> dict[str, Any]:
    p = validate_parameters(parameters)
    rows = c.checked_records(records, tuple(p[k] for k in ROLE_KEYS))
    items, owners, records_by_group, memberships, budget = ownership(
        rows, p["group_role"], p["item_role"]
    )
    shared = {i for i, groups in owners.items() if len(groups) >= p["min_groups"]}
    involved = Counter()
    for groups, row_items in memberships:
        if any(i in shared for i in row_items):
            involved.update(groups)
    groups = []
    for group, owned in items.items():
        common = sorted(owned & shared)
        groups.append(
            dict(
                group=group,
                record_count=records_by_group[group],
                involvement_record_count=involved[group],
                total_item_count=len(owned),
                shared_item_count=len(common),
                shared_rate=len(common) / len(owned),
                shared_items=common[:20],
                items_truncated=len(common) > 20,
            )
        )
    groups.sort(
        key=lambda g: (
            -g["shared_item_count"],
            -g["involvement_record_count"],
            -g["shared_rate"],
            -g["total_item_count"],
            g["group"],
        )
    )
    return c.finish(
        ANALYSIS_ID,
        len(rows),
        len(memberships),
        budget.contributions,
        all_group_count=len(groups),
        min_groups=p["min_groups"],
        groups=groups[: p["top_n"]],
    )


def required_roles(parameters: Mapping[str, object]) -> tuple[str, ...]:
    p = validate_parameters(parameters)
    return tuple(p[key] for key in ROLE_KEYS)


def analyze_shared_involvement(
    population: object, parameters: Mapping[str, object]
) -> dict[str, Any]:
    return c.run_population(population, parameters, required_roles(parameters), compute)


def analyze_shared_involvement_csv(
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
