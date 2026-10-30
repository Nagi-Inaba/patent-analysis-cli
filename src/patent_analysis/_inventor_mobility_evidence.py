"""Claim-specific evidence and review application to mobility candidates."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from datetime import date

from patent_analysis._inventor_mobility_common import MAX_ROWS, _fail
from patent_analysis.corporate_history import date_data
from patent_analysis.inventor_models import parse_observation_date


def _review_data(row, active=True):
    return dict(
        review_id=row["review_id"],
        inventor_id=row["inventor_id"],
        claim=row["claim"],
        status=row["status"],
        reason=row["reason"],
        reviewed_date=date_data(parse_observation_date(row["reviewed_date"], kind="checked")),
        evidence_ids=sorted(row["evidence_ids"]),
        event_ids=sorted(row["event_ids"]),
        record_ids=sorted(row["record_ids"]),
        source_ids=sorted(row["source_ids"]),
        supersedes_review_id=row["supersedes_review_id"],
        active=active,
    )


def _evidence_scope(row, candidate):
    start = parse_observation_date(row["valid_from"], kind="valid_from")
    end = parse_observation_date(row["valid_to"], kind="valid_to")
    return (
        row["type"] == "employment_move"
        and candidate["removed_ids"] == [row["from_entity_id"]]
        and candidate["added_ids"] == [row["to_entity_id"]]
        and start.start is not None
        and end.end is not None
        and start.start.isoformat() <= candidate["possible_period_end"]
        and end.end.isoformat() >= candidate["possible_period_start"]
    )


def _apply_evidence(candidates, snapshot, review_bindings, budget):
    if snapshot is None:
        if review_bindings:
            _fail()
        return []
    sources = {r["source_id"]: r["kind"] for r in snapshot.tables["sources"]}
    reviews = sorted(snapshot.tables["reviews"], key=lambda r: r["review_id"])
    attached = set()
    selected = defaultdict(set)
    if review_bindings is not None:
        if not isinstance(review_bindings, Mapping) or len(review_bindings) > MAX_ROWS:
            _fail()
        by_id = {c["candidate_id"]: c for c in candidates}
        review_ids = {r["review_id"]: r for r in reviews}
        for candidate_id, refs in review_bindings.items():
            if (
                not isinstance(candidate_id, str)
                or candidate_id not in by_id
                or not isinstance(refs, tuple)
                or len(refs) > 64
                or not all(isinstance(r, str) for r in refs)
                or len(set(refs)) != len(refs)
                or any(r not in review_ids for r in refs)
            ):
                _fail()
            if any(
                review_ids[r]["inventor_id"] != by_id[candidate_id]["canonical_inventor_id"]
                for r in refs
            ):
                _fail()
            selected[candidate_id].update(refs)
    else:
        evidence_index = {e["evidence_id"]: e for e in snapshot.tables["personal_evidence"]}
        for row in reviews:
            matches = []
            for c in candidates:
                if c["canonical_inventor_id"] != row["inventor_id"]:
                    continue
                exact_records = bool(row["record_ids"]) and set(row["record_ids"]) == set(
                    c["record_ids"]
                )
                exact_evidence = (
                    not row["record_ids"]
                    and bool(row["evidence_ids"])
                    and all(_evidence_scope(evidence_index[e], c) for e in row["evidence_ids"])
                )
                exact_events = (
                    not row["record_ids"]
                    and not row["evidence_ids"]
                    and bool(row["event_ids"])
                    and set(row["event_ids"]) <= {m["event_id"] for m in c["corporate_matches"]}
                )
                if exact_records or exact_evidence or exact_events:
                    matches.append(c)
            if len(matches) == 1:
                selected[matches[0]["candidate_id"]].add(row["review_id"])
    by_review = {r["review_id"]: r for r in reviews}
    # Linear connected-link traversal retains ancestors, descendants and branches.
    links = defaultdict(set)
    for r in reviews:
        parent = r["supersedes_review_id"]
        if parent is not None:
            links[r["review_id"]].add(parent)
            links[parent].add(r["review_id"])
    for refs in selected.values():
        stack = list(refs)
        while stack:
            for linked in links[stack.pop()] - refs:
                refs.add(linked)
                stack.append(linked)
    for c in candidates:
        direct = set()
        for row in sorted(snapshot.tables["personal_evidence"], key=lambda r: r["evidence_id"]):
            if row["inventor_id"] != c["canonical_inventor_id"]:
                continue
            start = parse_observation_date(row["valid_from"], kind="valid_from")
            end = parse_observation_date(row["valid_to"], kind="valid_to")
            if (start.start or date.min).isoformat() > c["possible_period_end"] or (
                end.end or date.max
            ).isoformat() < c["possible_period_start"]:
                continue
            matching = c["removed_ids"] == [row["from_entity_id"]] and c["added_ids"] == [
                row["to_entity_id"]
            ]
            is_direct = (
                matching
                and row["type"] == "employment_move"
                and row["claim_status"] == "reported"
                and start.start is not None
                and end.end is not None
                and any(sources.get(s) == "employment_record" for s in row["source_ids"])
            )
            if is_direct:
                direct.add(row["evidence_id"])
            if matching and (
                row["type"] == "user_assertion" or row["claim_status"] == "user_asserted"
            ):
                c["employment_status"] = "user_asserted"
            has_direct_source = any(
                sources.get(s) == "employment_record" for s in row["source_ids"]
            )
            touches = (
                row["from_entity_id"] in c["removed_ids"] + c["added_ids"]
                or row["to_entity_id"] in c["removed_ids"] + c["added_ids"]
            )
            if (
                touches
                and has_direct_source
                and (
                    row["claim_status"] == "conflicting"
                    or row["claim_status"] == "reported"
                    and (
                        row["type"] == "employment_continuity"
                        or row["type"] == "employment_move"
                        and not matching
                    )
                )
            ):
                c["conflicts"].append(row["evidence_id"])
            budget.append(
                c["evidence"],
                dict(
                    evidence_id=row["evidence_id"],
                    inventor_id=row["inventor_id"],
                    from_entity_id=row["from_entity_id"],
                    to_entity_id=row["to_entity_id"],
                    type=row["type"],
                    claim_status=row["claim_status"],
                    valid_from=date_data(start),
                    valid_to=date_data(end),
                    source_ids=sorted(row["source_ids"]),
                    matching_entities=matching,
                    direct_employment_support=is_direct,
                ),
            )
        superseded = {by_review[r]["supersedes_review_id"] for r in selected[c["candidate_id"]]}
        for row in reviews:
            if row["inventor_id"] != c["canonical_inventor_id"]:
                continue
            if row["review_id"] not in selected[c["candidate_id"]]:
                continue
            active = row["review_id"] not in superseded
            budget.append(c["reviews"], _review_data(row, active))
            attached.add(row["review_id"])
        live = [r for r in c["reviews"] if r["active"] and r["claim"] == "employment_move"]
        accepted = [r for r in live if r["status"] == "accepted"]
        if accepted:
            c["employment_status"] = (
                "confirmed"
                if any(direct & set(r["evidence_ids"]) for r in accepted)
                else "user_asserted"
            )
        branches = defaultdict(list)
        for r in c["reviews"]:
            if r["claim"] == "employment_move" and r["supersedes_review_id"] is not None:
                branches[r["supersedes_review_id"]].append(r["review_id"])
        for children in branches.values():
            if len(children) > 1:
                c["conflicts"].extend(children)
        statuses = {r["status"] for r in live}
        if "conflicting" in statuses or {"accepted", "rejected"} <= statuses:
            c["conflicts"].extend(r["review_id"] for r in live)
        elif "rejected" in statuses:
            c["employment_status"] = "rejected"
        elif "user_asserted" in statuses and c["employment_status"] == "unknown":
            c["employment_status"] = "user_asserted"
        elif "pending" in statuses and c["employment_status"] == "unknown":
            c["employment_status"] = "pending"
        elif "withdrawn" in statuses and c["employment_status"] == "unknown":
            c["employment_status"] = "withdrawn"
        if c["conflicts"]:
            c["conflicts"] = sorted(set(c["conflicts"]))
            c["employment_status"] = "conflicting"
        corporate_reviews = [
            r for r in c["reviews"] if r["active"] and r["claim"] == "corporate_event"
        ]
        corporate_statuses = {r["status"] for r in corporate_reviews}
        if "conflicting" in corporate_statuses or {"accepted", "rejected"} <= corporate_statuses:
            c["corporate_status"] = "conflicting"
            c["corporate_conflicts"] = sorted(r["review_id"] for r in corporate_reviews)
        elif "rejected" in corporate_statuses:
            c["corporate_status"] = "rejected"
        elif "accepted" in corporate_statuses:
            appropriate = any(
                m["corporate_status"] == "confirmed"
                and any(
                    m["event_id"] in r["event_ids"]
                    for r in corporate_reviews
                    if r["status"] == "accepted"
                )
                for m in c["corporate_matches"]
            )
            c["corporate_status"] = "confirmed" if appropriate else "user_asserted"
        elif "user_asserted" in corporate_statuses:
            c["corporate_status"] = "user_asserted"
        elif "pending" in corporate_statuses:
            c["corporate_status"] = "pending"
        elif "withdrawn" in corporate_statuses:
            c["corporate_status"] = "withdrawn"
        corporate_branches = defaultdict(list)
        for r in c["reviews"]:
            if r["claim"] == "corporate_event" and r["supersedes_review_id"] is not None:
                corporate_branches[r["supersedes_review_id"]].append(r["review_id"])
        for children in corporate_branches.values():
            if len(children) > 1:
                c["corporate_conflicts"].extend(children)
        if c["corporate_conflicts"]:
            c["corporate_conflicts"] = sorted(set(c["corporate_conflicts"]))
            c["corporate_status"] = "conflicting"
        if c["employment_status"] == "confirmed":
            c["interpretations"].append("confirmed_employment_move")
            c["interpretations"].sort()
        c["source_ids"] = sorted(
            set(c["source_ids"])
            | {s for e in c["evidence"] + c["reviews"] for s in e["source_ids"]}
        )
    unbound = []
    globally_superseded = {r["supersedes_review_id"] for r in reviews}
    for r in reviews:
        if r["review_id"] not in attached:
            budget.append(unbound, _review_data(r, r["review_id"] not in globally_superseded))
    return unbound
