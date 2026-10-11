"""Semantic checks for the closed inventor renderer DTOs.

Shapes, finite ranges and caps are enforced by the packaged JSON schemas first.
These checks mirror the renderer's relational invariants, not analytical kernels.
"""

from __future__ import annotations


def _invalid():
    raise ValueError("inventor presentation operands are inconsistent")


def _unique(ids):
    if len(ids) != len(set(ids)):
        _invalid()


def _edges(edges, count, *, directed=False):
    ordered, pairs = set(), {}
    for e in edges:
        a, b = e["source"], e["target"]
        if (
            type(a) is not int
            or type(b) is not int
            or not 0 <= a < count
            or not 0 <= b < count
            or a == b
        ):
            _invalid()
        pair = tuple(sorted((a, b)))
        is_directed = directed and e["directed"]
        if not is_directed:
            if pair in pairs:
                _invalid()
            pairs[pair] = False
        else:
            if (a, b) in ordered or pairs.get(pair) is False:
                _invalid()
            ordered.add((a, b))
            pairs[pair] = True


def _calendar(years):
    if years and years != list(range(years[0], years[-1] + 1)):
        _invalid()


def validate_inventor_projection(analysis_id, p):
    if p["kind"] == "inventor-network":
        _unique([n["id"] for n in p["nodes"]])
        if p["focus"] is not None and p["focus"] not in {n["id"] for n in p["nodes"]}:
            _invalid()
        if analysis_id == "inventor-ego-network.v1" and p["focus"] is None:
            _invalid()
        if analysis_id == "inventor-mobility-flow.v1" and any(
            not e["directed"] for e in p["edges"]
        ):
            _invalid()
        _edges(p["edges"], len(p["nodes"]), directed=True)
    elif p["kind"] == "inventor-timeline":
        _calendar(p["years"])
        _unique([n["id"] for n in p["nodes"]])
        _unique([b["id"] for b in p["bands"]])
        if (p["nodes"] or p["bands"]) and not p["years"]:
            _invalid()
        first, end = (p["years"][0], p["years"][-1] + 1) if p["years"] else (0, 0)
        if any(not 0 <= n["y"] < len(p["lanes"]) or not first <= n["x"] <= end for n in p["nodes"]):
            _invalid()
        if any(not first <= b["start"] <= b["end"] <= end for b in p["bands"]):
            _invalid()
        _edges(p["links"], len(p["nodes"]))
    elif p["kind"] == "inventor-alluvial":
        _calendar(p["years"])
        _unique([n["id"] for n in p["nodes"]])
        if any(n["year"] not in p["years"] for n in p["nodes"]):
            _invalid()
        _edges(p["links"], len(p["nodes"]))
        incoming, outgoing = [0] * len(p["nodes"]), [0] * len(p["nodes"])
        for e in p["links"]:
            a, b = p["nodes"][e["source"]], p["nodes"][e["target"]]
            span = b["year"] - a["year"]
            if span <= 0:
                _invalid()
            if e["kind"] == "newly_observed":
                if a["kind"] != "newly_observed" or b["kind"] != "cluster":
                    _invalid()
            elif e["kind"] == "not_observed":
                if a["kind"] != "cluster" or b["kind"] != "not_observed":
                    _invalid()
            elif (
                a["kind"] != "cluster"
                or b["kind"] != "cluster"
                or (span < 2 if e["kind"] == "gap" else span != 1)
            ):
                _invalid()
            outgoing[e["source"]] += e["value"]
            incoming[e["target"]] += e["value"]
        if any(
            incoming[i] > n["members"] or outgoing[i] > n["members"]
            for i, n in enumerate(p["nodes"])
        ):
            _invalid()
    elif p["kind"] == "inventor-scatter":
        _unique([n["id"] for n in p["points"] + p["unplottable"]])
        _edges(p["edges"], len(p["points"]))
    elif p["kind"] == "inventor-heatmap":
        pairs = [(c["x"], c["y"]) for c in p["cells"]]
        if len(pairs) != len(set(pairs)) or set(pairs) != {
            (x, y) for x in range(len(p["x"])) for y in range(len(p["y"]))
        }:
            _invalid()
