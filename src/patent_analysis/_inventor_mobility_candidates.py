"""Observed mobility episodes and association-change candidates."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping

from patent_analysis._inventor_mobility_common import (
    DISCLAIMERS,
    MAX_COMPARISONS,
    MAX_OBSERVATIONS,
    MAX_PERSONS,
    MAX_ROWS,
    _fail,
    _RowBudget,
    _stable_id,
)
from patent_analysis._inventor_mobility_evidence import _apply_evidence
from patent_analysis.corporate_history import (
    bounded_output,
    corporate_aliases,
    corporate_relations,
    date_data,
    match_corporate_events,
)
from patent_analysis.inventor_models import PatentObservation
from patent_analysis.inventor_sidecars import SidecarSnapshot, validate_observation_references


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
