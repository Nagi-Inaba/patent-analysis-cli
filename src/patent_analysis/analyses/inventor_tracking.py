"""Annual co-invention components and applicant associations without entity inference."""

from __future__ import annotations

import unicodedata
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from itertools import combinations
from pathlib import Path
from typing import Any

from . import _advanced_common as c

ANALYSIS_ID = "inventor-tracking.v1"
VARIANT = "network"
ROLE_KEYS = ("date_role", "inventor_role", "applicant_role")
MAX_INVENTORS = 20
MAX_YEAR_SPAN = 12
MAX_RESULT_BYTES = 192 * 1024


def validate_parameters(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) - {*ROLE_KEYS, "identity_kind"}:
        raise ValueError("unsupported inventor tracking parameters")
    p = {key: c.text(value.get(key), key, role=True) for key in ROLE_KEYS}
    if len(set(p.values())) != len(ROLE_KEYS):
        raise ValueError("analysis roles must differ")
    p["identity_kind"] = value.get("identity_kind", "name")
    if p["identity_kind"] not in ("name", "id"):
        raise ValueError("identity_kind must be name or id")
    return p


def required_roles(parameters: Mapping[str, object]) -> tuple[str, ...]:
    p = validate_parameters(parameters)
    return tuple(p[key] for key in ROLE_KEYS)


def relationships(observations, coedges):
    """Year-local components; adjacent-year links represent shared identities."""
    by_year = defaultdict(set)
    for observation in observations:
        by_year[observation["year"]].add(observation["inventor"])
    clusters, membership = [], {}
    for year, names in sorted(by_year.items()):
        adjacency = {name: set() for name in names}
        for edge in coedges:
            if edge["year"] == year:
                adjacency[edge["source"]].add(edge["target"])
                adjacency[edge["target"]].add(edge["source"])
        remaining, index = set(names), 0
        while remaining:
            pending, members = [min(remaining)], set()
            while pending:
                name = pending.pop()
                if name not in members:
                    members.add(name)
                    pending.extend(adjacency[name] - members)
            remaining.difference_update(members)
            index += 1
            identity = f"{year}:{index}"
            clusters.append({"cluster_id": identity, "year": year, "members": sorted(members)})
            for name in members:
                membership[year, name] = identity
    flows = defaultdict(list)
    for (year, name), source in sorted(membership.items()):
        if target := membership.get((year + 1, name)):
            flows[source, target].append(name)
    outgoing, incoming = Counter(a for a, _ in flows), Counter(b for _, b in flows)
    links = [
        {
            "source": a,
            "target": b,
            "inventors": sorted(names),
            "count": len(names),
            "split": outgoing[a] > 1,
            "merge": incoming[b] > 1,
        }
        for (a, b), names in sorted(flows.items())
    ]
    changes, previous = [], {}
    for observation in observations:
        name, year = observation["inventor"], observation["year"]
        if before := previous.get(name):
            known = not (before["missing_applicant_rows"] or observation["missing_applicant_rows"])
            added = (
                sorted(set(observation["applicants"]) - set(before["applicants"])) if known else []
            )
            removed = (
                sorted(set(before["applicants"]) - set(observation["applicants"])) if known else []
            )
            changes.append(
                {
                    "inventor": name,
                    "from_year": before["year"],
                    "to_year": year,
                    "gap_years": year - before["year"] - 1,
                    "from_cluster": membership[before["year"], name],
                    "to_cluster": membership[year, name],
                    "status": "unknown"
                    if not known
                    else "changed"
                    if added or removed
                    else "unchanged",
                    "added_applicants": added,
                    "removed_applicants": removed,
                }
            )
        previous[name] = observation
    return clusters, membership, links, changes


def compute(records: Iterable[c.Record], parameters: Mapping[str, object]) -> dict[str, Any]:
    p = validate_parameters(parameters)
    rows = c.checked_records(records, tuple(p[key] for key in ROLE_KEYS))
    observations, missing, pairs, associations = Counter(), Counter(), Counter(), Counter()
    inventors, years = set(), set()
    budget, visible = c.Budget(), 0
    for row in rows:
        if len(row[p["date_role"]]) > 1:
            raise ValueError("inventor tracking requires one observation year per record")
        year = c.year(row, p["date_role"])
        names, applicants = row[p["inventor_role"]], row[p["applicant_role"]]
        if p["identity_kind"] == "name":
            names = tuple(sorted({
                c.text(unicodedata.normalize("NFKC", name), "inventor") for name in names
            }))
        if year is None or not names:
            continue
        inventors.update(names)
        years.add(year)
        if len(inventors) > MAX_INVENTORS or max(years) - min(years) >= MAX_YEAR_SPAN:
            raise c.AnalysisCapacityError(
                "tracking requires at most 20 inventors across 12 calendar years"
            )
        n = len(names)
        budget.reserve(n + c.preflight_pair_size(n) + n * len(applicants), 0)
        visible += 1
        observations.update((year, name) for name in names)
        if not applicants:
            missing.update((year, name) for name in names)
        pairs.update((year, a, b) for a, b in combinations(sorted(names), 2))
        associations.update((year, name, applicant) for name in names for applicant in applicants)
        if len(observations) + len(pairs) + len(associations) > c.MAX_BUCKETS:
            raise c.AnalysisCapacityError("tracking keys exceed limit")
    affiliation_rows = [
        {"year": year, "inventor": name, "applicant": applicant, "count": count}
        for (year, name, applicant), count in sorted(associations.items())
    ]
    applicants_by_key = defaultdict(list)
    for year, name, applicant in sorted(associations):
        applicants_by_key[year, name].append(applicant)
    observed = [
        {
            "year": year,
            "inventor": name,
            "count": count,
            "missing_applicant_rows": missing[year, name],
            "applicants": applicants_by_key[year, name],
        }
        for (year, name), count in sorted(observations.items())
    ]
    coedges = [
        {"year": year, "source": a, "target": b, "count": count}
        for (year, a, b), count in sorted(pairs.items())
    ]
    clusters, membership, links, changes = relationships(observed, coedges)
    for observation in observed:
        observation["cluster_id"] = membership[observation["year"], observation["inventor"]]
    return c.finish(
        ANALYSIS_ID,
        len(rows),
        visible,
        budget.contributions,
        result_byte_limit=MAX_RESULT_BYTES,
        identity_kind=p["identity_kind"],
        years=sorted(years),
        inventors=[
            {
                "inventor": name,
                "count": sum(n for (y, a), n in observations.items() if a == name),
                "first_year": min(y for y, a in observations if a == name),
                "last_year": max(y for y, a in observations if a == name),
            }
            for name in sorted(inventors)
        ],
        observations=observed,
        co_inventions=coedges,
        affiliations=affiliation_rows,
        clusters=clusters,
        cluster_links=links,
        affiliation_changes=changes,
    )


def analyze_inventor_tracking_csv(
    source: str | Path,
    spec: Mapping[str, object],
    *,
    allowed_root: str | Path,
) -> dict[str, Any]:
    result = c.run_csv(
        source,
        spec,
        allowed_root=allowed_root,
        analysis_id=ANALYSIS_ID,
        variant=VARIANT,
        validator=validate_parameters,
        role_keys=ROLE_KEYS,
        compute=compute,
    )
    result["warnings"] = [
        "出願人との関係は同じ特許レコードでの共記載であり、雇用・転職を示しません。",
        "名前を用いる場合、同姓同名・表記揺れを自動で識別しません。"
        if result["data"]["identity_kind"] == "name"
        else "発明者IDは入力データの同一性を前提とし、外部照合しません。",
    ]
    return result
