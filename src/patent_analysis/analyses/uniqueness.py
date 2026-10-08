"""Distinct items owned by one group across the full selected population."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from . import _advanced_common as c
from ._item_ownership import ownership

ROLE_KEYS = ("group_role", "item_role")
ANALYSIS_ID = "uniqueness.v1"
VARIANT = "grouped-metrics"


def validate_parameters(value: object) -> dict[str, Any]:
    return c.parameters(value, ROLE_KEYS)


def compute(records: Iterable[c.Record], parameters: Mapping[str, object]) -> dict[str, Any]:
    p = validate_parameters(parameters)
    rows = c.checked_records(records, tuple(p[k] for k in ROLE_KEYS))
    items, owners, records_by_group, memberships, budget = ownership(
        rows, p["group_role"], p["item_role"]
    )
    groups = []
    for group, owned in items.items():
        unique = sorted(i for i in owned if len(owners[i]) == 1)
        groups.append(
            dict(
                group=group,
                record_count=records_by_group[group],
                total_item_count=len(owned),
                unique_item_count=len(unique),
                uniqueness_rate=len(unique) / len(owned),
                unique_items=unique[:20],
                items_truncated=len(unique) > 20,
            )
        )
    groups.sort(
        key=lambda g: (
            -g["unique_item_count"],
            -g["uniqueness_rate"],
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
        groups=groups[: p["top_n"]],
    )


def required_roles(parameters: Mapping[str, object]) -> tuple[str, ...]:
    p = validate_parameters(parameters)
    return tuple(p[key] for key in ROLE_KEYS)


def analyze_uniqueness(population: object, parameters: Mapping[str, object]) -> dict[str, Any]:
    return c.run_population(population, parameters, required_roles(parameters), compute)


def analyze_uniqueness_csv(
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
