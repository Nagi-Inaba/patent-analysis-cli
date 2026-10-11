"""M04/M05 annual witnessed activity and adjacent-calendar community flows.

Absent observations are not inactivity or retirement. Family annual presences
may repeat one cumulative unit. No default links across empty calendar years.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from fractions import Fraction

from patent_analysis.inventor_graph import co_inventor_graph, eligible, person_json, prepare
from patent_analysis.inventor_numeric import exact, finish, invalid, person_token, token_order
from patent_analysis.inventor_profiles import MAX_COLUMNS
from patent_analysis.inventor_units import aggregate_contributions, form_units

MAX_YEARS = 30


def _annual_inputs(units, observations):
    records, identities = prepare(units, observations)
    dates = {o.observed_date.kind for o in records.values() if o.observed_date.start}
    if len(dates) > 1:
        invalid()
    dated = defaultdict(list)
    missing = []
    for rid, row in sorted(records.items()):
        if row.observed_date.start is None:
            missing.append(rid)
        else:
            dated[row.observed_date.start.year].append(row)
    years = list(range(min(dated), max(dated) + 1)) if dated else []
    if len(years) > MAX_YEARS:
        invalid()
    columns = {c for row in records.values() for c in row.classifications}
    if len(columns) > MAX_COLUMNS or len({c[0] for c in columns}) > 1:
        invalid()
    views = {year: form_units(tuple(dated[year]), unit=units[0].unit) for year in years}
    return records, identities, dated, missing, years, views


def annual_activity(
    units,
    observations,
    *,
    person_weight="full",
    classification_weight="full",
    community_method="connected_components",
):
    records, identities, dated, missing, years, views = _annual_inputs(units, observations)
    contributions = aggregate_contributions(units, person_weight=person_weight)
    if classification_weight not in {"full", "fractional"}:
        invalid()
    originals = {u.unit_id: u for u in units}
    missing_ids = set(missing)
    activity = dict(contributions.people)
    summaries = [
        {
            **person_json(p, identities),
            "eligible": eligible(p),
            "cumulative_unit_activity": exact(activity[p]),
            "cumulative_unique_units": sum(p in u.inventor_keys for u in units),
            "annual_unit_presences": sum(p in u.inventor_keys for v in views.values() for u in v),
            "missing_date_unit_ids": sorted(
                {
                    u.unit_id
                    for u in units
                    if any(
                        p in records[r].inventor_keys for r in u.observation_ids if r in missing_ids
                    )
                }
            ),
        }
        for p in sorted(identities)
    ]
    output = []
    calendar = []
    previous_people = set()
    previous_partners = {}
    for year in years:
        annual_units = views[year]
        graph = co_inventor_graph(
            annual_units, tuple(dated[year]), community_method=community_method
        )
        communities = {n["person_token"]: n["community_id"] for n in graph["nodes"]}
        partners = defaultdict(set)
        current_people = {p for u in annual_units for p in u.inventor_keys}
        for u in annual_units:
            for a, b in u.observed_pairs:
                if eligible(a) and eligible(b):
                    partners[a].add(b)
                    partners[b].add(a)
        calendar.append(
            {
                "year": year,
                "observed": bool(dated[year]),
                "record_count": len(dated[year]),
                "unit_count": len(annual_units),
            }
        )
        for p in sorted(current_people | previous_people):
            selected = [u for u in annual_units if p in u.inventor_keys]
            total = Fraction(0)
            profile = defaultdict(Fraction)
            for u in selected:
                value = (
                    Fraction(1, len(originals[u.unit_id].inventor_keys))
                    if person_weight == "fractional"
                    else Fraction(1)
                )
                total += value
                codes = sorted(
                    {
                        c
                        for rid in u.observation_ids
                        if p in records[rid].inventor_keys
                        for c in records[rid].classifications
                    }
                )
                for c in codes:
                    profile[c] += value / (
                        len(codes) if classification_weight == "fractional" else 1
                    )
            before = previous_partners.get(p, set())
            after = partners[p]
            output.append(
                {
                    "person_token": person_token(p),
                    "year": year,
                    "observed": bool(selected),
                    "unit_count": len(selected) if selected else None,
                    "unit_ids": [u.unit_id for u in selected],
                    "record_ids": sorted(
                        {
                            rid
                            for u in selected
                            for rid in u.observation_ids
                            if p in records[rid].inventor_keys
                        }
                    ),
                    "activity": exact(total) if selected else None,
                    "classifications": [
                        {"classification": list(c), "count": exact(v)}
                        for c, v in sorted(profile.items())
                    ],
                    "partners": [person_token(q) for q in sorted(after)],
                    "added_partners": [person_token(q) for q in sorted(after - before)],
                    "continued_partners": [person_token(q) for q in sorted(after & before)],
                    "not_observed_partners": [person_token(q) for q in sorted(before - after)],
                    "community_id": communities.get(person_token(p)),
                }
            )
        previous_people = current_people
        previous_partners = partners
    return finish(
        {
            "people": summaries,
            "calendar": calendar,
            "observations": output,
            "missing_date_record_ids": missing,
            "basis": {
                "unit": units[0].unit if units else None,
                "person_weight": person_weight,
                "classification_weight": classification_weight,
                "annual_person_denominator": "original_unit_unique_people_including_unresolved",
                "cumulative": "unique_units",
                "annual": "year_local_unit_presences",
                "partner_comparison": "adjacent_calendar_years",
                "community_method": community_method,
                "annual_graph_basis": "year_local_units",
                "absence": "not_observed_not_inactivity",
                "precision": 12,
            },
            "coverage": {
                "records": len(records),
                "missing_date_records": len(missing),
                "ambiguous_people": sum(not eligible(p) for p in identities),
            },
        }
    )


def _group_id(year, kind, members):
    payload = json.dumps([year, kind, members], ensure_ascii=False, separators=(",", ":"))
    return f"{year}:{kind}:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


def cluster_flow(
    units, observations, *, community_method="connected_components", pair_weight="joint_unit_count"
):
    """M05 observed memberships, with explicit boundary/new/not-observed nodes.

    Every cluster has size-conserving incoming/outgoing widths. Scope entry/exit
    nodes make boundary conservation explicit without asserting activity outside
    the selected interval. IDs hash year+kind+sorted members, never team numbers.
    """
    records, identities, dated, missing, years, views = _annual_inputs(units, observations)
    yearly = {}
    nodes = []
    links = []
    for year in years:
        graph = co_inventor_graph(
            views[year],
            tuple(dated[year]),
            pair_weight=pair_weight,
            community_method=community_method,
        )
        groups = []
        for community in graph["communities"]:
            members = community["members"]
            node = {
                "node_id": _group_id(year, "cluster", members),
                "year": year,
                "kind": "cluster",
                "members": members,
                "size": len(members),
                "split": False,
                "merge": False,
            }
            groups.append(node)
            nodes.append(node)
        yearly[year] = groups

    def connect(source, target, members, kind):
        links.append(
            {
                "source": source["node_id"],
                "target": target["node_id"],
                "source_year": source["year"],
                "target_year": target["year"],
                "members": sorted(members, key=token_order),
                "width": len(members),
                "kind": kind,
            }
        )

    def auxiliary(cluster, members, year, kind, incoming):
        if not members:
            return
        # Cluster discriminator prevents accidental merging of unrelated residuals.
        node_id = _group_id(year, kind, [cluster["node_id"], *sorted(members, key=token_order)])
        node = {
            "node_id": node_id,
            "year": year,
            "kind": kind,
            "members": sorted(members, key=token_order),
            "size": len(members),
            "split": False,
            "merge": False,
        }
        nodes.append(node)
        connect(node, cluster, members, kind) if incoming else connect(cluster, node, members, kind)

    for year in years[:-1]:
        old = yearly[year]
        new = yearly[year + 1]
        before = {p for node in old for p in node["members"]}
        after = {p for node in new for p in node["members"]}
        for source in old:
            targets = 0
            for target in new:
                shared = set(source["members"]) & set(target["members"])
                if shared:
                    connect(source, target, shared, "shared_members")
                    targets += 1
            source["split"] = targets > 1
            auxiliary(source, set(source["members"]) - after, year + 1, "not_observed", False)
        for target in new:
            sources = sum(bool(set(target["members"]) & set(source["members"])) for source in old)
            target["merge"] = sources > 1
            auxiliary(target, set(target["members"]) - before, year, "newly_observed", True)
    if years:
        for node in yearly[years[0]]:
            auxiliary(node, node["members"], years[0], "scope_entry", True)
        for node in yearly[years[-1]]:
            auxiliary(node, node["members"], years[-1], "scope_exit", False)
    dated_people = {p for rows in dated.values() for row in rows for p in row.inventor_keys}
    unplottable = [
        {
            **person_json(p, identities),
            "reasons": (["ambiguous_identity"] if not eligible(p) else [])
            + (["missing_date"] if p not in dated_people else []),
        }
        for p in sorted(identities)
        if not eligible(p) or p not in dated_people
    ]
    return finish(
        {
            "unplottable": unplottable,
            "nodes": sorted(
                nodes, key=lambda n: (n["year"], n["kind"], [token_order(p) for p in n["members"]])
            ),
            "links": sorted(
                links, key=lambda link: (link["source_year"], link["source"], link["target"])
            ),
            "calendar": [{"year": y, "observed": bool(dated[y])} for y in years],
            "missing_date_record_ids": missing,
            "basis": {
                "community_method": community_method,
                "pair_weight": pair_weight,
                "graph_scope": "full_year_local_units",
                "links": "adjacent_calendar_years_only",
                "width": "observed_person_memberships",
                "boundary": "scope_entry_exit_not_activity_claim",
            },
            "coverage": {
                "records": len(records),
                "missing_date_records": len(missing),
                "ambiguous_people": sum(not eligible(p) for p in identities),
            },
        }
    )
