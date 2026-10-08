"""Validated, fixed calendar/swimlane presentation of inventor tracking aggregates."""

from __future__ import annotations

import unicodedata
from collections import defaultdict

from patent_analysis._render_text import graphemes, validate_safe_text
from patent_analysis.analyses.inventor_tracking import (
    MAX_INVENTORS,
    MAX_YEAR_SPAN,
    relationships,
)


def _applicant_label(values):
    # Check the complete source text before shortening the display-only label.
    full = " / ".join(values)
    validate_safe_text(full)
    if unicodedata.normalize("NFC", full) != full:
        raise ValueError("render text must be NFC")
    parts, size = [], 0
    for part in graphemes(full):
        if len(parts) >= 27 or size + len(part) > 256:
            return "".join(parts) + "…"
        parts.append(part)
        size += len(part)
    return "".join(parts)


def project_tracking(data):
    observations = data["observations"]
    keys = [(o["year"], o["inventor"]) for o in observations]
    names = sorted({name for _, name in keys})
    years = sorted({year for year, _ in keys})
    if (
        keys != sorted(set(keys))
        or len(names) > MAX_INVENTORS
        or (years and years[-1] - years[0] >= MAX_YEAR_SPAN)
        or years != data["years"]
    ):
        raise ValueError("inconsistent tracking identities or years")
    indexed = dict(zip(keys, observations, strict=True))
    summary = [
        {
            "inventor": name,
            "count": sum(o["count"] for o in observations if o["inventor"] == name),
            "first_year": min(y for y, a in keys if a == name),
            "last_year": max(y for y, a in keys if a == name),
        }
        for name in names
    ]
    if data["inventors"] != summary:
        raise ValueError("inconsistent tracking summary")
    associations, occupied = defaultdict(list), set()
    for a in data["affiliations"]:
        key = a["year"], a["inventor"]
        unique = (*key, a["applicant"])
        o = indexed.get(key)
        if (
            o is None
            or unique in occupied
            or not 1 <= a["count"] <= o["count"] - o["missing_applicant_rows"]
        ):
            raise ValueError("invalid tracking association")
        occupied.add(unique)
        associations[key].append(a["applicant"])
    total = sum(o["count"] for o in observations)
    visible = data["population"]["visible_rows"]
    if (
        bool(visible) != bool(observations)
        or total < visible
        or any(o["count"] > visible for o in observations)
    ):
        raise ValueError("tracking population is inconsistent")
    for key, o in indexed.items():
        if (
            not 0 <= o["missing_applicant_rows"] <= o["count"]
            or o["applicants"] != sorted(associations[key])
            or bool(o["applicants"]) != (o["missing_applicant_rows"] < o["count"])
        ):
            raise ValueError("inconsistent tracking applicant coverage")
    occupied = set()
    for edge in data["co_inventions"]:
        year, a, b = edge["year"], edge["source"], edge["target"]
        if (
            (year, a) not in indexed
            or (year, b) not in indexed
            or a >= b
            or (year, a, b) in occupied
            or not 1 <= edge["count"] <= min(indexed[year, a]["count"], indexed[year, b]["count"])
        ):
            raise ValueError("invalid tracking co-invention")
        occupied.add((year, a, b))
    expected_contributions = (
        total
        + sum(e["count"] for e in data["co_inventions"])
        + sum(a["count"] for a in data["affiliations"])
    )
    if data["contributions"] != expected_contributions:
        raise ValueError("inconsistent tracking contributions")
    clusters, membership, links, changes = relationships(observations, data["co_inventions"])
    if (
        clusters != data["clusters"]
        or links != data["cluster_links"]
        or changes != data["affiliation_changes"]
        or any(o["cluster_id"] != membership[key] for key, o in indexed.items())
    ):
        raise ValueError("inconsistent tracking relationships")
    calendar = list(range(years[0], years[-1] + 1)) if years else []
    positions = {key: index for index, key in enumerate(keys)}
    statuses = {(c["to_year"], c["inventor"]): c["status"] for c in changes}
    return {
        "kind": "tracking",
        "years": calendar,
        "inventors": names,
        "nodes": [
            {
                "x": calendar.index(y),
                "y": names.index(a),
                "cluster": int(o["cluster_id"].split(":")[1]) - 1,
                "count": o["count"],
                "applicants": _applicant_label(o["applicants"]),
                "changed": statuses.get((y, a)) == "changed",
                "unknown": bool(o["missing_applicant_rows"]) or statuses.get((y, a)) == "unknown",
            }
            for (y, a), o in indexed.items()
        ],
        "links": [
            {
                "source": positions[c["from_year"], c["inventor"]],
                "target": positions[c["to_year"], c["inventor"]],
                "gap": c["gap_years"] > 0,
            }
            for c in changes
        ],
        "context": (
            "色とC番号: 同一年の共発明クラスタ / ◇: 出願人の変化 / "
            "白抜き: 比較不明 / 破線: 未観測年あり"
        ),
    }
