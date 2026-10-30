"""Conservative organization flows from verified mobility candidates."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping
from fractions import Fraction

from patent_analysis._inventor_mobility_candidates import (
    _rights_only_without_personal_evidence,
    build_mobility,
)
from patent_analysis._inventor_mobility_common import (
    MAX_COMPARISONS,
    MAX_ROWS,
    _fail,
    _RowBudget,
    _stable_id,
)
from patent_analysis._inventor_mobility_verification import _verified_mobility
from patent_analysis.corporate_history import MAX_OUTPUT_BYTES, bounded_output
from patent_analysis.inventor_models import PatentObservation
from patent_analysis.inventor_numeric import exact
from patent_analysis.inventor_sidecars import SidecarSnapshot


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
