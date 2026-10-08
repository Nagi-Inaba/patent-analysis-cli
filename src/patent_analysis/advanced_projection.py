"""Pure, bounded presentation projections; aggregation remains in the analysis core.

Input data must first pass the matching native result schema. This module does
not parse CSVs, resolve columns or classify owners. Derived values are checked
against their supplied operands before projection; they are never silently fixed.
"""

from __future__ import annotations

from typing import Any

from patent_analysis.advanced_presentation import get_advanced_presentation


def _index(labels: list[str]) -> dict[str, int]:
    if len(labels) != len(set(labels)):
        raise ValueError("presentation axis identities must be unique")
    return {label: index for index, label in enumerate(labels)}


def _point(
    identity: int, label: str, x: float, y: float, size: float, category: str
) -> dict[str, Any]:
    return {"id": str(identity), "label": label, "x": x, "y": y, "size": size, "category": category}


def _check_quadrant_total(data: dict[str, Any], point: dict[str, Any]) -> None:
    """The four half-span counts and their union must admit one row population."""
    periods: list[tuple[int, int, int]] = []
    for side in ("long", "short"):
        span, counts = data[f"{side}_span"], point[side]
        start, end = span["start_year"], span["end_year"] + 1
        middle = (span["start_year"] + span["end_year"]) // 2 + 1
        periods.extend(((start, middle, counts["previous"]), (middle, end, counts["recent"])))
    boundaries = sorted({year for start, end, _ in periods for year in (start, end)})
    positions = {year: index for index, year in enumerate(boundaries)}
    # At most six prefix-count boundaries. Paired inequalities fix each supplied
    # count; monotone prefixes require nonnegative integer counts between them.
    edges: list[tuple[int, int, int]] = []
    for start, end, count in [*periods, (boundaries[0], boundaries[-1], point["total_count"])]:
        a, b = positions[start], positions[end]
        edges.extend(((a, b, count), (b, a, -count)))
    for i, (left, right) in enumerate(zip(boundaries, boundaries[1:], strict=False)):
        edges.append((i + 1, i, 0))
        if not any(start <= left and right <= end for start, end, _ in periods):
            edges.append((i, i + 1, 0))  # A gap outside both spans contributes zero.
    # A negative cycle means these closed, integer count equalities contradict
    # one another. Do not invent an overlap count or silently repair the total.
    prefixes = [0] * len(boundaries)
    for _ in boundaries:
        changed = False
        for a, b, amount in edges:
            if prefixes[b] > prefixes[a] + amount:
                prefixes[b] = prefixes[a] + amount
                changed = True
        if not changed:
            return
    raise ValueError("Growth total or half-span counts are inconsistent")


def _check_entrant_memberships(data: dict[str, Any]) -> None:
    applicants = {a["label"]: a["classification_memberships"] for a in data["applicants"]}
    if len(applicants) != len(data["applicants"]):
        raise ValueError("Duplicate entrant identity")
    subtotals = dict.fromkeys(applicants, 0)
    for cell in data["cells"]:
        applicant = cell["applicant"]
        if applicant not in applicants:
            raise ValueError("Unknown entrant identity")
        denominator = applicants[applicant]
        count = cell["count"]
        expected_share = count / denominator if denominator else 0.0
        if count > denominator or abs(cell["share"] - expected_share) > 1e-10:
            raise ValueError("Entrant cell contradicts its membership total")
        subtotals[applicant] += count
        if subtotals[applicant] > denominator:
            raise ValueError("Entrant subtotal exceeds its membership total")


def _check_cooccurrence_operands(data: dict[str, Any]) -> None:
    labels = _index(list(data["labels"]))
    counts = {item["label"]: item["count"] for item in data["label_counts"]}
    if len(counts) != len(data["label_counts"]) or set(counts) != set(labels):
        raise ValueError("Cooccurrence label counts must match the axes")
    pairs: dict[tuple[str, str], int] = {}
    for pair in data["pairs"]:
        a, b, count = pair["source"], pair["target"], pair["count"]
        if a not in counts or b not in counts or a == b:
            raise ValueError("Invalid cooccurrence pair identity")
        key = tuple(sorted((a, b)))
        if key in pairs or count > min(counts[a], counts[b]):
            raise ValueError("Cooccurrence pair contradicts label counts")
        pairs[key] = count
    if len(data["cells"]) != len(labels) ** 2:
        raise ValueError("Cooccurrence requires every axis pair")
    for cell in data["cells"]:
        a, b, count = cell["x"], cell["y"], cell["count"]
        if a not in counts or b not in counts:
            raise ValueError("Unknown cooccurrence cell identity")
        expected = 0 if a == b else pairs.get(tuple(sorted((a, b))), 0)
        if count != expected or count > min(counts[a], counts[b]):
            raise ValueError("Cooccurrence cell contradicts its pair or label counts")


def project_advanced_data(analysis_id: str, data: dict[str, Any]) -> dict[str, Any]:
    definition = get_advanced_presentation(analysis_id)
    if data.get("analysis_id") != analysis_id:
        raise ValueError("presentation data has a different analysis identity")
    if analysis_id == "inventor-tracking.v1":
        from patent_analysis.inventor_tracking_projection import project_tracking
        return project_tracking(data)
    if analysis_id == "growth-quadrant.v1":
        for span in (data["long_span"], data["short_span"]):
            if span["start_year"] >= span["end_year"]:
                raise ValueError("Growth span endpoints must be ordered")
        measured, omitted = [], []
        for index, point in enumerate(data["points"]):
            for side in ("long", "short"):
                counts = point[side]
                previous, recent = counts["previous"], counts["recent"]
                expected_rate = (
                    (recent - previous) / previous * 100 if previous else None if recent else 0.0
                )
                expected_state = "measured" if previous else "new" if recent else "empty"
                if counts["rate_percent"] != expected_rate or counts["state"] != expected_state:
                    raise ValueError("Growth rate or state contradicts its counts")
            _check_quadrant_total(data, point)
            x, y = point["long"]["rate_percent"], point["short"]["rate_percent"]
            expected_quadrant = (
                "new"
                if x is None or y is None
                else (
                    "sustained_growth"
                    if x >= 0 and y >= 0
                    else "recovery"
                    if x < 0 <= y
                    else "slowing"
                    if y < 0 <= x
                    else "decline"
                )
            )
            if point["quadrant"] != expected_quadrant:
                raise ValueError("Growth quadrant contradicts its rates")
            if x is None or y is None:
                omitted.append(
                    {
                        "label": point["label"],
                        "long_state": point["long"]["state"],
                        "short_state": point["short"]["state"],
                        "count": point["total_count"],
                    }
                )
            else:
                measured.append(
                    _point(index, point["label"], x, y, point["total_count"], point["quadrant"])
                )
        a, b = data["long_span"], data["short_span"]
        return {
            "kind": "quadrant",
            "x_label": "長期増減率（%）",
            "y_label": "短期増減率（%）",
            "size_label": "対象期間の件数",
            "points": measured,
            "unplottable": omitted,
            "context": (
                f"長期 {a['start_year']}–{a['end_year']} / "
                f"短期 {b['start_year']}–{b['end_year']}。"
                "期間の前半・後半の件数比較。年率ではありません。"
            ),
        }
    if analysis_id == "entry-exit.v1":
        cutoff, as_of = data["active_since_year"], data["as_of_year"]
        if as_of is None:
            if cutoff is not None or data["points"]:
                raise ValueError("Entry activity cutoff is inconsistent")
        elif cutoff != as_of - 2:
            raise ValueError("Entry activity cutoff is inconsistent")
        for point in data["points"]:
            if not point["first_year"] <= point["last_year"] <= as_of:
                raise ValueError("Entry observation years are inconsistent")
            if point["active_recent"] is not (point["last_year"] >= cutoff):
                raise ValueError("Entry activity flag contradicts its cutoff")
        points = [
            _point(
                i,
                p["label"],
                p["first_year"],
                p["last_year"],
                p["count"],
                "active" if p["active_recent"] else "inactive",
            )
            for i, p in enumerate(data["points"])
        ]
        active_since = data["active_since_year"]
        return {
            "kind": "scatter",
            "x_label": "初回観測年",
            "y_label": "最終観測年",
            "size_label": "件数",
            "x_year": True,
            "y_year": True,
            "points": points,
            "context": (
                "直近活動の基準年: "
                f"{active_since if active_since is not None else '対象なし'}"
                "。観測範囲の記述であり、市場撤退の判定ではありません。"
            ),
        }
    if analysis_id == "citation.v1":
        return {
            "kind": "scatter",
            "x_label": "観測年",
            "y_label": "被引用件数",
            "size_label": "被引用件数",
            "x_year": True,
            "y_year": False,
            "points": [
                _point(
                    p["point_id"],
                    p["label"],
                    p["year"],
                    p["citation_value"],
                    p["citation_value"],
                    "citation",
                )
                for p in data["points"]
            ],
            "context": (
                "レコード単位。同じ表示名でも別レコードとして保持。"
                "被引用0件は最小の点で表示。"
            ),
        }
    if analysis_id == "matrix-composition.v1":
        denominator = data["category_memberships"]
        if any(item["count"] > data["cell_rows"] for item in data["items"]):
            raise ValueError("Composition category count exceeds selected rows")
        if sum(item["count"] for item in data["items"]) > denominator:
            raise ValueError("Composition counts exceed the membership denominator")
        if sum(item["share"] for item in data["items"]) > 1 + 1e-10:
            raise ValueError("Composition shares exceed the full population")
        return {
            "kind": "bars",
            "value_label": "カテゴリ所属件数",
            "items": [
                {
                    "label": p["label"],
                    "value": p["count"],
                    "denominator": denominator,
                    "share": p["share"],
                    "record_count": data["cell_rows"],
                    "involvement_count": None,
                }
                for p in data["items"]
            ],
            "context": (
                f"選択セル {data['cell']['x']} × {data['cell']['y']} / "
                f"分母: 全カテゴリ所属 {denominator} 件。上位表示外も分母に含みます。"
            ),
        }
    if analysis_id in {"new-entrants.v1", "compara.v1", "cooccurrence.v1"}:
        if analysis_id == "new-entrants.v1":
            if any(a["first_year"] < data["as_of_year"] for a in data["applicants"]):
                raise ValueError("New entrant predates the first-observation cutoff")
            _check_entrant_memberships(data)
            xs, ys = list(data["classifications"]), [a["label"] for a in data["applicants"]]
            cells = [
                (c["classification"], c["applicant"], c["count"], c["share"]) for c in data["cells"]
            ]
            context = (
                f"初回観測年が {data['as_of_year']} 年以降の出願人。"
                "割合の分母は各出願人の全分類所属件数。"
            )
            x_label, y_label, signed = "分類", "出願人", False
        elif analysis_id == "compara.v1":
            for cell in data["cells"]:
                if cell["difference"] != cell["a_count"] - cell["b_count"]:
                    raise ValueError("Compara difference must equal a_count minus b_count")
            xs, ys = list(data["x"]), list(data["y"])
            cells = [(c["x"], c["y"], c["difference"], None) for c in data["cells"]]
            context = (
                f"差分 = {data['groups']['a']} − {data['groups']['b']}。"
                "同じレコードが両群に属する場合は各群に1件。"
            )
            x_label, y_label, signed = "横軸カテゴリ", "縦軸カテゴリ", True
        else:
            _check_cooccurrence_operands(data)
            xs, ys = list(data["labels"]), list(data["labels"])
            cells = [(c["x"], c["y"], c["count"], None) for c in data["cells"]]
            context = "同一レコード内の異なる項目の組合せ。対称行列で、対角成分は0です。"
            x_label, y_label, signed = "項目", "項目", False
        xi, yi = _index(xs), _index(ys)
        if analysis_id == "compara.v1" and len(cells) != len(xs) * len(ys):
            raise ValueError("Compara requires a value for every axis pair")
        occupied: set[tuple[int, int]] = set()
        projected = []
        for x, y, value, share in cells:
            if x not in xi or y not in yi or (xi[x], yi[y]) in occupied:
                raise ValueError("invalid presentation cell identity")
            occupied.add((xi[x], yi[y]))
            projected.append({"x": xi[x], "y": yi[y], "value": value, "share": share})
        return {
            "kind": "heatmap",
            "x": xs,
            "y": ys,
            "x_label": x_label,
            "y_label": y_label,
            "signed": signed,
            "cells": projected,
            "context": context,
        }
    if analysis_id == "collaboration-network.v1":
        nodes = [{"label": n["label"], "value": n["count"]} for n in data["nodes"]]
        positions = _index([n["label"] for n in nodes])
        edges = []
        occupied = set()
        for edge in data["edges"]:
            source, target = edge["source"], edge["target"]
            if source not in positions or target not in positions or source == target:
                raise ValueError("invalid presentation edge identity")
            if edge["count"] > min(
                nodes[positions[source]]["value"], nodes[positions[target]]["value"]
            ):
                raise ValueError("Collaboration edge exceeds an endpoint count")
            pair = tuple(sorted((positions[source], positions[target])))
            if pair in occupied:
                raise ValueError("duplicate presentation edge")
            occupied.add(pair)
            edges.append(
                {"source": positions[source], "target": positions[target], "value": edge["count"]}
            )
        return {
            "kind": "network",
            "nodes": nodes,
            "edges": edges,
            "context": (
                "共同レコードのみを計数。固定円周配置は関係の強弱や距離を表しません。"
                "線は共同件数。"
            ),
        }
    if analysis_id in {"uniqueness.v1", "shared-involvement.v1"}:
        unique = analysis_id == "uniqueness.v1"
        count_key, rate_key = (
            ("unique_item_count", "uniqueness_rate")
            if unique
            else ("shared_item_count", "shared_rate")
        )
        return {
            "kind": "bars",
            "value_label": "固有項目数" if unique else "共有項目数",
            "items": [
                {
                    "label": p["group"],
                    "value": p[count_key],
                    "denominator": p["total_item_count"],
                    "share": p[rate_key],
                    "record_count": p["record_count"],
                    "involvement_count": p.get("involvement_record_count"),
                }
                for p in data["groups"]
            ],
            "context": "全母集団で所属を判定。上位表示で所有者・割合の分母は変わりません。"
            if unique
            else (
                f"{data['min_groups']} グループ以上に属する項目。"
                "関与件数は同一レコード内で二重計上しません。"
            ),
        }
    raise ValueError(f"unsupported presentation kind: {definition.kind}")
