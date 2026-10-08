"""New-to-observed-population applicants and their classification memberships."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from . import _advanced_common as c

ROLE_KEYS = ("date_role", "applicant_role", "classification_role")
ANALYSIS_ID = "new-entrants.v1"
VARIANT = "matrix"


def validate_parameters(value: object) -> dict[str, Any]:
    p = c.parameters(value, ROLE_KEYS, ("as_of_year", "top_classifications"))
    p["as_of_year"] = c.integer(p.get("as_of_year"), "as_of_year", 1800, 2199)
    p["top_classifications"] = c.integer(
        p.get("top_classifications", 20), "top_classifications", 1, 20
    )
    return p


def compute(records: Iterable[c.Record], parameters: Mapping[str, object]) -> dict[str, Any]:
    p = validate_parameters(parameters)
    rows = c.checked_records(records, tuple(p[k] for k in ROLE_KEYS))
    first = {}
    row_counts = Counter()
    history_budget = c.Budget()
    for row in rows:
        y = c.year(row, p["date_role"])
        labels = row[p["applicant_role"]]
        if y is None or not labels:
            continue
        history_budget.reserve(len(labels), sum(a not in first for a in labels))
        for applicant in labels:
            first[applicant] = min(first.get(applicant, y), y)
            row_counts[applicant] += 1
    candidates = sorted(
        (a for a in first if first[a] >= p["as_of_year"]), key=lambda a: (-row_counts[a], a)
    )[: p["top_n"]]
    selected = set(candidates)
    pairs = Counter()
    totals = Counter()
    classifications = Counter()
    budget = c.Budget()
    visible = 0
    for row in rows:
        if c.year(row, p["date_role"]) is None:
            continue
        applicants = tuple(a for a in row[p["applicant_role"]] if a in selected)
        items = row[p["classification_role"]]
        if not applicants or not items:
            continue
        amount = c.preflight_cartesian_size(len(applicants), len(items))
        budget.reserve(amount, sum((a, i) not in pairs for a in applicants for i in items))
        visible += 1
        for a in applicants:
            for item in items:
                pairs[a, item] += 1
                totals[a] += 1
                classifications[item] += 1
    labels = sorted(classifications, key=lambda x: (-classifications[x], x))[
        : p["top_classifications"]
    ]
    kept = set(labels)
    cells = [
        dict(applicant=a, classification=i, count=n, share=n / totals[a])
        for (a, i), n in sorted(pairs.items(), key=lambda t: (-t[1], t[0]))
        if i in kept
    ]
    applicants = [
        dict(
            label=a,
            first_year=first[a],
            row_count=row_counts[a],
            classification_memberships=totals[a],
        )
        for a in candidates
    ]
    return c.finish(
        ANALYSIS_ID,
        len(rows),
        visible,
        budget.contributions,
        as_of_year=p["as_of_year"],
        applicants=applicants,
        classifications=labels,
        cells=cells,
        share_basis="all_classification_memberships_per_applicant",
    )


def required_roles(parameters: Mapping[str, object]) -> tuple[str, ...]:
    p = validate_parameters(parameters)
    return tuple(p[key] for key in ROLE_KEYS)


def analyze_new_entrants(population: object, parameters: Mapping[str, object]) -> dict[str, Any]:
    return c.run_population(population, parameters, required_roles(parameters), compute)


def analyze_new_entrants_csv(
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
