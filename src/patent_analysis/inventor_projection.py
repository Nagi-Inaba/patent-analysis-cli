"""Display-only inventor projections; original opaque IDs/metrics stay neutral.

Generated view IDs hash exact identity tokens without normalizing them. Display
labels alone are NFC/shortened. Fixed circle distances have no analytical meaning.
"""

from __future__ import annotations

import hashlib
import math
import unicodedata
from fractions import Fraction

from patent_analysis._render_text import graphemes, validate_safe_text
from patent_analysis.inventor_numeric import PRECISION, number, person_token

MAX_NODES = 40
MAX_EDGES = 300


def _invalid():
    raise ValueError("inventor presentation operands are inconsistent")


def _value(cell):
    if not isinstance(cell, dict) or set(cell) != {"value", "numerator", "denominator"}:
        _invalid()
    try:
        n, d = int(cell["numerator"]), int(cell["denominator"])
        if str(n) != cell["numerator"] or str(d) != cell["denominator"] or n < 0 or d <= 0:
            _invalid()
        exact = Fraction(n, d)
        if type(cell["value"]) not in {int, float} or cell["value"] != number(exact):
            _invalid()
    except (TypeError, ValueError, OverflowError):
        _invalid()
    return exact


def _view_id(token):
    if not isinstance(token, str):
        _invalid()
    return "view:" + hashlib.sha256(token.encode("utf-8")).hexdigest()


def _label(value):
    # Normalize only a separate DISPLAY label, never the underlying ID/token.
    text = unicodedata.normalize("NFC", validate_safe_text(value))
    out = []
    byte_count = 0
    for cluster in graphemes(text):
        size = len(cluster.encode("utf-8"))
        if len(out) == 27 or byte_count + size > 240:
            return "".join(out) + "…" if out else "（表示ラベル省略）"
        out.append(cluster)
        byte_count += size
    return "".join(out)


def _network(statistics, *, ego=False):
    original = statistics["nodes"]
    tokens = [n["person_token"] for n in original]
    if len(tokens) != len(set(tokens)) or len(tokens) > 200:
        _invalid()
    identities = {n["person_token"]: n for n in original}
    for node in original:
        if node["person_token"] != person_token(tuple(node["person_key"])):
            _invalid()
        _value(node["activity"])
        _value(node["strength"])
    occupied = set()
    adjacency = {token: set() for token in tokens}
    strengths = dict.fromkeys(tokens, Fraction(0))
    for edge in statistics["edges"]:
        a, b = edge["source"], edge["target"]
        pair = tuple(sorted((a, b)))
        if a not in identities or b not in identities or a == b or pair in occupied:
            _invalid()
        occupied.add(pair)
        weight = _value(edge["weight"])
        if not weight:
            _invalid()
        adjacency[a].add(b)
        adjacency[b].add(a)
        strengths[a] += weight
        strengths[b] += weight
    if any(
        (
            n["degree"] < len(adjacency[n["person_token"]])
            or _value(n["strength"]) < strengths[n["person_token"]]
        )
        if ego
        else (
            n["degree"] != len(adjacency[n["person_token"]])
            or _value(n["strength"]) != strengths[n["person_token"]]
        )
        for n in original
    ):
        _invalid()
    if (
        not ego
        and original
        and abs(math.fsum(n["pagerank"] for n in original) - 1) > (len(original) * 0.5e-12 + 1e-12)
    ):
        _invalid()
    focus_token = person_token(tuple(statistics["focus"])) if ego else None
    hops = {}
    if ego:
        if focus_token not in identities or statistics["hops"] not in (1, 2, 3):
            _invalid()
        hops[focus_token] = 0
        for depth in range(1, statistics["hops"] + 1):
            for token in sorted(t for t, d in hops.items() if d == depth - 1):
                for partner in sorted(adjacency[token]):
                    hops.setdefault(partner, depth)
        supplied = statistics["hop_membership"]
        if (
            len(supplied) != len(hops)
            or set(hops) != set(tokens)
            or {h["person_token"]: h["hop"] for h in supplied} != hops
        ):
            _invalid()
    ordered = sorted(original, key=lambda n: (-_value(n["activity"]), n["person_token"]))
    if ego:
        ordered = sorted(
            ordered,
            key=lambda n: (hops[n["person_token"]], -_value(n["activity"]), n["person_token"]),
        )
    selected = ordered[:MAX_NODES]
    # Layout/indices are stable exact-token order, NOT force layout or metric distances.
    selected = sorted(selected, key=lambda n: n["person_token"])
    positions = {n["person_token"]: i for i, n in enumerate(selected)}
    groups = {g: i for i, g in enumerate(sorted({n["community_id"] for n in original}))}
    count = len(selected)
    nodes = [
        {
            "id": _view_id(n["person_token"]),
            "label": _label(n["display_name"]),
            "x": number(math.cos(2 * math.pi * i / count)),
            "y": number(math.sin(2 * math.pi * i / count)),
            "value": number(_value(n["activity"])),
            "group": groups[n["community_id"]],
            "hop": hops[n["person_token"]] if ego else None,
        }
        for i, n in enumerate(selected)
    ]
    edges = sorted(
        (e for e in statistics["edges"] if e["source"] in positions and e["target"] in positions),
        key=lambda e: (-_value(e["weight"]), e["source"], e["target"]),
    )[:MAX_EDGES]
    return {
        "kind": "inventor-network",
        "nodes": nodes,
        "edges": [
            {
                "source": positions[e["source"]],
                "target": positions[e["target"]],
                "value": number(_value(e["weight"])),
                "directed": False,
                "state": "observed",
            }
            for e in edges
        ],
        "focus": _view_id(focus_token) if ego else None,
        "context": (
            f"全体指標は表示選別前に算出。表示 {len(nodes)}/{len(original)} 人、"
            f"{len(edges)}/{len(statistics['edges'])} 辺。"
            "固定円周配置の距離は類似度・関係の強さを表しません。"
            "色はこの図の協働カテゴリで、部署の確認ではありません。"
            "大きさは活動寄与、線は観測ペア重み。表示名のみNFC・短縮。"
        ),
    }


def _people(rows):
    mapped = {}
    for row in rows:
        token = row["person_token"]
        if token in mapped or token != person_token(tuple(row["person_key"])):
            _invalid()
        mapped[token] = row
    return mapped


def _technology(stats):
    people = _people(stats["profiles"])
    columns = {tuple(c["classification"]): c for c in stats["classifications"]}
    if len(columns) != len(stats["classifications"]):
        _invalid()
    mass = _value(stats["coverage"]["classification_mass"])
    if stats["cells"] and not mass:
        _invalid()
    totals = dict.fromkeys(columns, Fraction(0))
    person_totals = dict.fromkeys(people, Fraction(0))
    cells = {}
    for c in stats["cells"]:
        p, code = c["person_token"], tuple(c["classification"])
        if p not in people or code not in columns or (p, code) in cells:
            _invalid()
        count = _value(c["count"])
        denominator = _value(people[p]["classification_total"])
        reference = columns[code]["reference_share"]
        if (
            not denominator
            or c["share"] != number(count / denominator)
            or reference is None
            or not reference
            or c["relative_specialization"]
            != number(count / denominator / (_value(columns[code]["count"]) / mass))
        ):
            _invalid()
        cells[p, code] = c["share"]
        totals[code] += count
        person_totals[p] += count
    if sum(totals.values(), Fraction(0)) != mass:
        _invalid()
    for code, c in columns.items():
        if _value(c["count"]) != totals[code] or c["reference_share"] != (
            number(totals[code] / mass) if mass else None
        ):
            _invalid()
    for p, row in people.items():
        if _value(row["classification_total"]) != person_totals[p] or bool(
            row["undefined_reason"]
        ) != (person_totals[p] == 0):
            _invalid()
    selected = list(people)[:12]
    codes = list(columns)[:12]
    return {
        "kind": "inventor-heatmap",
        "x": [_label(":".join(c)) for c in codes],
        "y": [_label(people[p]["display_name"]) for p in selected],
        "x_label": "技術分野",
        "y_label": "発明者",
        "value_label": "構成比 (0–1)",
        "cells": [
            {"x": x, "y": y, "value": None if not person_totals[p] else cells.get((p, c), 0)}
            for y, p in enumerate(selected)
            for x, c in enumerate(codes)
        ],
        "context": (
            f"表示 {len(selected)}/{len(people)} 人・{len(codes)}/{len(columns)} 分類。"
            "省略は表示のみ。構成比の分母と専門性の参照母集団は全統計。"
            "分類なしは不明、分類が既知の人物の非該当セルは0。氏名は本人確認ではない。"
        ),
    }


def _calendar(rows):
    years = [r["year"] for r in rows]
    if years and (years != list(range(years[0], years[-1] + 1)) or len(years) > 30):
        _invalid()
    return years


def _activity(stats):
    people = _people(stats["people"])
    years = _calendar(stats["calendar"])
    selected = list(people)[:12]
    lanes = {p: i for i, p in enumerate(selected)}
    occupied = set()
    nodes = []
    groups = {
        g: i
        for i, g in enumerate(
            sorted(
                {r["community_id"] for r in stats["observations"] if r["community_id"] is not None}
            )
        )
    }
    for r in stats["observations"]:
        p, year = r["person_token"], r["year"]
        if p not in people or year not in years or (p, year) in occupied:
            _invalid()
        occupied.add((p, year))
        if r["observed"]:
            size = number(_value(r["activity"]))
            if r["unit_count"] != len(r["unit_ids"]) or not r["unit_count"]:
                _invalid()
        else:
            if r["activity"] is not None or r["unit_count"] is not None or r["unit_ids"]:
                _invalid()
            size = 0  # Unknown glyph size only, NOT an analytical zero.
        if p in lanes:
            nodes.append(
                {
                    "id": _view_id(p + ":" + str(year)),
                    "x": year,
                    "y": lanes[p],
                    "size": size,
                    "category": groups.get(r["community_id"], 0),
                    "label": _label(
                        f"{year} 観測 {r['unit_count']}"
                        if r["observed"]
                        else f"{year} 未観測・活動不明"
                    ),
                    "state": "observed" if r["observed"] else "unknown",
                }
            )
    nodes = nodes[:40]
    links = []
    for i, n in enumerate(nodes):
        for j, m in enumerate(nodes):
            if n["y"] == m["y"] and m["x"] == n["x"] + 1 and n["state"] == m["state"] == "observed":
                links.append({"source": i, "target": j, "gap": False, "state": "observed"})
    return {
        "kind": "inventor-timeline",
        "lanes": [_label(people[p]["display_name"]) for p in selected],
        "years": years,
        "nodes": nodes,
        "links": links,
        "bands": [],
        "context": (
            f"表示 {len(selected)}/{len(people)} 人・"
            f"{len(nodes)}/{len(stats['observations'])} 観測。"
            f"日付欠損 {len(stats['missing_date_record_ids'])} 件は年を補完しない。"
            "空白・未観測は活動0や退職を意味しない。年度間は観測の接続のみ。"
            "年内単位の在席観測と累積の重複なし単位数は異なる。省略は表示のみ。"
        ),
    }


def _alluvial(stats):
    years = _calendar(stats["calendar"])
    original = stats["nodes"]
    indexed = {n["node_id"]: n for n in original}
    if len(indexed) != len(original):
        _invalid()
    adjacency = {k: set() for k in indexed}
    incoming, outgoing = {}, {}
    seen = set()
    for n in original:
        if n["year"] not in years or n["size"] != len(set(n["members"])):
            _invalid()
    for e in stats["links"]:
        a, b = e["source"], e["target"]
        if a not in indexed or b not in indexed or a == b or (a, b) in seen:
            _invalid()
        seen.add((a, b))
        members = set(e["members"])
        if (
            not members
            or e["width"] != len(members)
            or not members <= set(indexed[a]["members"]) & set(indexed[b]["members"])
            or e["source_year"] != indexed[a]["year"]
            or e["target_year"] != indexed[b]["year"]
            or e["target_year"] - e["source_year"] not in (0, 1)
        ):
            _invalid()
        for key, table in [(a, outgoing), (b, incoming)]:
            if table.get(key, set()) & members:
                _invalid()
            table.setdefault(key, set()).update(members)
        adjacency[a].add(b)
        adjacency[b].add(a)
    for n in original:
        if n["kind"] == "cluster" and (
            incoming.get(n["node_id"], set()) != set(n["members"])
            or outgoing.get(n["node_id"], set()) != set(n["members"])
        ):
            _invalid()
    # Select WHOLE connected components, never change membership mass to fit a cap.
    selected, visited = set(), set()
    for key in indexed:
        if key in visited:
            continue
        component, pending = set(), [key]
        while pending:
            k = pending.pop()
            if k not in component:
                component.add(k)
                pending.extend(adjacency[k] - component)
        visited.update(component)
        proposed = selected | component
        edge_count = sum(
            e["source"] in proposed and e["target"] in proposed for e in stats["links"]
        )
        if len(proposed) <= 32 and edge_count <= 60:
            selected = proposed
    nodes = [
        n
        for n in original
        if n["node_id"] in selected and n["kind"] not in {"scope_entry", "scope_exit"}
    ]
    positions = {n["node_id"]: i for i, n in enumerate(nodes)}
    kinds = {"scope_entry": "newly_observed", "scope_exit": "not_observed"}
    links = []
    for e in stats["links"]:
        if e["source"] not in positions or e["target"] not in positions:
            continue
        source, target = indexed[e["source"]], indexed[e["target"]]
        kind = kinds.get(e["kind"], e["kind"])
        if kind == "shared_members":
            kind = "split" if source["split"] else ("merge" if target["merge"] else "continuation")
        links.append(
            {
                "source": positions[e["source"]],
                "target": positions[e["target"]],
                "value": e["width"],
                "kind": kind,
            }
        )
    return {
        "kind": "inventor-alluvial",
        "years": years,
        "nodes": [
            {
                "id": _view_id(n["node_id"]),
                "year": n["year"],
                "members": n["size"],
                "kind": kinds.get(n["kind"], n["kind"]),
                "label": _label(f"{n['year']} {kinds.get(n['kind'], n['kind'])} {n['size']}人"),
            }
            for n in nodes
        ],
        "links": links,
        "context": (
            f"表示 {len(nodes)}/{len(original)} 節点・{len(links)}/{len(stats['links'])} リンク。"
            "省略は表示のみ、完全な連結成分を選別し幅の保存を維持。"
            "幅は共通する観測人物数。部署・確率・雇用ではない。"
            "同年の範囲境界節点・リンクは表示省略（全統計には保存）。"
            "新規/未観測は入社/退職ではない。空年を跨ぐ継続は推測しない。"
        ),
    }


def _similarity(stats):
    from patent_analysis.inventor_numeric import project_features

    people = _people(stats["features"])
    profiles = _people(stats["profiles"])
    if people.keys() != profiles.keys():
        _invalid()
    pairs = set()
    for e in stats["similarities"]:
        a, b = e["source"], e["target"]
        pair = tuple(sorted((a, b)))
        if a not in people or b not in people or pair in pairs:
            _invalid()
        pairs.add(pair)
        va, vb = people[a]["values"], people[b]["values"]
        if len(va) != len(stats["classifications"]) or len(vb) != len(va):
            _invalid()
        na, nb = math.sqrt(math.fsum(v * v for v in va)), math.sqrt(math.fsum(v * v for v in vb))
        cosine = (
            None
            if (people[a]["undefined_reason"] or people[b]["undefined_reason"] or not na or not nb)
            else number(
                min(1, max(0, math.fsum(x * y for x, y in zip(va, vb, strict=True)) / (na * nb)))
            )
        )
        actual = e["cosine"]
        if cosine is None:
            if actual is not None:
                _invalid()
        else:
            if type(actual) not in {int, float} or not 0 <= actual <= 1:
                _invalid()
            # The kernel computes cosine BEFORE exporting rounded features.
            # Each coordinate has error <= half a decimal quantum; normalized
            # direction error is <= 2*L2(error)/norm(exported vector).
            quantum = 10.0**-PRECISION
            vector_error = math.sqrt(len(va)) * quantum / 2
            tolerance = (
                quantum + 2 * vector_error * (1 / na + 1 / nb) + 32 * len(va) * math.ulp(1.0)
            )
            if (a == b and actual != 1) or abs(actual - cosine) > tolerance:
                _invalid()
    if len(pairs) != len(people) * (len(people) + 1) // 2:
        _invalid()
    layout = project_features(stats["features"])  # FULL population before display pruning.
    plotted = [p for p in layout["points"] if p["raw_coordinates"] is not None]
    selected = plotted[:24]
    positions = {p["person_token"]: i for i, p in enumerate(selected)}
    points = [
        {
            "id": _view_id(p["person_token"]),
            "label": _label(people[p["person_token"]]["display_name"]),
            "x": p["raw_coordinates"][0] + p["display_offset"][0],
            "y": p["raw_coordinates"][1] + p["display_offset"][1],
            "size": number(_value(profiles[p["person_token"]]["activity"])),
            "category": "technology",
        }
        for p in selected
    ]
    undefined = [p for p in layout["points"] if p["raw_coordinates"] is None]
    unplottable = [
        {
            "id": _view_id(p["person_token"]),
            "label": _label(people[p["person_token"]]["display_name"]),
            "reason": _label(p["undefined_reason"]),
        }
        for p in undefined[:24]
    ]
    edges, seen = [], set()
    for e in stats["co_inventor_edges"]:
        a, b = e["source"], e["target"]
        pair = tuple(sorted((a, b)))
        if a not in people or b not in people or a == b or pair in seen:
            _invalid()
        seen.add(pair)
        value = number(_value(e["weight"]))
        if a in positions and b in positions and len(edges) < 60:
            edges.append({"source": positions[a], "target": positions[b], "value": value})
    return {
        "kind": "inventor-scatter",
        "x_label": "MDS 第1軸",
        "y_label": "MDS 第2軸",
        "size_label": "活動寄与",
        "points": points,
        "edges": edges,
        "unplottable": unplottable,
        "context": (
            f"表示 {len(points)}/{len(plotted)} 有効点・"
            f"未定義 {len(unplottable)}/{len(undefined)} 人・"
            f"共発明線 {len(edges)}/{len(stats['co_inventor_edges'])}。省略は表示のみ。"
            f"MDS=canonical_projector_classical_mds.v1、特徴={stats['basis']['feature']}、"
            f"stress={layout['distortion']['stress']}、保持エネルギー={layout['distortion']['retained_energy']}。"
            "全特徴からunit-vector chordの2次元近似。同座標のずれは表示のみ、"
            "stressと元類似度を変えない。未定義を原点/0へ置かない。本人確認ではない。"
        ),
    }


def _impact(stats):
    people = _people(stats["people"])
    units = {u["unit_id"]: u for u in stats["units"]}
    if len(units) != len(stats["units"]):
        _invalid()
    coverage = stats["coverage"]
    known = sum(u["citation_count"] is not None for u in units.values())
    zeros = sum(u["citation_count"] == 0 for u in units.values())
    if (
        coverage["units"] != len(units)
        or coverage["known_citation_units"] != known
        or coverage["missing_citation_units"] != len(units) - known
        or coverage["known_zero_units"] != zeros
        or _value(coverage["unit_citation_sum"])
        != sum(u["citation_count"] for u in units.values() if u["citation_count"] is not None)
    ):
        _invalid()
    for p in people.values():
        activity, denominator = _value(p["activity"]), _value(p["known_citation_activity"])
        if denominator > activity or p["partial_citation_coverage"] != (denominator < activity):
            _invalid()
        for sum_key, mean_key, den in [
            ("raw_sum", "raw_mean", denominator),
            ("adjusted_sum", "adjusted_mean", activity),
        ]:
            total, mean = p[sum_key], p[mean_key]
            if (total is None) != (mean is None):
                _invalid()
            if total is not None and (not den or _value(mean) != _value(total) / den):
                _invalid()
    valid = [
        p
        for p in people.values()
        if p["adjusted_mean"] is not None and "ambiguous_identity" not in p["unplottable_reasons"]
    ]
    missing = [p for p in people.values() if p not in valid]
    points = [
        {
            "id": _view_id(p["person_token"]),
            "label": _label(p["display_name"]),
            "x": number(_value(p["activity"])),
            "y": number(_value(p["adjusted_mean"])),
            "size": number(_value(p["raw_sum"])),
            "category": "partial" if p["partial_citation_coverage"] else "complete",
        }
        for p in valid[:24]
    ]
    unplottable = [
        {
            "id": _view_id(p["person_token"]),
            "label": _label(p["display_name"]),
            "reason": _label(",".join(p["unplottable_reasons"]) or "undefined_adjustment"),
        }
        for p in missing[:24]
    ]
    return {
        "kind": "inventor-scatter",
        "x_label": "活動寄与（全単位）",
        "y_label": "同一出願年・技術分野の補正引用平均",
        "size_label": "既知の引用合計",
        "points": points,
        "edges": [],
        "unplottable": unplottable,
        "context": (
            f"引用スナップショット {stats['basis']['snapshot_date']}、"
            f"既知 {known}/{len(units)} 単位、"
            f"既知0 {zeros}、欠損 {len(units) - known}。表示 {len(points)}/{len(valid)} 点、"
            f"未定義 {len(unplottable)}/{len(missing)} 人。省略は表示のみ。"
            "同一出願年・技術分野の全参照母集団、"
            f"最小cohort {stats['basis']['min_cohort_units']} 単位。"
            "既知引用平均の分母は既知活動、補正平均は全活動。欠損を0で補完しない。"
            "引用は個人能力・採用適性ではない。自己引用情報は不明。"
        ),
    }


def _date_position(day):
    from datetime import date

    value = date.fromisoformat(day)
    start = date(value.year, 1, 1)
    end = date(value.year + 1, 1, 1)
    return value.year + (value - start).days / (end - start).days


def _confirmed_candidate(c):
    if c["employment_status"] != "confirmed":
        return
    direct = {
        e["evidence_id"]
        for e in c["evidence"]
        if e["inventor_id"] == c["canonical_inventor_id"]
        and e["type"] == "employment_move"
        and e["claim_status"] == "reported"
        and e["direct_employment_support"]
        and e["matching_entities"]
        and e["from_entity_id"] in c["removed_ids"]
        and e["to_entity_id"] in c["added_ids"]
        and e["valid_from"]["start"]
        and e["valid_to"]["end"]
        and e["valid_from"]["start"] <= c["possible_period_end"]
        and e["valid_to"]["end"] >= c["possible_period_start"]
    }
    accepted = [
        r
        for r in c["reviews"]
        if r["active"]
        and r["inventor_id"] == c["canonical_inventor_id"]
        and r["claim"] == "employment_move"
        and r["status"] == "accepted"
        and direct & set(r["evidence_ids"])
    ]
    if not c["canonical_inventor_id"] or not accepted or c["conflicts"]:
        _invalid()


def _mobility_operands(stats):
    associations = {}
    for a in stats["associations"]:
        key = (person_token(tuple(a["person_key"])), a["record_id"])
        if key in associations:
            _invalid()
        associations[key] = a
        d = a["observed_date"]
        if (d["start"] is None) != (d["end"] is None) or (d["start"] and d["start"] > d["end"]):
            _invalid()
    episodes = {e["episode_id"]: e for e in stats["episodes"]}
    if len(episodes) != len(stats["episodes"]):
        _invalid()
    for e in episodes.values():
        p = person_token(tuple(e["person_key"]))
        observed = e["observations"]
        if not observed or e["record_ids"] != sorted({o["record_id"] for o in observed}):
            _invalid()
        for o in observed:
            a = associations.get((p, o["record_id"]))
            if (
                not a
                or a["observed_date"] != o["observed_date"]
                or a["applicant_ids"] != o["applicant_ids"]
                or not o["observed_date"]["start"]
            ):
                _invalid()
        if (
            e["start"] != min(o["observed_date"]["start"] for o in observed)
            or e["end"] != max(o["observed_date"]["end"] for o in observed)
            or e["applicant_ids"] != sorted({a for o in observed for a in o["applicant_ids"]})
        ):
            _invalid()
    candidates = {}
    for c in stats["candidates"]:
        _confirmed_candidate(c)
        if c["candidate_id"] in candidates:
            _invalid()
        candidates[c["candidate_id"]] = c
        a, b = episodes.get(c["preceding_episode_id"]), episodes.get(c["following_episode_id"])
        if (
            not a
            or not b
            or a["person_key"] != c["person_key"]
            or b["person_key"] != c["person_key"]
            or a["end"] >= b["start"]
            or c["period_start"] != a["end"]
            or c["period_end"] != b["start"]
            or c["from_ids"] != a["applicant_ids"]
            or c["to_ids"] != b["applicant_ids"]
            or c["removed_ids"] != sorted(set(c["from_ids"]) - set(c["to_ids"]))
            or c["added_ids"] != sorted(set(c["to_ids"]) - set(c["from_ids"]))
        ):
            _invalid()
    return associations, episodes, candidates


def _mobility(stats):
    associations, episodes, candidates = _mobility_operands(stats)
    people = sorted({p for p, _ in associations})[:12]
    lanes = {p: i for i, p in enumerate(people)}
    dated = [a for a in associations.values() if a["observed_date"]["start"]]
    years = (
        list(
            range(
                min(int(a["observed_date"]["start"][:4]) for a in dated),
                max(int(a["observed_date"]["end"][:4]) for a in dated) + 1,
            )
        )
        if dated
        else []
    )
    if len(years) > 30:
        _invalid()
    nodes, links, endpoints = [], [], {}
    for (p, record), a in associations.items():
        d = a["observed_date"]
        if p not in lanes or not d["start"] or len(nodes) + 2 > 40:
            continue
        first = len(nodes)
        for endpoint in ["start", "end"]:
            index = len(nodes)
            endpoints[p, record, endpoint] = index
            nodes.append(
                {
                    "id": _view_id(person_token((p, record)) + ":" + endpoint),
                    "x": _date_position(d[endpoint]),
                    "y": lanes[p],
                    "size": 1,
                    "category": 0,
                    "label": _label(
                        f"{d['raw']} ({d['precision']}) 出願人 "
                        + (",".join(a["applicant_ids"]) or "不明")
                    ),
                    "state": "observed"
                    if a["applicant_ids"] and a["person_key"][0] in {"id", "name"}
                    else "unknown",
                }
            )
        if d["start"] != d["end"]:
            links.append({"source": first, "target": first + 1, "gap": False, "state": "observed"})
    for c in candidates.values():
        if (
            c["person_key"][0] not in {"id", "name"}
            or not c["from_ids"]
            or not c["to_ids"]
            or "unknown_applicants" in c["reason_codes"]
        ):
            continue
        a, b = episodes[c["preceding_episode_id"]], episodes[c["following_episode_id"]]
        old = max(a["observations"], key=lambda o: o["observed_date"]["end"])
        new = min(b["observations"], key=lambda o: o["observed_date"]["start"])
        p = person_token(tuple(c["person_key"]))
        source = endpoints.get((p, old["record_id"], "end"))
        target = endpoints.get((p, new["record_id"], "start"))
        if source is None or target is None:
            continue
        state = (
            "confirmed"
            if c["employment_status"] == "confirmed"
            else "observed"
            if c["employment_status"] in {"rejected", "conflicting", "pending", "withdrawn"}
            or c["candidate_status"] == "unknown"
            else "inferred"
        )
        links.append(
            {
                "source": source,
                "target": target,
                "gap": c["missing_calendar_years"] > 0,
                "state": state,
            }
        )
        nodes[target]["label"] = _label(
            f"{c['employment_status']} 証拠{len(c['evidence'])}/review{len(c['reviews'])} "
            + nodes[target]["label"]
        )
    bands, events = [], {}
    event_lists = [r["event_matches"] for r in stats["corporate_changes"]] + [
        c["corporate_matches"] for c in candidates.values()
    ]
    for matches in event_lists:
        for event in matches:
            fact_keys = (
                "event_id",
                "type",
                "status",
                "scope",
                "entity_ids",
                "record_ids",
                "source_ids",
                "announcement_date",
                "effective_date",
            )
            fact = {key: event[key] for key in fact_keys}
            if event["event_id"] in events and events[event["event_id"]] != fact:
                _invalid()
            events[event["event_id"]] = fact
    kinds = {
        "patent_rights_transfer": "rights_transfer",
        "business_transfer": "organizational_transfer",
    }
    for event in events.values():
        d = (
            event["effective_date"]
            if event["effective_date"]["start"]
            else event["announcement_date"]
        )
        kind = kinds.get(event["type"], event["type"])
        if (
            not d["start"]
            or event["status"] not in {"announced", "completed"}
            or kind == "minority_investment"
            or not years
            or len(bands) >= 6
        ):
            continue
        start, end = _date_position(d["start"]), _date_position(d["end"])
        if start < years[0] or end > years[-1] + 1:
            continue
        bands.append(
            {
                "id": _view_id(event["event_id"]),
                "start": start,
                "end": end,
                "label": _label(f"{d['raw']} ({d['precision']}) 企業事実・在籍未確認"),
                "kind": kind,
                "status": event["status"],
            }
        )
    return {
        "kind": "inventor-timeline",
        "lanes": [_label(__import__("json").loads(p)[1]) for p in people],
        "years": years,
        "nodes": nodes,
        "links": links,
        "bands": bands,
        "context": (
            f"表示 {len(nodes) // 2}/{len(associations)} 特許関係観測、候補 {len(candidates)} 件、"
            f"企業帯 {len(bands)}/{len(events)}、日付欠損 {stats['coverage']['missing_dates']}。"
            "省略は表示のみ。区間は元の日付精度の不確実範囲、在籍期間ではない。"
            "推定リンクは雇用移動候補、独立の証拠・レビューのみ雇用確認。"
            "企業事実・M&Aの確認は個人雇用の確認ではない。欠損日付は補完しない。"
            "氏名一致のみは本人確認や移動証拠ではない。"
            "空白は退職を意味せず、複数出願人は特許共記載であり兼務確認ではない。"
        ),
    }


def _fractional_weights(associations, episodes, candidates, axis):
    """Check allocation operands using observed direct historical relations only."""
    boundary_maps = {}
    if axis == "group":
        by_record = {}
        for (_, record), association in associations.items():
            relations = association["group_relations"]
            if record in by_record and by_record[record] != relations:
                _invalid()
            by_record[record] = relations
        for eid, episode in episodes.items():
            for legal in episode["applicant_ids"]:
                parents = set()
                for record in episode["record_ids"]:
                    rows = [
                        r for r in by_record[record] if r["child_id"] == legal and r["controlling"]
                    ]
                    if len(rows) != 1 or rows[0]["strength"] != "definite":
                        parents.clear()
                        break
                    parents.add(rows[0]["parent_id"])
                boundary_maps[eid, legal] = next(iter(parents)) if len(parents) == 1 else None
    expected = {}
    for cid, c in candidates.items():
        weights = {}
        if c["canonical_inventor_id"] is not None and c["removed_ids"] and c["added_ids"]:
            mass = Fraction(1, len(c["removed_ids"]) * len(c["added_ids"]))
            for a in c["removed_ids"]:
                for b in c["added_ids"]:
                    source = boundary_maps[c["preceding_episode_id"], a] if axis == "group" else a
                    target = boundary_maps[c["following_episode_id"], b] if axis == "group" else b
                    if source is not None and target is not None and source != target:
                        pair = source, target
                        weights[pair] = weights.get(pair, Fraction(0)) + mass
        expected[cid] = weights
    return expected


def _corporate_flow(stats):
    associations, episodes, candidates = _mobility_operands(stats)
    ids = [n["entity_id"] for n in stats["nodes"]]
    if len(ids) != len(set(ids)):
        _invalid()
    buckets, masses = {}, {}
    fractional = stats["provenance"].get("allocation") == "fractional_flows"
    expected_weights = (
        _fractional_weights(associations, episodes, candidates, stats["provenance"]["axis"])
        if fractional
        else {}
    )
    seen = set()
    layer = stats["provenance"]["layer"]
    for f in stats["flows"]:
        a, b = f["from_id"], f["to_id"]
        if (
            f["flow_id"] in seen
            or a not in ids
            or b not in ids
            or a == b
            or f["unique_inventors"] != len(set(f["inventor_ids"]))
            or f["transition_events"] != len(set(f["candidate_ids"]))
            or not set(f["candidate_ids"]) <= candidates.keys()
            or f["layer"] != layer
        ):
            _invalid()
        seen.add(f["flow_id"])
        for cid in f["candidate_ids"]:
            c = candidates[cid]
            if layer == "confirmed_employment_move" and c["employment_status"] != "confirmed":
                _invalid()
            if (
                c["canonical_inventor_id"] not in f["inventor_ids"]
                or not c["from_ids"]
                or not c["to_ids"]
            ):
                _invalid()
        bucket = buckets.setdefault((a, b), set())
        bucket.update(f["inventor_ids"])  # UNION, not summed bucket head counts.
        if fractional:
            weight = _value(f["flow_weight"])
            if weight != _value(f["event_mass"]):
                _invalid()
            expected = sum(
                (expected_weights[cid].get((a, b), Fraction(0)) for cid in f["candidate_ids"]),
                Fraction(0),
            )
            if not expected or weight != expected:
                _invalid()
            masses[a, b] = masses.get((a, b), Fraction(0)) + weight
    if "allocation_summary" in stats:
        summary = stats["allocation_summary"]
        allocated = sum((_value(f["event_mass"]) for f in stats["flows"]), Fraction(0))
        unallocated = sum((_value(u["event_mass"]) for u in stats["unallocated"]), Fraction(0))
        eligible = sum(c["canonical_inventor_id"] is not None for c in candidates.values())
        if (
            summary["eligible_events"] != eligible
            or _value(summary["allocated_event_mass"]) != allocated
            or _value(summary["unallocated_event_mass"]) != unallocated
            or _value(summary["total_event_mass"]) != eligible
            or allocated + unallocated != eligible
        ):
            _invalid()
    selected = sorted(ids)[:40]
    positions = {key: i for i, key in enumerate(selected)}
    count = len(selected)
    nodes = [
        {
            "id": _view_id(key),
            "label": _label(key),
            "x": number(math.cos(2 * math.pi * i / count)),
            "y": number(math.sin(2 * math.pi * i / count)),
            "value": len(set().union(*(v for (a, b), v in buckets.items() if key in (a, b)))),
            "group": i,
            "hop": None,
        }
        for i, key in enumerate(selected)
    ]
    state = {
        "observed_association_change": "observed",
        "individual_move_candidate": "inferred",
        "confirmed_employment_move": "confirmed",
        "organizational_transfer_candidate": "corporate",
    }[layer]
    edges = [
        {
            "source": positions[a],
            "target": positions[b],
            "value": number(masses[a, b]) if fractional else len(v),
            "directed": True,
            "state": state,
        }
        for (a, b), v in sorted(buckets.items())
        if a in positions and b in positions
    ][:300]
    allocation_caption = (
        f"axis={stats['provenance']['axis']}、"
        f"allocation={stats['provenance'].get('allocation', 'unique_inventors')}。"
    )
    if "allocation_summary" in stats:
        allocation_caption += f"未配分質量 {unallocated.numerator}/{unallocated.denominator}。"
    weight_caption = (
        "線幅は按分イベント質量（人数ではない）、同ペアの状態bucketを質量和へ統合。"
        if fractional
        else "線幅は同ペアの全状態bucketに属するcanonical人物和集合、反復イベント件数ではない。"
    )
    return {
        "kind": "inventor-network",
        "nodes": nodes,
        "edges": edges,
        "focus": None,
        "context": (
            f"表示 {len(nodes)}/{len(ids)} 法人・{len(edges)}/{len(buckets)} 有向ペア。"
            f"採用層={layer}、未配分 {len(stats['unallocated'])} 行。"
            + allocation_caption
            + "省略は表示のみ。線は観測出願人の集合変化。"
            + weight_caption
            + "円面積は関与canonical人物の和集合。候補・企業事実と個人雇用確認は独立。"
            "特許の企業間変化を雇用移動やM&Aの証明としない。"
            "固定円周配置の距離に分析的意味はない。"
        ),
    }


def _finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        _invalid()
    if isinstance(value, dict):
        for child in value.values():
            _finite(child)
    elif isinstance(value, list):
        for child in value:
            _finite(child)


def project_inventor(analysis_id, data):
    _finite(data)
    if analysis_id != data.get("analysis_id"):
        _invalid()
    if analysis_id == "inventor-network.v1":
        return _network(data["statistics"])
    if analysis_id == "inventor-ego-network.v1":
        return _network(data["statistics"], ego=True)
    if analysis_id == "inventor-technology.v1":
        return _technology(data["statistics"])
    if analysis_id == "inventor-activity.v1":
        return _activity(data["statistics"])
    if analysis_id == "inventor-cluster-flow.v1":
        return _alluvial(data["statistics"])
    if analysis_id == "inventor-similarity.v1":
        return _similarity(data["statistics"])
    if analysis_id == "inventor-impact.v1":
        return _impact(data["statistics"])
    if analysis_id == "inventor-mobility.v1":
        return _mobility(data["statistics"])
    if analysis_id == "inventor-mobility-flow.v1":
        return _corporate_flow(data["statistics"])
    raise ValueError("unsupported inventor presentation")
