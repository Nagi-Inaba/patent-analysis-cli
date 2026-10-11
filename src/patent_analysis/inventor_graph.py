"""M01/M02 pure full-graph kernels. Metrics precede ego extraction.

No SciPy/NetworkX required. Exact reciprocal-strength Brandes distances;
PageRank uses uniform teleport/dangling, alpha .85 and global L1 residual.
"""

from __future__ import annotations

import heapq
import math
from collections import defaultdict
from fractions import Fraction

from patent_analysis.inventor_numeric import (
    checked,
    exact,
    finish,
    invalid,
    json_size,
    number,
    person_token,
    token_order,
)
from patent_analysis.inventor_units import aggregate_contributions, form_units

MAX_NODES = 200
MAX_EDGES = 5000


def prepare(units, observations):
    """Validate complete evidence, not a family person/code Cartesian product."""
    aggregate_contributions(units)
    if not isinstance(observations, tuple):
        invalid()
    if units:
        rebuilt = form_units(observations, unit=units[0].unit)
        if tuple(sorted(units, key=lambda u: u.unit_id)) != rebuilt:
            invalid()
    elif observations:
        invalid()
    records = {o.record_id: o for o in observations}
    identities = defaultdict(list)
    for row in records.values():
        for identity in row.inventors:
            identities[identity.key].append(identity)
    if len(identities) > MAX_NODES:
        invalid()
    return records, identities


def eligible(key):
    return key[0] in {"id", "name"}


def person_json(key, identities):
    values = identities[key]
    return {
        "person_key": list(key),
        "person_token": person_token(key),
        "inventor_id": key[1] if key[0] == "id" else None,
        "display_name": min(i.display_name for i in values),
        "identity_status": sorted({i.status for i in values}),
        "caveats": sorted({c for i in values for c in i.caveats}),
        "candidate_ids": sorted({c for i in values for c in i.candidate_ids}),
        "source_ids": sorted({s for i in values for s in i.source_ids}),
    }


def _betweenness(adjacency, weighted):
    totals = dict.fromkeys(adjacency, Fraction(0))
    for source in adjacency:
        predecessors = {p: [] for p in adjacency}
        sigma = dict.fromkeys(adjacency, 0)
        sigma[source] = 1
        distance = {source: Fraction(0)}
        stack = []
        queue = [(Fraction(0), source)]
        settled = set()
        while queue:
            current_distance, node = heapq.heappop(queue)
            if node in settled:
                continue
            settled.add(node)
            stack.append(node)
            for neighbor, strength in sorted(adjacency[node].items()):
                candidate = checked(current_distance + (1 / strength if weighted else 1))
                if neighbor not in distance or candidate < distance[neighbor]:
                    distance[neighbor] = candidate
                    sigma[neighbor] = sigma[node]
                    predecessors[neighbor] = [node]
                    heapq.heappush(queue, (candidate, neighbor))
                elif candidate == distance[neighbor]:
                    sigma[neighbor] += sigma[node]
                    predecessors[neighbor].append(node)
        dependency = dict.fromkeys(adjacency, Fraction(0))
        for node in reversed(stack):
            for parent in predecessors[node]:
                dependency[parent] = checked(
                    dependency[parent]
                    + Fraction(sigma[parent], sigma[node]) * (1 + dependency[node])
                )
            if node != source:
                totals[node] = checked(totals[node] + dependency[node])
    n = len(adjacency)
    return {
        p: checked(v / ((n - 1) * (n - 2))) if n > 2 else Fraction(0) for p, v in totals.items()
    }


def _pagerank(adjacency, *, max_iterations=1000):
    n = len(adjacency)
    if not n:
        return {}, {"iterations": 0, "residual": 0.0}
    people = list(adjacency)
    strengths = {p: sum(adjacency[p].values(), Fraction(0)) for p in people}
    transitions = {
        p: [(q, float(w / strengths[p])) for q, w in adjacency[p].items()] for p in people
    }

    def step(values):
        dangling = math.fsum(values[p] for p in people if not strengths[p])
        base = (0.15 + 0.85 * dangling) / n
        out = dict.fromkeys(people, base)
        for p in people:
            for q, probability in transitions[p]:
                out[q] += 0.85 * values[p] * probability
        return out

    values = dict.fromkeys(people, 1 / n)
    for iteration in range(1, max_iterations + 1):
        nxt = step(values)
        residual = math.fsum(abs(nxt[p] - values[p]) for p in people)
        if (
            not all(math.isfinite(v) and v >= 0 for v in nxt.values())
            or abs(math.fsum(nxt.values()) - 1) > 1e-12
        ):
            invalid()
        if residual <= 1e-12:
            return values, {"iterations": iteration, "residual": number(residual)}
        values = nxt
    invalid()


def _components(adjacency):
    remaining = set(adjacency)
    groups = []
    while remaining:
        pending = [min(remaining)]
        found = set()
        while pending:
            p = pending.pop()
            if p not in found:
                found.add(p)
                pending.extend(q for q in adjacency[p] if q not in found)
        remaining -= found
        groups.append(tuple(sorted(found)))
    return sorted(groups)


def _communities(adjacency, method):
    if method == "connected_components":
        return _components(adjacency)
    if method != "greedy_modularity":
        invalid()
    groups = {p: (p,) for p in adjacency}
    degree = {p: sum(a.values(), Fraction(0)) for p, a in adjacency.items()}
    m = sum(degree.values(), Fraction(0)) / 2
    cross = {(p, q): w for p, a in adjacency.items() for q, w in a.items() if p < q}
    if not m:
        return sorted(groups.values())
    # Merge largest positive exact delta Q; lexicographic sorted-members tie.
    # This is a deterministic greedy heuristic, not a global optimum.
    while cross:
        candidates = [
            (checked(w / m - degree[p] * degree[q] / (2 * m * m)), groups[p], groups[q], p, q)
            for (p, q), w in cross.items()
        ]
        best = min(candidates, key=lambda v: (-v[0], v[1], v[2]))
        gain, _, _, p, q = best
        if gain <= 0:
            break
        groups[p] = tuple(sorted(groups[p] + groups.pop(q)))
        degree[p] += degree.pop(q)
        cross.pop((p, q))
        updated = defaultdict(Fraction)
        for (a, b), w in cross.items():
            a, b = (p if a == q else a), (p if b == q else b)
            updated[tuple(sorted((a, b)))] += w
        cross = dict(sorted(updated.items()))
    return sorted(groups.values())


def date_json(date):
    return {
        "raw": date.raw,
        "kind": date.kind,
        "precision": date.precision,
        "start": date.start.isoformat() if date.start else None,
        "end": date.end.isoformat() if date.end else None,
    }


def co_inventor_graph(
    units,
    observations,
    *,
    person_weight="full",
    pair_weight="joint_unit_count",
    community_method="connected_components",
):
    """Return closed JSON nodes/edges/communities over the full eligible population."""
    records, identities = prepare(units, observations)
    if len({r.observed_date.kind for r in records.values() if r.observed_date.start}) > 1:
        invalid()
    contributions = aggregate_contributions(
        units, person_weight=person_weight, pair_weight=pair_weight
    )
    for _, value in (*contributions.people, *contributions.pairs):
        checked(value)
    people = sorted(p for p in identities if eligible(p))
    pairs = {pair: checked(w) for pair, w in contributions.pairs if all(map(eligible, pair))}
    if len(pairs) > MAX_EDGES:
        invalid()
    adjacency = {p: {} for p in people}
    for (a, b), weight in pairs.items():
        adjacency[a][b] = adjacency[b][a] = weight
    for neighbors in adjacency.values():
        checked(sum(neighbors.values(), Fraction(0)))
    activities = dict(contributions.people)
    evidence = defaultdict(set)
    unit_evidence = defaultdict(list)
    for unit in sorted(units, key=lambda u: u.unit_id):
        for pair, ids in unit.pair_evidence:
            evidence[pair].update(ids)
            unit_evidence[pair].append(unit.unit_id)
    edges = []
    for (a, b), weight in sorted(pairs.items()):
        ids = sorted(evidence[(a, b)])
        dates = [records[r].observed_date for r in ids if records[r].observed_date.start]
        first = min(dates, key=lambda d: (d.start, d.end, d.raw)) if dates else None
        last = max(dates, key=lambda d: (d.end, d.start, d.raw)) if dates else None
        edges.append(
            {
                "source": person_token(a),
                "target": person_token(b),
                "weight": exact(weight),
                "unit_ids": unit_evidence[(a, b)],
                "record_ids": ids,
                "first_observation": date_json(first) if first else None,
                "last_observation": date_json(last) if last else None,
                "missing_date_records": sum(records[r].observed_date.start is None for r in ids),
                "classifications": [
                    list(c) for c in sorted({c for r in ids for c in records[r].classifications})
                ],
            }
        )
    preliminary = [
        {
            **person_json(p, identities),
            "activity": exact(activities[p]),
            "strength": exact(sum(adjacency.get(p, {}).values(), Fraction(0))),
        }
        for p in sorted(identities)
    ]
    token_bytes = max((json_size(person_token(p)) for p in identities), default=0)
    # Linear evidence serialization plus conservative metric/community/coverage reserve.
    finish(
        {"nodes": preliminary, "edges": edges},
        reserve_bytes=len(identities) * (256 + 3 * token_bytes) + 4096,
    )
    unweighted = _betweenness(adjacency, False)
    weighted = _betweenness(adjacency, True)
    rank, convergence = _pagerank(adjacency)
    groups = _communities(adjacency, community_method)
    membership = {p: person_token(group[0]) for group in groups for p in group}
    nodes = [
        {
            **person_json(p, identities),
            "activity": exact(activities[p]),
            "degree": len(adjacency[p]),
            "strength": exact(sum(adjacency[p].values(), Fraction(0))),
            "betweenness_unweighted": number(unweighted[p]),
            "betweenness_weighted": number(weighted[p]),
            "pagerank": number(rank[p]),
            "community_id": membership[p],
        }
        for p in people
    ]
    return finish(
        {
            "nodes": nodes,
            "edges": edges,
            "unplottable": [
                {
                    **person_json(p, identities),
                    "activity": exact(activities[p]),
                    "reason": "ambiguous_identity",
                }
                for p in sorted(identities)
                if not eligible(p)
            ],
            "communities": [
                {"community_id": person_token(g[0]), "members": [person_token(p) for p in g]}
                for g in groups
            ],
            "coverage": {
                "units": len(units),
                "records": len(records),
                "ambiguous_people": sum(not eligible(p) for p in identities),
                "missing_inventor_units": contributions.missing_inventor_units,
                "excluded_pair_weight": exact(
                    sum(
                        (w for pair, w in contributions.pairs if not all(map(eligible, pair))),
                        Fraction(0),
                    )
                ),
                "excluded_person_weight": exact(
                    sum((w for p, w in contributions.people if not eligible(p)), Fraction(0))
                ),
            },
            "basis": {
                "unit": units[0].unit if units else None,
                "person_weight": person_weight,
                "pair_weight": pair_weight,
                "community_method": community_method,
                "metrics_scope": "full_graph",
                "distance": "reciprocal_strength",
                "precision": 12,
                "pagerank_alpha": 0.85,
                "pagerank_l1_tolerance": 1e-12,
                "pagerank_max_iterations": 1000,
                "algorithm_version": "inventor_graph.v1",
            },
            "pagerank_convergence": convergence,
        }
    )


def ego_network(graph, *, focus, hops=1):
    """Extract 1/2/3-hop evidence; retain M01 GLOBAL metrics including isolates.

    Accepts this module's closed graph result, not an arbitrary persisted graph.
    Caller must validate persisted results before invoking this helper.
    """
    if (
        not isinstance(focus, tuple)
        or len(focus) != 2
        or not eligible(focus)
        or type(hops) is not int
        or hops not in {1, 2, 3}
    ):
        invalid()
    token = person_token(focus)
    adjacency = {n["person_token"]: set() for n in graph["nodes"]}
    if token not in adjacency:
        invalid()
    for edge in graph["edges"]:
        adjacency[edge["source"]].add(edge["target"])
        adjacency[edge["target"]].add(edge["source"])
    distances = {token: 0}
    for depth in range(1, hops + 1):
        frontier = sorted(p for p, d in distances.items() if d == depth - 1)
        for p in frontier:
            for q in sorted(adjacency[p]):
                distances.setdefault(q, depth)
    nodes = [n for n in graph["nodes"] if n["person_token"] in distances]
    edges = [e for e in graph["edges"] if e["source"] in distances and e["target"] in distances]
    partners = [
        {
            "person_token": e["target"] if e["source"] == token else e["source"],
            "weight": e["weight"],
            "unit_ids": e["unit_ids"],
            "record_ids": e["record_ids"],
            "first_observation": e["first_observation"],
            "last_observation": e["last_observation"],
            "missing_date_records": e["missing_date_records"],
            "classifications": e["classifications"],
        }
        for e in graph["edges"]
        if token in (e["source"], e["target"])
    ]
    return finish(
        {
            "focus": list(focus),
            "hops": hops,
            "nodes": nodes,
            "edges": edges,
            "hop_membership": [
                {"person_token": n["person_token"], "hop": distances[n["person_token"]]}
                for n in nodes
            ],
            "partners": sorted(partners, key=lambda p: token_order(p["person_token"])),
            "basis": graph["basis"],
            "coverage": graph["coverage"],
            "unplottable": graph["unplottable"],
            "omitted_nodes": len(graph["nodes"]) - len(nodes),
            "omitted_edges": len(graph["edges"]) - len(edges),
        }
    )
