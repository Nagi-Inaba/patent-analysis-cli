"""Shared M08/M09/M10 pure kernels: patent associations are not employment."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Mapping
from datetime import date
from fractions import Fraction

from patent_analysis.corporate_history import (
    MAX_OUTPUT_BYTES,
    bounded_output,
    corporate_aliases,
    corporate_relations,
    date_data,
    match_corporate_events,
)
from patent_analysis.errors import DatasetInputError
from patent_analysis.inventor_models import PatentObservation, parse_observation_date
from patent_analysis.inventor_numeric import exact
from patent_analysis.inventor_sidecars import SidecarSnapshot, validate_observation_references

MAX_PERSONS = 200
MAX_OBSERVATIONS = 5000
MAX_ROWS = 5000
MAX_COMPARISONS = 200000
DISCLAIMERS = [
    "patent_applicant_association_is_not_employment",
    "candidate_period_is_not_guaranteed_employment_interval",
    "calendar_gaps_are_not_proof_of_absence_or_retirement",
    "corporate_completion_does_not_confirm_personal_employment_move",
]


def _fail(budget=False):
    raise DatasetInputError(
        "dataset input exceeds published limits" if budget else "input is invalid"
    )


def _stable_id(prefix, facts):
    raw = json.dumps(facts, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return prefix + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


class _RowBudget:
    def __init__(self):
        self.bytes = 0

    def spend(self, value):
        self.bytes += len(json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8"))
        if self.bytes > MAX_OUTPUT_BYTES:
            _fail(True)

    def append(self, rows, value):
        if len(rows) >= MAX_ROWS:
            _fail(True)
        self.spend(value)
        rows.append(value)


def build_mobility(
    observations: tuple[PatentObservation, ...],
    snapshot: SidecarSnapshot | None = None,
    *,
    minimum_observations: int = 1,
    maximum_gap_years: int = 5,
    review_bindings: Mapping[str, tuple[str, ...]] | None = None,
) -> dict:
    """Observed unordered episodes, set-change candidates and claim-specific audit history."""
    if (
        not isinstance(observations, tuple)
        or not all(isinstance(o, PatentObservation) for o in observations)
        or snapshot is not None
        and not isinstance(snapshot, SidecarSnapshot)
        or review_bindings is not None
        and not isinstance(review_bindings, Mapping)
        or type(minimum_observations) is not int
        or not 1 <= minimum_observations <= 5000
        or type(maximum_gap_years) is not int
        or not 0 <= maximum_gap_years <= 9998
    ):
        _fail()
    if len(observations) > MAX_OBSERVATIONS:
        _fail(True)
    records = {}
    for o in observations:
        old = records.setdefault(o.record_id, o)

        def identity_facts(record):
            return sorted(
                {
                    (
                        p.key,
                        p.status,
                        p.display_name,
                        tuple(sorted(p.source_ids)),
                        tuple(sorted(p.candidate_ids)),
                        tuple(sorted(p.caveats)),
                    )
                    for p in record.inventors
                }
            )

        if old.semantic_key() != o.semantic_key() or identity_facts(old) != identity_facts(o):
            _fail()
    observations = tuple(records[k] for k in sorted(records))
    if len({o.observed_date.kind for o in observations if o.observed_date.start is not None}) > 1:
        _fail()
    people = {p.key for o in observations for p in o.inventors}
    association_count = sum(len(o.inventor_keys) for o in observations)
    if len(people) > MAX_PERSONS or association_count > MAX_ROWS:
        _fail(True)
    relations = {}
    aliases = {}
    if snapshot:
        comparisons = sum(len(o.applicant_ids) for o in observations) * (
            len(snapshot.tables["groups"]) + len(snapshot.tables["entity_aliases"])
        )
        comparisons += association_count * (
            2 * (len(snapshot.tables["events"]) + len(snapshot.tables["sources"]))
            + len(snapshot.tables["personal_evidence"])
            + 3 * len(snapshot.tables["reviews"])
            + sum(
                len(r["evidence_ids"]) + len(r["event_ids"]) + len(r["record_ids"])
                for r in snapshot.tables["reviews"]
            )
        )
        if sum(len(rows) for rows in snapshot.tables.values()) > MAX_ROWS:
            _fail(True)
        if comparisons > MAX_COMPARISONS:
            _fail(True)
    if snapshot is not None:
        validate_observation_references(
            snapshot, observations, inventor_ids=tuple(sorted(k[1] for k in people if k[0] == "id"))
        )
    context_budget = _RowBudget()
    for o in observations:
        relations[o.record_id] = [
            r for a in o.applicant_ids for r in corporate_relations(snapshot, a, o.observed_date)
        ]
        aliases[o.record_id] = [
            r for a in o.applicant_ids for r in corporate_aliases(snapshot, a, o.observed_date)
        ]
        context_budget.spend(relations[o.record_id])
        context_budget.spend(aliases[o.record_id])
    budget = _RowBudget()
    associations = []
    by_person = defaultdict(list)
    identities = defaultdict(set)
    for o in observations:
        for p in o.inventors:
            identities[p.key].add(p.status)
    for o in observations:
        for key in o.inventor_keys:
            budget.append(
                associations,
                dict(
                    person_key=list(key),
                    record_id=o.record_id,
                    observed_date=date_data(o.observed_date),
                    applicant_ids=list(o.applicant_ids),
                    source_ids=list(o.source_ids),
                    identity_status=sorted(identities[key]),
                    group_relations=relations[o.record_id],
                    entity_aliases=aliases[o.record_id],
                ),
            )
            if o.observed_date.start is not None and not key[0].startswith("ambiguous"):
                by_person[key].append(o)
    episodes = []
    candidates = []
    corporate_changes = []
    for key in sorted(by_person):
        groups = []
        last_end = None
        for o in sorted(
            by_person[key], key=lambda o: (o.observed_date.start, o.observed_date.end, o.record_id)
        ):
            if last_end is not None and o.observed_date.start <= last_end:
                groups[-1].append(o)
                last_end = max(last_end, o.observed_date.end)
            else:
                groups.append([o])
                last_end = o.observed_date.end
        person_episodes = []
        for group in groups:
            start = min(o.observed_date.start for o in group)
            end = max(o.observed_date.end for o in group)
            ids = sorted(o.record_id for o in group)
            applicants = sorted({a for o in group for a in o.applicant_ids})
            episode = dict(
                episode_id=_stable_id("ep_", [key, ids]),
                person_key=list(key),
                start=start.isoformat(),
                end=end.isoformat(),
                record_ids=ids,
                applicant_ids=applicants,
                observations=[
                    dict(
                        record_id=o.record_id,
                        observed_date=date_data(o.observed_date),
                        applicant_ids=list(o.applicant_ids),
                    )
                    for o in sorted(group, key=lambda o: o.record_id)
                ],
                unknown_applicants=any(not o.applicant_ids for o in group),
                parallel_association=len(applicants) > 1,
                unordered=True,
            )
            budget.append(episodes, episode)
            person_episodes.append((episode, group))
        seen_events = set()
        for episode, _ in person_episodes:
            for match in match_corporate_events(
                snapshot,
                tuple(episode["applicant_ids"]),
                tuple(episode["applicant_ids"]),
                tuple(episode["record_ids"]),
                episode["start"],
                episode["end"],
            ):
                if match["event_id"] in seen_events:
                    continue
                seen_events.add(match["event_id"])
                budget.append(
                    corporate_changes,
                    dict(
                        change_id=_stable_id("cc_", [key, match["event_id"]]),
                        person_key=list(key),
                        type=match["type"],
                        entity_ids=match["entity_ids"],
                        record_ids=episode["record_ids"],
                        from_relations=[],
                        to_relations=[],
                        event_matches=[match],
                        employment_confirmation=False,
                    ),
                )
        left_counts = _run_counts(person_episodes, maximum_gap_years)
        right_counts = list(
            reversed(_run_counts(list(reversed(person_episodes)), maximum_gap_years))
        )
        for index, ((old, old_rows), (new, new_rows)) in enumerate(
            zip(person_episodes, person_episodes[1:], strict=False)
        ):
            before, after = set(old["applicant_ids"]), set(new["applicant_ids"])
            if before == after:
                for entity in sorted(before):
                    old_rel = [
                        r
                        for o in old_rows
                        for r in relations[o.record_id]
                        if r["child_id"] == entity and r["controlling"]
                    ]
                    new_rel = [
                        r
                        for o in new_rows
                        for r in relations[o.record_id]
                        if r["child_id"] == entity and r["controlling"]
                    ]
                    if {r["parent_id"] for r in old_rel} != {r["parent_id"] for r in new_rel}:
                        budget.append(
                            corporate_changes,
                            dict(
                                change_id=_stable_id(
                                    "cc_", [key, entity, old["episode_id"], new["episode_id"]]
                                ),
                                person_key=list(key),
                                type="group_change",
                                entity_ids=[entity],
                                record_ids=sorted(old["record_ids"] + new["record_ids"]),
                                from_relations=old_rel,
                                to_relations=new_rel,
                                event_matches=[],
                                employment_confirmation=False,
                            ),
                        )
                for match in match_corporate_events(
                    snapshot,
                    tuple(before),
                    tuple(after),
                    tuple(old["record_ids"] + new["record_ids"]),
                    old["start"],
                    new["end"],
                ):
                    if (
                        match["type"] in {"name_change", "group_change", "patent_rights_transfer"}
                        and match["event_id"] not in seen_events
                    ):
                        seen_events.add(match["event_id"])
                        budget.append(
                            corporate_changes,
                            dict(
                                change_id=_stable_id("cc_", [key, match["event_id"]]),
                                person_key=list(key),
                                type=match["type"],
                                entity_ids=match["entity_ids"],
                                record_ids=sorted(old["record_ids"] + new["record_ids"]),
                                from_relations=[],
                                to_relations=[],
                                event_matches=[match],
                                employment_confirmation=False,
                            ),
                        )
                continue
            removed, added = sorted(before - after), sorted(after - before)
            facts = [key, old["observations"], new["observations"]]
            year_distance = int(new["start"][:4]) - int(old["end"][:4])
            gap_years = max(0, year_distance - 1)
            reasons = []
            if key[0] == "name":
                reasons.append("name_match_is_not_person_confirmation")
            if old["unknown_applicants"] or new["unknown_applicants"]:
                reasons.append("unknown_applicants")
            if min(left_counts[index], right_counts[index + 1]) < minimum_observations:
                reasons.append("insufficient_observations")
            if year_distance > maximum_gap_years:
                reasons.append("gap_exceeds_threshold")
            interpretations = ["individual_move_candidate", "unexplained_association_change"]
            if old["parallel_association"] or new["parallel_association"]:
                interpretations.append("parallel_association")
            shared_tech = {t for o in old_rows for t in o.classifications} & {
                t for o in new_rows for t in o.classifications
            }
            shared_people = (
                {p for o in old_rows for p in o.inventor_keys}
                & {p for o in new_rows for p in o.inventor_keys}
            ) - {key}
            budget.append(
                candidates,
                dict(
                    candidate_id=_stable_id("mc_", facts),
                    person_key=list(key),
                    canonical_inventor_id=key[1] if key[0] == "id" else None,
                    identity_status=sorted(identities[key]),
                    from_ids=sorted(before),
                    to_ids=sorted(after),
                    removed_ids=removed,
                    added_ids=added,
                    retained_ids=sorted(before & after),
                    preceding_episode_id=old["episode_id"],
                    following_episode_id=new["episode_id"],
                    preceding_observation_count=left_counts[index],
                    following_observation_count=right_counts[index + 1],
                    preceding_dates=[date_data(o.observed_date) for o in old_rows],
                    following_dates=[date_data(o.observed_date) for o in new_rows],
                    period_start=old["end"],
                    period_end=new["start"],
                    possible_period_start=old["start"],
                    possible_period_end=new["end"],
                    missing_calendar_years=gap_years,
                    gap_year_distance=year_distance,
                    record_ids=sorted(old["record_ids"] + new["record_ids"]),
                    source_ids=sorted({s for o in old_rows + new_rows for s in o.source_ids}),
                    observed_status="observed",
                    candidate_status="unknown" if reasons else "candidate",
                    employment_status="unknown",
                    corporate_status="unknown",
                    interpretations=interpretations,
                    reason_codes=reasons,
                    supporting_signals=dict(
                        shared_technologies=[list(t) for t in sorted(shared_tech)],
                        shared_coinventor_keys=[
                            list(p) for p in sorted(shared_people) if p[0] == "id"
                        ],
                        simultaneous_canonical_persons=0,
                    ),
                    corporate_matches=[],
                    evidence=[],
                    reviews=[],
                    conflicts=[],
                    corporate_conflicts=[],
                ),
            )
    simultaneous = defaultdict(set)
    for c in candidates:
        if c["canonical_inventor_id"] is not None:
            signature = (
                tuple(c["from_ids"]),
                tuple(c["to_ids"]),
                c["period_start"],
                c["period_end"],
            )
            simultaneous[signature].add(c["canonical_inventor_id"])
    for candidate in candidates:
        signature = (
            tuple(candidate["from_ids"]),
            tuple(candidate["to_ids"]),
            candidate["period_start"],
            candidate["period_end"],
        )
        candidate["supporting_signals"]["simultaneous_canonical_persons"] = len(
            simultaneous[signature]
        )
        matches = match_corporate_events(
            snapshot,
            tuple(candidate["removed_ids"]),
            tuple(candidate["added_ids"]),
            tuple(candidate["record_ids"]),
            candidate["possible_period_start"],
            candidate["possible_period_end"],
        )
        budget.spend(matches)
        candidate["corporate_matches"] = matches
        if any(m["corporate_status"] == "confirmed" for m in matches):
            candidate["corporate_status"] = "confirmed"
        if any(m["organizational_transfer_support"] for m in matches):
            candidate["interpretations"].append("organizational_transfer_candidate")
        if any(
            m["type"] == "patent_rights_transfer" or m["scope"] == "patents_only" for m in matches
        ):
            candidate["interpretations"].append("patent_rights_transfer")
        candidate["source_ids"] = sorted(
            set(candidate["source_ids"]) | {s for m in matches for s in m["source_ids"]}
        )
        candidate["interpretations"].sort()
    unbound_reviews = _apply_evidence(candidates, snapshot, review_bindings, budget)
    for c in candidates:
        allocatable = (
            c["canonical_inventor_id"] is not None
            and len(c["from_ids"]) == len(c["to_ids"]) == 1
            and len(c["removed_ids"]) == len(c["added_ids"]) == 1
            and "unknown_applicants" not in c["reason_codes"]
        )
        personal_allowed = not _rights_only_without_personal_evidence(c) and c[
            "employment_status"
        ] not in {
            "rejected",
            "conflicting",
            "pending",
            "withdrawn",
        }
        c["default_flow_adoption"] = dict(
            observed_association_change=allocatable,
            individual_move_candidate=allocatable
            and personal_allowed
            and c["candidate_status"] == "candidate",
            confirmed_employment_move=allocatable and c["employment_status"] == "confirmed",
            organizational_transfer_candidate=allocatable
            and "organizational_transfer_candidate" in c["interpretations"]
            and c["corporate_status"] in {"unknown", "confirmed"},
        )
    return bounded_output(
        dict(
            associations=sorted(associations, key=lambda r: (r["person_key"], r["record_id"])),
            episodes=episodes,
            candidates=candidates,
            corporate_changes=corporate_changes,
            unbound_reviews=unbound_reviews,
            coverage=dict(
                observations=len(observations),
                persons=sum(not k[0].startswith("ambiguous") for k in people),
                canonical_persons=sum(k[0] == "id" for k in people),
                missing_inventors=sum(not o.inventor_keys for o in observations),
                name_only_associations=sum(
                    k[0] == "name" for o in observations for k in o.inventor_keys
                ),
                missing_dates=sum(o.observed_date.start is None for o in observations),
                missing_applicants=sum(not o.applicant_ids for o in observations),
                ambiguous_associations=sum(
                    k[0].startswith("ambiguous") for o in observations for k in o.inventor_keys
                ),
                sidecar="provided" if snapshot else "input_not_provided",
            ),
            provenance=dict(
                kernel_version="mobility.1",
                minimum_observations=minimum_observations,
                maximum_gap_years=maximum_gap_years,
                date_basis="input_observation_kind",
                candidate_period_basis="preceding_end_to_following_start",
                gap_threshold_basis="calendar_boundary_year_distance",
                matching_period_basis="boundary_episode_uncertainty_envelope",
                review_binding_basis="explicit_candidate_ids"
                if review_bindings is not None
                else "unambiguous_exact_scope",
            ),
            disclaimers=list(DISCLAIMERS),
        )
    )


def _rights_only_without_personal_evidence(candidate):
    return (
        bool(candidate["corporate_matches"])
        and all(
            m["type"] == "patent_rights_transfer" or m["scope"] == "patents_only"
            for m in candidate["corporate_matches"]
        )
        and not any(e["direct_employment_support"] for e in candidate["evidence"])
    )


def _run_counts(episodes, maximum_gap_years):
    counts = []
    previous = None
    for episode, rows in episodes:
        count = 0 if episode["unknown_applicants"] else len(rows)
        if (
            previous
            and not episode["unknown_applicants"]
            and not previous["unknown_applicants"]
            and previous["applicant_ids"] == episode["applicant_ids"]
            and abs(int(previous["start"][:4]) - int(episode["start"][:4])) <= maximum_gap_years
        ):
            count += counts[-1]
        counts.append(count)
        previous = episode
    return counts


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


def build_mobility_evidence(
    observations: tuple[PatentObservation, ...],
    snapshot: SidecarSnapshot | None = None,
    *,
    minimum_observations: int = 1,
    maximum_gap_years: int = 5,
    review_bindings: Mapping[str, tuple[str, ...]] | None = None,
) -> dict:
    """M10 retains all M08 rows and histories, with identical canonical candidate IDs."""
    return build_mobility(
        observations,
        snapshot,
        minimum_observations=minimum_observations,
        maximum_gap_years=maximum_gap_years,
        review_bindings=review_bindings,
    )


def build_mobility_flow(
    observations: tuple[PatentObservation, ...],
    snapshot: SidecarSnapshot | None = None,
    *,
    axis: str = "legal",
    layer: str = "observed_association_change",
    statuses: tuple[str, ...] | None = None,
    minimum_observations: int = 1,
    maximum_gap_years: int = 5,
    review_bindings: Mapping[str, tuple[str, ...]] | None = None,
) -> dict:
    """Aggregate the exact shared candidate set; no company-name inference or Cartesian edges."""
    if axis not in {"legal", "historical_group"} or layer not in {
        "observed_association_change",
        "individual_move_candidate",
        "confirmed_employment_move",
        "organizational_transfer_candidate",
    }:
        _fail()
    defaults = {
        "observed_association_change": ("observed",),
        "individual_move_candidate": ("candidate",),
        "confirmed_employment_move": ("confirmed",),
        "organizational_transfer_candidate": ("candidate", "confirmed"),
    }
    allowed = {
        "observed",
        "candidate",
        "unknown",
        "confirmed",
        "user_asserted",
        "pending",
        "rejected",
        "withdrawn",
        "conflicting",
    }
    if statuses is None:
        statuses = defaults[layer]
    if (
        not isinstance(statuses, tuple)
        or not statuses
        or len(statuses) > len(allowed)
        or len(set(statuses)) != len(statuses)
        or not set(statuses) <= allowed
    ):
        _fail()
    result = build_mobility(
        observations,
        snapshot,
        minimum_observations=minimum_observations,
        maximum_gap_years=maximum_gap_years,
        review_bindings=review_bindings,
    )
    return _legacy_flows(result, axis, layer, statuses)


def _legacy_flows(result, axis, layer, statuses):
    buckets = defaultdict(list)
    unallocated = []
    episode_index = {e["episode_id"]: e for e in result["episodes"]}
    relation_index = {a["record_id"]: a["group_relations"] for a in result["associations"]}
    for c in result["candidates"]:
        status = (
            c["observed_status"]
            if layer == "observed_association_change"
            else c["employment_status"]
            if layer == "confirmed_employment_move"
            else c["corporate_status"]
            if layer == "organizational_transfer_candidate"
            else c["candidate_status"]
        )
        if layer == "organizational_transfer_candidate" and status == "unknown":
            status = "candidate"
        reason = None
        if c["canonical_inventor_id"] is None:
            reason = "unconfirmed_identity"
        elif (
            len(c["removed_ids"]) != 1
            or len(c["added_ids"]) != 1
            or len(c["from_ids"]) != 1
            or len(c["to_ids"]) != 1
        ):
            reason = "multivalue_or_missing_origin_destination"
        elif "unknown_applicants" in c["reason_codes"]:
            reason = "unknown_applicants"
        elif layer in {"individual_move_candidate", "confirmed_employment_move"} and (
            c["employment_status"] in {"conflicting", "rejected", "withdrawn", "pending"}
        ):
            reason = c["employment_status"]
        elif layer == "individual_move_candidate" and _rights_only_without_personal_evidence(c):
            reason = "rights_only_without_personal_evidence"
        elif layer == "confirmed_employment_move" and c["employment_status"] != "confirmed":
            reason = "employment_not_confirmed"
        elif layer == "organizational_transfer_candidate" and (
            c["corporate_status"] in {"conflicting", "rejected", "withdrawn", "pending"}
        ):
            reason = c["corporate_status"]
        elif layer == "organizational_transfer_candidate" and (
            "organizational_transfer_candidate" not in c["interpretations"]
        ):
            reason = "no_organizational_transfer_support"
        elif status not in statuses:
            reason = "status_not_selected"
        origin = c["removed_ids"][0] if len(c["removed_ids"]) == 1 else None
        destination = c["added_ids"][0] if len(c["added_ids"]) == 1 else None
        if not reason and axis == "historical_group":
            mapped = []
            for legal, episode_id in [
                (origin, c["preceding_episode_id"]),
                (destination, c["following_episode_id"]),
            ]:
                parents = set()
                for record_id in episode_index[episode_id]["record_ids"]:
                    rels = [
                        r
                        for r in relation_index[record_id]
                        if r["child_id"] == legal and r["controlling"]
                    ]
                    if not rels:
                        reason = "missing_group_mapping"
                        break
                    if len(rels) != 1 or rels[0]["strength"] != "definite":
                        reason = "uncertain_group_mapping"
                        break
                    parents.add(rels[0]["parent_id"])
                if len(parents) != 1:
                    reason = reason or "uncertain_group_mapping"
                mapped.append(next(iter(parents)) if len(parents) == 1 else None)
            origin, destination = mapped
            if not reason and origin == destination:
                reason = "same_historical_group"
        if reason:
            unallocated.append(
                dict(candidate_id=c["candidate_id"], reason=reason, layer=layer, status=status)
            )
            continue
        buckets[
            (
                origin,
                destination,
                status,
                c["employment_status"],
                c["corporate_status"],
                tuple(c["reason_codes"]),
            )
        ].append(c)
    flows = []
    for (origin, destination, status, employment, corporate, reasons), members in sorted(
        buckets.items()
    ):
        people = sorted({c["canonical_inventor_id"] for c in members})
        ids = sorted(c["candidate_id"] for c in members)
        flows.append(
            dict(
                flow_id=_stable_id(
                    "mf_",
                    [axis, layer, origin, destination, status, employment, corporate, reasons],
                ),
                from_id=origin,
                to_id=destination,
                layer=layer,
                status=status,
                employment_status=employment,
                corporate_status=corporate,
                reason_codes=list(reasons),
                unique_inventors=len(people),
                transition_events=len(ids),
                inventor_ids=people,
                candidate_ids=ids,
            )
        )
    result["flows"] = flows
    result["nodes"] = [
        dict(entity_id=i)
        for i in sorted({f["from_id"] for f in flows} | {f["to_id"] for f in flows})
    ]
    result["unallocated"] = unallocated
    result["provenance"].update(
        axis=axis,
        layer=layer,
        statuses=sorted(statuses),
        network_kind="directed_legal_network_cycles_permitted"
        if axis == "legal"
        else "directed_historical_group_network_cycles_permitted",
    )
    return bounded_output(result)


def _review_component_seeds(reviews):
    """One seed per attached supersession component; original binding cap stays 64."""
    links = defaultdict(set)
    remaining = {r["review_id"] for r in reviews}
    for r in reviews:
        parent = r["supersedes_review_id"]
        if parent is not None:
            links[r["review_id"]].add(parent)
            links[parent].add(r["review_id"])
    seeds = []
    while remaining:
        seed = min(remaining)
        seeds.append(seed)
        remaining.remove(seed)
        stack = [seed]
        while stack:
            for linked in links[stack.pop()] & remaining:
                remaining.remove(linked)
                stack.append(linked)
    return tuple(seeds)


def _verified_mobility(mobility, observations, snapshot):
    """Rebuild with authoritative thresholds and the explicit review component bindings.

    The entire M08 audit must match, not just claimed statuses or candidate IDs.
    Explicit seeds can be reconstructed from their attached review components:
    rebinding the full component preserves supersession/branch semantics.
    """
    try:
        if not isinstance(mobility, dict):
            _fail()
        bounded_output(mobility)
        provenance = mobility["provenance"]
        basis = provenance["review_binding_basis"]
        if basis not in {"explicit_candidate_ids", "unambiguous_exact_scope"}:
            _fail()
        bindings = (
            {
                c["candidate_id"]: _review_component_seeds(c["reviews"])
                for c in mobility["candidates"]
            }
            if basis == "explicit_candidate_ids"
            else None
        )
        verified = build_mobility(
            observations,
            snapshot,
            minimum_observations=provenance["minimum_observations"],
            maximum_gap_years=provenance["maximum_gap_years"],
            review_bindings=bindings,
        )
        if json.dumps(mobility, sort_keys=True, allow_nan=False) != json.dumps(
            verified, sort_keys=True, allow_nan=False
        ):
            _fail()
        return verified
    except DatasetInputError:
        raise
    except (KeyError, TypeError, ValueError, RecursionError, OverflowError):
        _fail()


def _fractional_reason(c, layer, status):
    if c["canonical_inventor_id"] is None:
        return "unconfirmed_identity"
    if "unknown_applicants" in c["reason_codes"]:
        return "unknown_applicants"
    if not c["removed_ids"] or not c["added_ids"]:
        return "multivalue_or_missing_origin_destination"
    if layer == "confirmed_employment_move" and (len(c["from_ids"]) != 1 or len(c["to_ids"]) != 1):
        return "multivalue_or_missing_origin_destination"
    if layer != "observed_association_change":
        if c["employment_status"] in {"conflicting", "rejected", "withdrawn", "pending"}:
            return c["employment_status"]
        if layer == "individual_move_candidate" and _rights_only_without_personal_evidence(c):
            return "rights_only_without_personal_evidence"
        if layer == "confirmed_employment_move" and c["employment_status"] != "confirmed":
            return "employment_not_confirmed"
    if layer == "individual_move_candidate" and c["candidate_status"] != status:
        return "status_not_selected"
    return None


def _fractional_pairs(c):
    for origin in c["removed_ids"]:
        for destination in c["added_ids"]:
            yield origin, destination


def _historical_mapping(legal, episode, relations):
    parents = set()
    for record_id in episode["record_ids"]:
        rels = relations.get((record_id, legal), ())
        if not rels:
            return None, "missing_group_mapping"
        if len(rels) != 1 or rels[0]["strength"] != "definite":
            return None, "uncertain_group_mapping"
        parents.add(rels[0]["parent_id"])
    if len(parents) != 1:
        return None, "uncertain_group_mapping"
    return next(iter(parents)), None


def _fractional_flows(result, axis, layer, selected_status):
    # Count potential contributions BEFORE creating any Cartesian pair.
    count = sum(max(1, len(c["removed_ids"]) * len(c["added_ids"])) for c in result["candidates"])
    if count > MAX_ROWS or count > MAX_COMPARISONS:
        _fail(True)
    # Conservative contribution reservation, including refs/rational cell scaffolding.
    # This is a refusal gate, not a promise that every smaller input fits the output.
    estimate = len(json.dumps(result, ensure_ascii=False, allow_nan=False).encode("utf-8"))
    estimate += 128 * count
    estimate += sum(
        sum(len(i.encode("utf-8")) for i in c["removed_ids"]) * len(c["added_ids"])
        + sum(len(i.encode("utf-8")) for i in c["added_ids"]) * len(c["removed_ids"])
        for c in result["candidates"]
    )
    if estimate > MAX_OUTPUT_BYTES:
        _fail(True)
    episodes = {e["episode_id"]: e for e in result["episodes"]}
    relations = defaultdict(list)
    # Each record occurs in several person associations; index it just once.
    seen = set()
    for a in result["associations"]:
        if a["record_id"] not in seen:
            for r in a["group_relations"]:
                if r["controlling"]:
                    relations[a["record_id"], r["child_id"]].append(r)
            seen.add(a["record_id"])
    comparisons = count
    if axis == "group":
        comparisons += sum(
            sum(
                max(1, len(relations[record, legal]))
                for record in episodes[c[episode]]["record_ids"]
                for legal in c[ids]
            )
            for c in result["candidates"]
            for episode, ids in [
                ("preceding_episode_id", "removed_ids"),
                ("following_episode_id", "added_ids"),
            ]
        )
    if comparisons > MAX_COMPARISONS:
        _fail(True)
    mapping_cache = {}
    buckets = {}
    unallocated = []
    budget = _RowBudget()
    for c in result["candidates"]:
        status = (
            c["observed_status"]
            if layer == "observed_association_change"
            else c["employment_status"]
            if layer == "confirmed_employment_move"
            else c["candidate_status"]
        )
        reason = _fractional_reason(c, layer, selected_status)
        if reason:
            budget.append(
                unallocated,
                dict(
                    candidate_id=c["candidate_id"],
                    reason=reason,
                    layer=layer,
                    status=status,
                    event_mass=exact(int(c["canonical_inventor_id"] is not None)),
                ),
            )
            continue
        weight = Fraction(1, len(c["removed_ids"]) * len(c["added_ids"]))
        for legal_origin, legal_destination in _fractional_pairs(c):
            origin, destination = legal_origin, legal_destination
            pair_reason = None
            if axis == "group":
                mapped = []
                for legal, ep in [
                    (legal_origin, c["preceding_episode_id"]),
                    (legal_destination, c["following_episode_id"]),
                ]:
                    if (legal, ep) not in mapping_cache:
                        mapping_cache[legal, ep] = _historical_mapping(
                            legal, episodes[ep], relations
                        )
                    parent, mapping_reason = mapping_cache[legal, ep]
                    pair_reason = pair_reason or mapping_reason
                    mapped.append(parent)
                origin, destination = mapped
                if not pair_reason and origin == destination:
                    pair_reason = "same_historical_group"
            if not pair_reason and origin == destination:
                pair_reason = "self_edge"
            if pair_reason:
                budget.append(
                    unallocated,
                    dict(
                        candidate_id=c["candidate_id"],
                        reason=pair_reason,
                        layer=layer,
                        status=status,
                        event_mass=exact(weight),
                        from_legal_id=legal_origin,
                        to_legal_id=legal_destination,
                        from_id=origin,
                        to_id=destination,
                    ),
                )
                continue
            budget.spend([c["candidate_id"], origin, destination, exact(weight)])
            key = (
                origin,
                destination,
                status,
                c["employment_status"],
                c["corporate_status"],
                tuple(c["reason_codes"]),
            )
            mass, members = buckets.setdefault(key, (Fraction(), {}))
            members[c["candidate_id"]] = c
            buckets[key] = (mass + weight, members)
    flows = []
    masses = {}
    for (origin, destination, status, employment, corporate, reasons), (mass, members) in sorted(
        buckets.items()
    ):
        people = sorted({c["canonical_inventor_id"] for c in members.values()})
        flow_id = _stable_id(
            "mff_", [axis, layer, origin, destination, status, employment, corporate, reasons]
        )
        masses[flow_id] = mass
        budget.append(
            flows,
            dict(
                flow_id=flow_id,
                from_id=origin,
                to_id=destination,
                layer=layer,
                status=status,
                employment_status=employment,
                corporate_status=corporate,
                reason_codes=list(reasons),
                unique_inventors=len(people),
                transition_events=len(members),
                inventor_ids=people,
                candidate_ids=sorted(members),
            ),
        )
    result["flows"] = flows
    result["nodes"] = [
        dict(entity_id=i)
        for i in sorted({f["from_id"] for f in flows} | {f["to_id"] for f in flows})
    ]
    result["unallocated"] = unallocated
    result["provenance"].update(
        layer=layer,
        statuses=[selected_status],
        network_kind="directed_legal_network_cycles_permitted"
        if axis == "legal_entity"
        else "directed_historical_group_network_cycles_permitted",
    )
    return result, masses


def organization_flows(
    mobility: dict,
    observations: tuple[PatentObservation, ...],
    snapshot: SidecarSnapshot | None,
    *,
    axis: str = "legal_entity",
    mode: str = "observations",
    allocation: str = "unique_inventors",
) -> dict:
    """Verified M08 audit plus conservative organization flows (separate M09 contract).

    Unique weights count canonical people within each strict legacy bucket.
    Fractional weights are candidate-EVENT mass, NOT fractional headcount:
    each adopted event contributes 1/(removed origins * added destinations)
    to actual removed->added pairs only; retained applicants never contribute.
    Unmapped/uncertain/self group pairs keep their original fractional mass
    in unallocated without renormalizing. Canonical candidate events (including
    exclusions) have mass one; name-only candidates have mass zero. Confirmed
    mode refuses all multivalued boundary sets, even with broad reviews.
    No caller-owned object is mutated. Historical groups are boundary-specific
    definite direct controlling parents, never current-parent backfill.
    """
    if (
        type(axis) is not str
        or axis not in {"legal_entity", "group"}
        or type(mode) is not str
        or mode not in {"observations", "candidate_moves", "confirmed_moves"}
        or type(allocation) is not str
        or allocation not in {"unique_inventors", "fractional_flows"}
    ):
        _fail()
    result = _verified_mobility(mobility, observations, snapshot)
    layer, status = {
        "observations": ("observed_association_change", "observed"),
        "candidate_moves": ("individual_move_candidate", "candidate"),
        "confirmed_moves": ("confirmed_employment_move", "confirmed"),
    }[mode]
    legacy_axis = "legal" if axis == "legal_entity" else "historical_group"
    masses = {}
    if allocation == "unique_inventors":
        result = _legacy_flows(result, legacy_axis, layer, (status,))
    else:
        result, masses = _fractional_flows(result, axis, layer, status)
    basis = (
        "unique_canonical_inventors_per_bucket"
        if allocation == "unique_inventors"
        else "fractional_candidate_event_mass"
    )
    if len(result["nodes"]) > MAX_ROWS:
        _fail(True)
    candidates = {c["candidate_id"]: c for c in result["candidates"]}
    budget = _RowBudget()
    for flow in result["flows"]:
        members = [candidates[i] for i in flow["candidate_ids"]]
        flow.update(
            axis=axis,
            mode=mode,
            allocation=allocation,
            weight_basis=basis,
            flow_weight=exact(
                flow["unique_inventors"]
                if allocation == "unique_inventors"
                else masses[flow["flow_id"]]
            ),
            event_mass=exact(masses.get(flow["flow_id"], Fraction(flow["transition_events"]))),
            record_ids=sorted({i for c in members for i in c["record_ids"]}),
            source_ids=sorted({i for c in members for i in c["source_ids"]}),
            evidence_ids=sorted({e["evidence_id"] for c in members for e in c["evidence"]}),
            review_ids=sorted({r["review_id"] for c in members for r in c["reviews"]}),
            event_ids=sorted({e["event_id"] for c in members for e in c["corporate_matches"]}),
        )
        budget.spend(flow)
    for row in result["unallocated"]:
        c = candidates[row["candidate_id"]]
        row.update(
            axis=axis,
            mode=mode,
            allocation=allocation,
            weight_basis=basis,
            employment_status=c["employment_status"],
            corporate_status=c["corporate_status"],
            reason_codes=list(c["reason_codes"]),
            event_mass=row.get("event_mass", exact(int(c["canonical_inventor_id"] is not None))),
            from_legal_id=row.get("from_legal_id"),
            to_legal_id=row.get("to_legal_id"),
            from_id=row.get("from_id"),
            to_id=row.get("to_id"),
        )
        budget.spend(row)
    allocated = sum(
        (
            Fraction(int(f["event_mass"]["numerator"]), int(f["event_mass"]["denominator"]))
            for f in result["flows"]
        ),
        Fraction(),
    )
    excluded = sum(
        (
            Fraction(int(r["event_mass"]["numerator"]), int(r["event_mass"]["denominator"]))
            for r in result["unallocated"]
        ),
        Fraction(),
    )
    eligible = sum(c["canonical_inventor_id"] is not None for c in result["candidates"])
    if allocated + excluded != eligible:
        _fail()
    result["allocation_summary"] = dict(
        allocation=allocation,
        weight_basis=basis,
        mass_basis="canonical_candidate_events",
        eligible_events=eligible,
        allocated_event_mass=exact(allocated),
        unallocated_event_mass=exact(excluded),
        total_event_mass=exact(allocated + excluded),
    )
    result["provenance"].update(axis=axis, mode=mode, allocation=allocation, weight_basis=basis)
    return bounded_output(result)
