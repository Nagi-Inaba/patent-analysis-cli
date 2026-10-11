import json
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
from types import MappingProxyType

import pytest
from test_corporate_history import event, group, snapshot

from patent_analysis.errors import DatasetInputError
from patent_analysis.inventor_identity import Alias, IdentityResolver
from patent_analysis.inventor_mobility import (
    build_mobility,
    build_mobility_evidence,
    build_mobility_flow,
    organization_flows,
)
from patent_analysis.inventor_models import PatentObservation, parse_observation_date
from patent_analysis.inventor_sidecars import TABLE_IDS, SidecarSnapshot, read_inventor_sidecar


def obs(record, when, applicants=("A",), person="i", **kwargs):
    identity = IdentityResolver().resolve(inventor_id=person)
    return PatentObservation(
        record,
        (identity,),
        parse_observation_date(when, kind="filing"),
        applicant_ids=applicants,
        **kwargs,
    )


def test_organization_unique_adapter_preserves_legacy_buckets_and_event_basis():
    rows = (
        obs("r1", "2020"),
        obs("r2", "2021", ("B",)),
        obs("r3", "2022"),
        obs("r4", "2023", ("B",)),
    )
    mobility = build_mobility(rows)
    before = json.dumps(mobility, sort_keys=True)
    result = organization_flows(mobility, rows, None)
    legacy = build_mobility_flow(rows)
    for actual, original in zip(result["flows"], legacy["flows"], strict=True):
        assert {k: actual[k] for k in original} == original
    forward = result["flows"][0]
    assert forward["flow_weight"] == {"value": 1.0, "numerator": "1", "denominator": "1"}
    assert forward["unique_inventors"] == 1 and forward["transition_events"] == 2
    assert forward["event_mass"]["numerator"] == "2"
    assert forward["weight_basis"] == "unique_canonical_inventors_per_bucket"
    assert forward["record_ids"] == ["r1", "r2", "r3", "r4"]
    assert json.dumps(mobility, sort_keys=True) == before
    assert result["candidates"] == mobility["candidates"]


def test_fractional_multivalued_change_is_event_mass_not_headcount():
    rows = (obs("r1", "2020", ("A", "B")), obs("r2", "2021", ("C", "D")))
    mobility = build_mobility(rows)
    result = organization_flows(mobility, rows, None, allocation="fractional_flows")
    assert [(f["from_id"], f["to_id"]) for f in result["flows"]] == [
        ("A", "C"),
        ("A", "D"),
        ("B", "C"),
        ("B", "D"),
    ]
    for f in result["flows"]:
        assert f["flow_weight"] == {"value": 0.25, "numerator": "1", "denominator": "4"}
        assert f["event_mass"] == f["flow_weight"]
        assert f["unique_inventors"] == f["transition_events"] == 1
        assert f["weight_basis"] == "fractional_candidate_event_mass"
        assert f["candidate_ids"] == [mobility["candidates"][0]["candidate_id"]]
    assert result["unallocated"] == []
    summary = result["allocation_summary"]
    assert summary["eligible_events"] == 1
    assert summary["allocated_event_mass"]["numerator"] == "1"
    assert summary["total_event_mass"]["numerator"] == "1"
    assert result["candidates"] == mobility["candidates"]


def test_fractional_group_partial_same_group_keeps_excluded_quarter_mass():
    rows = (obs("r1", "2020", ("A", "B")), obs("r2", "2021", ("C", "D")))
    s = snapshot(
        entities=[
            dict(entity_id=i, display_name=i, source_ids=("s",))
            for i in ("A", "B", "C", "D", "P", "Q", "R")
        ],
        groups=[
            dict(group(), group_id=f"g{i}", child_id=i, parent_id=p)
            for i, p in [("A", "P"), ("B", "Q"), ("C", "P"), ("D", "R")]
        ],
    )
    mobility = build_mobility(rows, s)
    result = organization_flows(mobility, rows, s, axis="group", allocation="fractional_flows")
    assert [(f["from_id"], f["to_id"]) for f in result["flows"]] == [
        ("P", "R"),
        ("Q", "P"),
        ("Q", "R"),
    ]
    assert all(f["flow_weight"]["denominator"] == "4" for f in result["flows"])
    u = result["unallocated"][0]
    assert u["reason"] == "same_historical_group"
    assert u["from_legal_id"] == "A" and u["to_legal_id"] == "C"
    assert u["from_id"] == u["to_id"] == "P"
    assert u["event_mass"] == {"value": 0.25, "numerator": "1", "denominator": "4"}
    summary = result["allocation_summary"]
    assert summary["allocated_event_mass"]["numerator"] == "3"
    assert summary["allocated_event_mass"]["denominator"] == "4"
    assert summary["unallocated_event_mass"] == u["event_mass"]
    assert summary["total_event_mass"]["numerator"] == "1"


def test_fractional_byte_budget_preflights_before_cartesian_generator(monkeypatch):
    import patent_analysis.inventor_mobility as module

    rows = (
        obs("r1", "2020", tuple(f"A{i}" for i in range(64))),
        obs("r2", "2021", tuple(f"B{i}" for i in range(64))),
    )
    mobility = build_mobility(rows)
    monkeypatch.setattr(
        module, "_fractional_pairs", lambda *args: pytest.fail("Cartesian expansion started")
    )
    with pytest.raises(DatasetInputError, match="limits"):
        organization_flows(mobility, rows, None, allocation="fractional_flows")


def mass(cell):
    return Fraction(int(cell["numerator"]), int(cell["denominator"]))


def assert_conserved(result):
    summary = result["allocation_summary"]
    assert sum((mass(f["event_mass"]) for f in result["flows"]), Fraction()) == mass(
        summary["allocated_event_mass"]
    )
    assert sum((mass(u["event_mass"]) for u in result["unallocated"]), Fraction()) == mass(
        summary["unallocated_event_mass"]
    )
    assert (
        mass(summary["allocated_event_mass"]) + mass(summary["unallocated_event_mass"])
        == (mass(summary["total_event_mass"]))
        == summary["eligible_events"]
    )


def test_fractional_recurrence_and_retained_coapplicant_never_fractional_headcount():
    rows = (
        obs("r1", "2020", ("A", "C")),
        obs("r2", "2021", ("B", "C")),
        obs("r3", "2022", ("A", "C")),
        obs("r4", "2023", ("B", "C")),
    )
    result = organization_flows(build_mobility(rows), rows, None, allocation="fractional_flows")
    assert [
        (
            f["from_id"],
            f["to_id"],
            f["unique_inventors"],
            f["transition_events"],
            mass(f["flow_weight"]),
        )
        for f in result["flows"]
    ] == [("A", "B", 1, 2, 2), ("B", "A", 1, 1, 1)]
    assert_conserved(result)
    unique = organization_flows(build_mobility(rows), rows, None)
    assert unique["flows"] == []
    assert all(
        u["reason"] == "multivalue_or_missing_origin_destination" for u in unique["unallocated"]
    )
    assert_conserved(unique)


@pytest.mark.parametrize("status", ["rejected", "pending", "withdrawn", "conflicting"])
@pytest.mark.parametrize("allocation", ["unique_inventors", "fractional_flows"])
def test_adapter_review_gates_never_depend_on_allocation(status, allocation):
    rows = change_rows()
    s = job_snapshot(reviews=[review(status=status)])
    mobility = build_mobility(rows, s)
    for mode in ("candidate_moves", "confirmed_moves"):
        result = organization_flows(mobility, rows, s, mode=mode, allocation=allocation)
        assert result["flows"] == []
        assert result["unallocated"][0]["reason"] == status
        assert result["candidates"] == mobility["candidates"]
        assert_conserved(result)
    observed = organization_flows(mobility, rows, s, allocation=allocation)
    assert len(observed["flows"]) == 1
    assert observed["flows"][0]["employment_status"] == status
    assert_conserved(observed)


@pytest.mark.parametrize("allocation", ["unique_inventors", "fractional_flows"])
def test_adapter_rights_only_is_not_candidate_or_confirmed_employment(allocation):
    rows = change_rows()
    s = job_snapshot(
        evidences=[],
        reviews=[],
        events=[event(type="patent_rights_transfer", scope="patents_only")],
    )
    mobility = build_mobility(rows, s)
    candidate = organization_flows(mobility, rows, s, mode="candidate_moves", allocation=allocation)
    assert candidate["flows"] == []
    assert candidate["unallocated"][0]["reason"] == "rights_only_without_personal_evidence"
    assert_conserved(candidate)
    confirmed = organization_flows(mobility, rows, s, mode="confirmed_moves", allocation=allocation)
    assert confirmed["flows"] == []
    assert confirmed["unallocated"][0]["reason"] == "employment_not_confirmed"
    assert_conserved(confirmed)
    observed = organization_flows(mobility, rows, s, allocation=allocation)
    assert len(observed["flows"]) == 1
    assert observed["flows"][0]["event_ids"] == ["e"]


def test_multivalued_confirmed_mode_never_invents_pairwise_employment():
    rows = (obs("r1", "2020", ("A", "B")), obs("r2", "2021", ("C", "D")))
    s = job_snapshot(
        evidences=[evidence(to_entity_id="C")],
        entities=[
            dict(entity_id=i, display_name=i, source_ids=("s",)) for i in ("A", "B", "C", "D")
        ],
    )
    mobility = build_mobility(rows, s)
    result = organization_flows(
        mobility, rows, s, mode="confirmed_moves", allocation="fractional_flows"
    )
    assert result["flows"] == []
    assert result["unallocated"][0]["reason"] == "multivalue_or_missing_origin_destination"
    assert mass(result["unallocated"][0]["event_mass"]) == 1
    assert_conserved(result)
    forged = deepcopy(mobility)
    forged["candidates"][0]["employment_status"] = "confirmed"
    with pytest.raises(DatasetInputError, match="input is invalid"):
        organization_flows(forged, rows, s, mode="confirmed_moves", allocation="fractional_flows")


@pytest.mark.parametrize("uncertain", [False, True])
def test_fractional_group_missing_or_uncertain_mapping_never_backfills(uncertain):
    rows = (obs("r1", "2020", ("A", "B")), obs("r2", "2021", ("C",)))
    groups = [group(), dict(group(), group_id="gc", child_id="C", parent_id="Q")]
    if uncertain:
        groups.append(dict(group(start=None), group_id="gb", child_id="B"))
    s = snapshot(groups=groups)
    result = organization_flows(
        build_mobility(rows, s), rows, s, axis="group", allocation="fractional_flows"
    )
    assert len(result["flows"]) == len(result["unallocated"]) == 1
    assert mass(result["flows"][0]["flow_weight"]) == Fraction(1, 2)
    u = result["unallocated"][0]
    assert u["reason"] == ("uncertain_group_mapping" if uncertain else "missing_group_mapping")
    assert u["from_id"] is None and u["to_id"] == "Q"
    assert mass(u["event_mass"]) == Fraction(1, 2)
    assert_conserved(result)


def test_fractional_group_multiple_legal_pairs_can_merge_without_event_overcount():
    rows = (obs("r1", "2020", ("A", "B")), obs("r2", "2021", ("C",)))
    s = snapshot(
        groups=[
            group(),
            dict(group(), group_id="gb", child_id="B"),
            dict(group(), group_id="gc", child_id="C", parent_id="Q"),
        ]
    )
    result = organization_flows(
        build_mobility(rows, s), rows, s, axis="group", allocation="fractional_flows"
    )
    assert len(result["flows"]) == 1
    f = result["flows"][0]
    assert f["unique_inventors"] == f["transition_events"] == 1
    assert mass(f["flow_weight"]) == 1
    assert_conserved(result)


@pytest.mark.parametrize("mode", ["observations", "candidate_moves", "confirmed_moves"])
def test_fractional_missing_endpoint_never_distributes_unknown(mode):
    rows = (obs("r1", "2020", ()), obs("r2", "2021", ("B", "C")))
    result = organization_flows(
        build_mobility(rows), rows, None, mode=mode, allocation="fractional_flows"
    )
    assert result["flows"] == []
    assert result["unallocated"][0]["reason"] == "unknown_applicants"
    assert mass(result["unallocated"][0]["event_mass"]) == 1
    assert_conserved(result)


def test_fractional_name_only_and_ambiguous_people_are_not_eligible_mass():
    name = IdentityResolver().resolve(name="Name")
    ambiguous = IdentityResolver(
        (Alias("name", "Same", "x", "Same", ("s",), "candidate"),)
    ).resolve(name="Same")
    rows = tuple(
        PatentObservation(
            r, (name, ambiguous), parse_observation_date(d, kind="filing"), applicant_ids=(a,)
        )
        for r, d, a in [("r1", "2020", "A"), ("r2", "2021", "B")]
    )
    result = organization_flows(build_mobility(rows), rows, None, allocation="fractional_flows")
    assert result["flows"] == []
    assert len(result["unallocated"]) == 1
    assert result["unallocated"][0]["reason"] == "unconfirmed_identity"
    assert result["allocation_summary"]["eligible_events"] == 0
    assert result["coverage"]["ambiguous_associations"] == 2
    assert_conserved(result)


@pytest.mark.parametrize("which", ["axis", "mode", "allocation"])
@pytest.mark.parametrize("value", [True, float("nan"), float("inf"), "unknown", [], None])
def test_organization_enums_are_exact_and_fail_safely(which, value):
    rows = change_rows()
    with pytest.raises(DatasetInputError, match="input is invalid"):
        organization_flows(build_mobility(rows), rows, None, **{which: value})


@pytest.mark.parametrize(
    "field,value",
    [
        ("employment_status", "confirmed"),
        ("preceding_observation_count", True),
        ("gap_year_distance", float("inf")),
    ],
)
def test_adapter_rejects_forged_audit_fields(field, value):
    rows = change_rows()
    mobility = build_mobility(rows)
    mobility["candidates"][0][field] = value
    with pytest.raises(DatasetInputError, match="input is invalid"):
        organization_flows(
            mobility, rows, None, mode="confirmed_moves", allocation="fractional_flows"
        )


def test_adapter_preserves_explicit_bindings_thresholds_and_input_permutation():
    rows = (
        obs("r1", "2020"),
        obs("r2", "2021", ("B",)),
        obs("r3", "2022"),
        obs("r4", "2023", ("B",)),
    )
    s = job_snapshot(
        evidences=[evidence(valid_from="2020", valid_to="2023")], reviews=[review(record_ids=())]
    )
    baseline = build_mobility(rows, s)
    cid = baseline["candidates"][0]["candidate_id"]
    mobility = build_mobility(
        rows, s, minimum_observations=2, maximum_gap_years=1, review_bindings={cid: ("v",)}
    )
    before = deepcopy(mobility)
    for allocation in ("unique_inventors", "fractional_flows"):
        result = organization_flows(
            mobility, rows, s, mode="confirmed_moves", allocation=allocation
        )
        assert len(result["flows"]) == 1
        assert result["flows"][0]["candidate_ids"] == [cid]
        assert result["flows"][0]["evidence_ids"] == ["p"]
        assert result["flows"][0]["review_ids"] == ["v"]
        assert result["candidates"] == mobility["candidates"]
        assert result["provenance"]["minimum_observations"] == 2
        assert result["provenance"]["maximum_gap_years"] == 1
        assert result == organization_flows(
            mobility, tuple(reversed(rows)), s, mode="confirmed_moves", allocation=allocation
        )
        assert_conserved(result)
    assert mobility == before
    with pytest.raises(DatasetInputError):
        organization_flows(mobility, rows, None, mode="confirmed_moves")
    with pytest.raises(DatasetInputError):
        organization_flows(
            mobility, (rows[0], replace(rows[1], applicant_ids=("C",))) + rows[2:], s
        )


@pytest.mark.parametrize("limit", ["MAX_ROWS", "MAX_COMPARISONS"])
def test_fractional_row_and_operation_preflight_precedes_expansion(monkeypatch, limit):
    import patent_analysis.inventor_mobility as module

    rows = (obs("r1", "2020", ("A", "B")), obs("r2", "2021", ("C", "D")))
    mobility = build_mobility(rows)
    monkeypatch.setattr(module, limit, 3)
    monkeypatch.setattr(module, "_fractional_pairs", lambda *args: pytest.fail("expansion started"))
    with pytest.raises(DatasetInputError, match="limits"):
        organization_flows(mobility, rows, None, allocation="fractional_flows")


def test_verified_adapter_preserves_long_explicit_supersession_component():
    rows = change_rows()
    s = job_snapshot(
        reviews=[
            review(review_id=f"v{i:02}", supersedes_review_id=f"v{i - 1:02}" if i else None)
            for i in range(65)
        ]
    )
    cid = build_mobility(rows, s)["candidates"][0]["candidate_id"]
    mobility = build_mobility(rows, s, review_bindings={cid: ("v64",)})
    result = organization_flows(mobility, rows, s, mode="confirmed_moves")
    assert result["candidates"] == mobility["candidates"]
    assert len(result["flows"][0]["review_ids"]) == 65
    assert result["provenance"]["review_binding_basis"] == "explicit_candidate_ids"


def test_adapter_verification_preserves_safe_budget_error(monkeypatch):
    import patent_analysis.inventor_mobility as module

    rows = change_rows()
    mobility = build_mobility(rows)
    monkeypatch.setattr(module, "MAX_ROWS", 1)
    with pytest.raises(DatasetInputError, match="dataset input exceeds published limits"):
        organization_flows(mobility, rows, None)


def test_day_changes_are_observed_not_confirmed_employment():
    result = build_mobility((obs("r1", "2020-01-01"), obs("r2", "2020-12-01", ("B",))))
    assert len(result["candidates"]) == 1
    c = result["candidates"][0]
    assert c["from_ids"] == ["A"] and c["to_ids"] == ["B"]
    assert c["removed_ids"] == ["A"] and c["added_ids"] == ["B"]
    assert c["employment_status"] == "unknown"
    assert c["interpretations"] == ["individual_move_candidate", "unexplained_association_change"]
    assert c["preceding_dates"][0]["precision"] == "day"
    assert c["record_ids"] == ["r1", "r2"]


def test_overlapping_coarse_intervals_are_one_unordered_episode():
    result = build_mobility(
        (obs("r1", "2020"), obs("r2", "2020", ("B",)), obs("r3", "2020-06-01", ("C",)))
    )
    assert result["candidates"] == []
    assert len(result["episodes"]) == 1
    e = result["episodes"][0]
    assert e["parallel_association"] and e["unordered"]
    assert e["record_ids"] == ["r1", "r2", "r3"]
    assert [r["applicant_ids"] for r in e["observations"]] == [["A"], ["B"], ["C"]]


def test_unknown_applicant_episode_is_not_repaired_and_thresholds_preserve_candidates():
    rows = (
        obs("r1", "2000"),
        obs("r2", "2010", ()),
        obs("r3", "2011", ("B",)),
        obs("r4", None, ("C",)),
    )
    result = build_mobility(rows, minimum_observations=2, maximum_gap_years=5)
    assert len(result["candidates"]) == 2
    first, second = result["candidates"]
    assert first["to_ids"] == [] and second["from_ids"] == []
    assert first["candidate_status"] == second["candidate_status"] == "unknown"
    assert "unknown_applicants" in first["reason_codes"]
    assert "insufficient_observations" in first["reason_codes"]
    assert "gap_exceeds_threshold" in first["reason_codes"]
    assert first["missing_calendar_years"] == 9
    assert result["coverage"]["missing_dates"] == 1


def test_name_only_is_caveated_and_ambiguous_people_never_generate_transitions():
    resolver = IdentityResolver((Alias("name", "Same", "x", "Same", ("s",), "candidate"),))
    name = IdentityResolver().resolve(name="Name")
    ambiguous = resolver.resolve(name="Same")
    rows = tuple(
        PatentObservation(
            r, (name, ambiguous), parse_observation_date(d, kind="filing"), applicant_ids=(a,)
        )
        for r, d, a in [("r1", "2020", "A"), ("r2", "2021", "B")]
    )
    result = build_mobility(rows)
    assert len(result["candidates"]) == 1
    c = result["candidates"][0]
    assert c["canonical_inventor_id"] is None
    assert c["employment_status"] == "unknown"
    assert "name_match_is_not_person_confirmation" in c["reason_codes"]
    assert result["coverage"]["persons"] == 1
    assert result["coverage"]["canonical_persons"] == 0
    assert result["coverage"]["ambiguous_associations"] == 2


def test_same_legal_id_name_and_temporal_parent_changes_are_corporate_only():
    old = group("2010-01-01", "2020-12-31")
    new = dict(group("2021-01-01", "2030-12-31"), group_id="g2", parent_id="Q")
    s = snapshot(
        groups=[old, new],
        events=[event(type="name_change", entity_ids=("A",), effective_date="2020-06-01")],
    )
    result = build_mobility((obs("r1", "2020"), obs("r2", "2021")), s)
    assert result["candidates"] == []
    assert {r["type"] for r in result["corporate_changes"]} == {"name_change", "group_change"}
    assert all(not r["employment_confirmation"] for r in result["corporate_changes"])
    assert result["associations"][0]["group_relations"][0]["parent_id"] == "P"
    assert result["associations"][1]["group_relations"][0]["parent_id"] == "Q"


def test_acquisition_is_additional_interpretation_not_employment_confirmation():
    s = snapshot(events=[event()], sources=[dict(source_id="s", kind="corporate_record")])
    result = build_mobility((obs("r1", "2020-01-01"), obs("r2", "2020-12-31", ("B",))), s)
    c = result["candidates"][0]
    assert "organizational_transfer_candidate" in c["interpretations"]
    assert "individual_move_candidate" in c["interpretations"]
    assert c["corporate_status"] == "confirmed"
    assert c["employment_status"] == "unknown"
    assert c["corporate_matches"][0]["event_id"] == "e"


def evidence(**changes):
    row = dict(
        evidence_id="p",
        inventor_id="i",
        from_entity_id="A",
        to_entity_id="B",
        valid_from="2020-05-01",
        valid_to="2020-07-01",
        type="employment_move",
        claim_status="reported",
        source_ids=("job",),
    )
    row.update(changes)
    return row


def review(**changes):
    row = dict(
        review_id="v",
        inventor_id="i",
        claim="employment_move",
        status="accepted",
        reason="checked direct employment record",
        reviewed_date="2022-01-01",
        evidence_ids=("p",),
        event_ids=(),
        record_ids=("r1", "r2"),
        source_ids=("job",),
        supersedes_review_id=None,
    )
    row.update(changes)
    return row


def job_snapshot(evidences=None, reviews=None, **tables):
    return snapshot(
        personal_evidence=[evidence()] if evidences is None else evidences,
        reviews=[review()] if reviews is None else reviews,
        sources=[
            dict(source_id="job", kind="employment_record"),
            dict(source_id="s", kind="corporate_record"),
            dict(source_id="user", kind="user_review"),
        ],
        **tables,
    )


def change_rows():
    return (obs("r1", "2020-01-01"), obs("r2", "2020-12-31", ("B",)))


def test_direct_evidence_and_scoped_accepted_review_can_confirm_alongside_acquisition():
    c = build_mobility(change_rows(), job_snapshot(events=[event()]))["candidates"][0]
    assert c["employment_status"] == "confirmed"
    assert c["corporate_status"] == "confirmed"
    assert "organizational_transfer_candidate" in c["interpretations"]
    assert "confirmed_employment_move" in c["interpretations"]
    assert c["evidence"][0]["evidence_id"] == "p"
    assert c["reviews"][0]["review_id"] == "v"
    assert c["evidence"][0]["valid_from"]["raw"] == "2020-05-01"


def test_contradicting_direct_continuity_prevents_confirmation():
    s = job_snapshot(
        evidences=[
            evidence(),
            evidence(evidence_id="stay", type="employment_continuity", to_entity_id="A"),
        ]
    )
    c = build_mobility(change_rows(), s)["candidates"][0]
    assert c["employment_status"] == "conflicting"
    assert "stay" in c["conflicts"]
    assert len(c["evidence"]) == 2
    assert "confirmed_employment_move" not in c["interpretations"]


def test_user_assertion_without_review_stays_user_asserted():
    s = job_snapshot(
        evidences=[
            evidence(type="user_assertion", claim_status="user_asserted", source_ids=("user",))
        ],
        reviews=[],
    )
    c = build_mobility(change_rows(), s)["candidates"][0]
    assert c["employment_status"] == "user_asserted"


@pytest.mark.parametrize(
    "ev,rv,expected",
    [
        (evidence(source_ids=("user",)), review(), "user_asserted"),
        (evidence(type="patent_association"), review(), "user_asserted"),
        (evidence(), review(claim="corporate_event"), "unknown"),
        (evidence(from_entity_id="C"), review(), "conflicting"),
        (evidence(valid_from="2019-01-01", valid_to="2019-12-31"), review(), "user_asserted"),
        (evidence(inventor_id="other"), review(), "user_asserted"),
    ],
)
def test_accepted_review_does_not_bypass_claim_person_entity_date_and_source(ev, rv, expected):
    c = build_mobility(change_rows(), job_snapshot(evidences=[ev], reviews=[rv]))["candidates"][0]
    assert c["employment_status"] == expected


def test_candidate_specific_review_binding_does_not_confirm_every_same_person_transition():
    rows = (
        obs("r1", "2020"),
        obs("r2", "2021", ("B",)),
        obs("r3", "2022"),
        obs("r4", "2023", ("B",)),
    )
    s = job_snapshot(
        evidences=[evidence(valid_from="2020", valid_to="2023")], reviews=[review(record_ids=())]
    )
    before = build_mobility(rows, s)
    first, _, third = before["candidates"]
    assert first["employment_status"] == third["employment_status"] == "unknown"
    assert before["unbound_reviews"][0]["review_id"] == "v"
    result = build_mobility(rows, s, review_bindings={first["candidate_id"]: ("v",)})
    assert result["candidates"][0]["employment_status"] == "confirmed"
    assert result["candidates"][2]["employment_status"] == "unknown"
    assert [c["candidate_id"] for c in result["candidates"]] == [
        c["candidate_id"] for c in before["candidates"]
    ]


@pytest.mark.parametrize("binding", ["unknown_candidate", "unknown_review", "wrong_person"])
def test_review_bindings_reject_unknown_refs_and_wrong_person(binding):
    s = job_snapshot(reviews=[review(inventor_id="other" if binding == "wrong_person" else "i")])
    cid = build_mobility(change_rows(), s)["candidates"][0]["candidate_id"]
    bindings = {
        ("unknown" if binding == "unknown_candidate" else cid): (
            ("missing" if binding == "unknown_review" else "v"),
        )
    }
    with pytest.raises(DatasetInputError):
        build_mobility(change_rows(), s, review_bindings=bindings)


def test_superseded_review_is_history_not_a_live_rejection():
    s = job_snapshot(
        reviews=[review(review_id="old", status="rejected"), review(supersedes_review_id="old")]
    )
    c = build_mobility(change_rows(), s)["candidates"][0]
    assert c["employment_status"] == "confirmed"
    assert [(r["review_id"], r["status"], r["active"]) for r in c["reviews"]] == [
        ("old", "rejected", False),
        ("v", "accepted", True),
    ]


def test_live_rejected_and_accepted_reviews_conflict_without_latest_wins():
    s = job_snapshot(reviews=[review(review_id="z-reject", status="rejected"), review()])
    c = build_mobility(change_rows(), s)["candidates"][0]
    assert c["employment_status"] == "conflicting"
    assert set(c["conflicts"]) == {"v", "z-reject"}
    assert {r["status"] for r in c["reviews"]} == {"accepted", "rejected"}


def test_supersession_branches_conflict_even_with_two_accepted_leaves():
    s = job_snapshot(
        reviews=[
            review(review_id="old", status="pending"),
            review(review_id="a", supersedes_review_id="old"),
            review(review_id="b", supersedes_review_id="old"),
        ]
    )
    c = build_mobility(change_rows(), s)["candidates"][0]
    assert c["employment_status"] == "conflicting"
    assert {"a", "b"} <= set(c["conflicts"])


@pytest.mark.parametrize("status", ["pending", "rejected", "withdrawn"])
def test_unaccepted_review_history_is_retained(status):
    c = build_mobility(change_rows(), job_snapshot(reviews=[review(status=status)]))["candidates"][
        0
    ]
    assert c["employment_status"] == status
    assert c["reviews"][0]["status"] == status


def test_recurrent_changes_keep_cycles_unique_persons_and_event_counts_separate():
    rows = (
        obs("r1", "2020"),
        obs("r2", "2021", ("B",)),
        obs("r3", "2022"),
        obs("r4", "2023", ("B",)),
    )
    result = build_mobility_flow(rows)
    assert [
        (f["from_id"], f["to_id"], f["unique_inventors"], f["transition_events"])
        for f in result["flows"]
    ] == [("A", "B", 1, 2), ("B", "A", 1, 1)]
    assert result["unallocated"] == []
    assert result["provenance"]["network_kind"] == "directed_legal_network_cycles_permitted"
    assert {i for f in result["flows"] for i in f["candidate_ids"]} == {
        c["candidate_id"] for c in build_mobility(rows)["candidates"]
    }


def test_selected_layer_filters_do_not_adopt_unknown_or_rejected_employment():
    result = build_mobility_flow(change_rows(), layer="confirmed_employment_move")
    assert result["flows"] == []
    assert result["unallocated"][0]["reason"] == "employment_not_confirmed"
    rejected = build_mobility_flow(
        change_rows(),
        job_snapshot(reviews=[review(status="rejected")]),
        layer="individual_move_candidate",
    )
    assert rejected["flows"] == []
    assert rejected["unallocated"][0]["reason"] == "rejected"
    confirmed = build_mobility_flow(
        change_rows(), job_snapshot(), layer="confirmed_employment_move"
    )
    assert confirmed["flows"][0]["transition_events"] == 1
    assert confirmed["flows"][0]["status"] == "confirmed"


def test_coapplication_and_multicompany_changes_are_unallocated_not_cartesian_expanded():
    rows = (obs("r1", "2020", ("A", "C")), obs("r2", "2021", ("B", "C")))
    result = build_mobility_flow(rows)
    assert result["flows"] == []
    assert len(result["unallocated"]) == 1
    c = result["candidates"][0]
    assert c["retained_ids"] == ["C"]
    assert c["from_ids"] == ["A", "C"] and c["to_ids"] == ["B", "C"]
    assert "parallel_association" in c["interpretations"]


def test_historical_group_axis_requires_definite_full_interval_mapping():
    ga = group("2010-01-01", "2030-12-31")
    gb = dict(ga, group_id="gb", child_id="B", parent_id="Q")
    result = build_mobility_flow(change_rows(), snapshot(groups=[ga, gb]), axis="historical_group")
    assert [(f["from_id"], f["to_id"]) for f in result["flows"]] == [("P", "Q")]
    uncertain = build_mobility_flow(
        change_rows(), snapshot(groups=[dict(ga, valid_from=None), gb]), axis="historical_group"
    )
    assert uncertain["flows"] == []
    assert uncertain["unallocated"][0]["reason"] == "uncertain_group_mapping"
    missing = build_mobility_flow(change_rows(), axis="historical_group")
    assert missing["flows"] == []
    assert missing["unallocated"][0]["reason"] == "missing_group_mapping"


def test_witnessed_technology_coinventor_and_simultaneous_changes_are_support_only():
    i = IdentityResolver().resolve(inventor_id="i")
    j = IdentityResolver().resolve(inventor_id="j")
    rows = tuple(
        PatentObservation(
            r,
            (i, j),
            parse_observation_date(d, kind="filing"),
            applicant_ids=(a,),
            classifications=(("IPC", "H01"),),
        )
        for r, d, a in [("r1", "2020-01-01", "A"), ("r2", "2021-01-01", "B")]
    )
    result = build_mobility(rows)
    assert len(result["candidates"]) == 2
    for c in result["candidates"]:
        assert c["supporting_signals"]["shared_technologies"] == [["IPC", "H01"]]
        assert len(c["supporting_signals"]["shared_coinventor_keys"]) == 1
        assert c["supporting_signals"]["simultaneous_canonical_persons"] == 2
        assert c["employment_status"] == "unknown"


def test_minimum_observations_counts_contiguous_known_same_set_on_each_side():
    rows = (
        obs("r1", "2018"),
        obs("r2", "2019"),
        obs("r3", "2020", ("B",)),
        obs("r4", "2021", ("B",)),
    )
    c = build_mobility(rows, minimum_observations=2)["candidates"][0]
    assert c["candidate_status"] == "candidate"
    assert c["preceding_observation_count"] == c["following_observation_count"] == 2
    assert c["period_start"] == "2019-12-31"
    assert c["period_end"] == "2020-01-01"


def test_evidence_comparison_budget_rejects_before_candidate_or_event_matching(monkeypatch):
    import patent_analysis.inventor_mobility as module

    rows = tuple(obs(f"r{i}", f"{1000 + i}", ("A" if i % 2 == 0 else "B",)) for i in range(500))
    s = job_snapshot(evidences=[evidence(evidence_id=f"p{i}") for i in range(500)], reviews=[])
    monkeypatch.setattr(
        module,
        "match_corporate_events",
        lambda *args: pytest.fail("superlinear comparison started"),
    )
    with pytest.raises(DatasetInputError, match="limits"):
        build_mobility(rows, s)


def test_m10_is_same_candidate_audit_set_with_explicit_default_flow_adoption():
    s = job_snapshot(reviews=[review(status="rejected")])
    m08 = build_mobility(change_rows(), s)
    m10 = build_mobility_evidence(change_rows(), s)
    assert m10 == m08
    c = m10["candidates"][0]
    assert c["default_flow_adoption"]["observed_association_change"] is True
    assert c["default_flow_adoption"]["confirmed_employment_move"] is False
    assert c["default_flow_adoption"]["individual_move_candidate"] is False
    assert c["reviews"][0]["status"] == "rejected"


def test_output_budget_rejects_during_rows_before_event_comparison(monkeypatch):
    import patent_analysis.inventor_mobility as module

    applicants = tuple(str(i) + "x" * 512 for i in range(64))
    rows = tuple(obs(f"r{i}", f"{2000 + i}", applicants) for i in range(10))
    monkeypatch.setattr(
        module,
        "match_corporate_events",
        lambda *args: pytest.fail("comparison after excessive output allocation"),
    )
    with pytest.raises(DatasetInputError, match="limits"):
        build_mobility(rows)


def test_exact_unambiguous_evidence_scope_can_attach_without_record_scope():
    c = build_mobility(change_rows(), job_snapshot(reviews=[review(record_ids=())]))["candidates"][
        0
    ]
    assert c["employment_status"] == "confirmed"
    assert c["reviews"][0]["review_id"] == "v"


def test_corporate_rejection_blocks_only_corporate_layer_not_personal_confirmation():
    s = job_snapshot(
        reviews=[
            review(),
            review(
                review_id="corp",
                claim="corporate_event",
                status="rejected",
                evidence_ids=(),
                event_ids=("e",),
            ),
        ],
        events=[event()],
    )
    c = build_mobility(change_rows(), s)["candidates"][0]
    assert c["employment_status"] == "confirmed"
    assert c["corporate_status"] == "rejected"
    flow = build_mobility_flow(change_rows(), s, layer="organizational_transfer_candidate")
    assert flow["flows"] == []
    assert flow["unallocated"][0]["reason"] == "rejected"


def test_concordant_accepted_reviews_do_not_arbitrarily_replace_direct_confirmation():
    s = job_snapshot(
        reviews=[review(), review(review_id="z", evidence_ids=(), source_ids=("user",))]
    )
    c = build_mobility(change_rows(), s)["candidates"][0]
    assert c["employment_status"] == "confirmed"
    assert len(c["reviews"]) == 2


def test_snapshot_entity_references_are_validated_without_fuzzy_name_mapping():
    s = snapshot(entities=[dict(entity_id="A", display_name="Company A", source_ids=("s",))])
    with pytest.raises(DatasetInputError):
        build_mobility(change_rows(), s)


def test_associations_preserve_temporal_alias_hints_without_backfilling_current_name():
    alias = dict(
        alias_id="a",
        raw_alias="Old Name",
        entity_id="A",
        valid_from="2010-01-01",
        valid_to="2020-12-31",
        source_ids=("s",),
    )
    result = build_mobility(
        (obs("r1", "2020"), obs("r2", "2021")), snapshot(entity_aliases=[alias])
    )
    assert result["associations"][0]["entity_aliases"][0]["raw_alias"] == "Old Name"
    assert result["associations"][1]["entity_aliases"] == []
    assert result["candidates"] == []


def test_review_bindings_are_finite_mapping_even_without_snapshot():
    with pytest.raises(DatasetInputError):
        build_mobility(change_rows(), review_bindings=[])


def test_conflicting_identity_metadata_on_duplicate_record_is_rejected():
    curated = IdentityResolver((Alias("id", "raw", "i", "I", ("s",)),)).resolve(inventor_id="raw")
    duplicate = PatentObservation(
        "r1", (curated,), parse_observation_date("2020", kind="filing"), applicant_ids=("A",)
    )
    with pytest.raises(DatasetInputError):
        build_mobility((obs("r1", "2020"), duplicate))


def test_maximum_gap_threshold_is_calendar_boundary_year_distance_not_missing_years():
    result = build_mobility(
        (obs("r1", "2020-12-31"), obs("r2", "2022-01-01", ("B",))), maximum_gap_years=1
    )
    c = result["candidates"][0]
    assert c["candidate_status"] == "unknown"
    assert c["missing_calendar_years"] == 1
    assert c["gap_year_distance"] == 2
    assert result["provenance"]["gap_threshold_basis"] == "calendar_boundary_year_distance"


def test_single_observed_episode_still_retains_applicable_corporate_name_event():
    result = build_mobility(
        (obs("r1", "2020"),),
        snapshot(
            events=[event(type="name_change", entity_ids=("A",), effective_date="2020-06-01")]
        ),
    )
    assert result["candidates"] == []
    assert len(result["corporate_changes"]) == 1
    assert result["corporate_changes"][0]["type"] == "name_change"


def test_coarse_boundary_uncertainty_is_used_for_possible_event_and_evidence_matches():
    c = build_mobility(
        (obs("r1", "2020"), obs("r2", "2021", ("B",))), job_snapshot(events=[event()])
    )["candidates"][0]
    assert c["possible_period_start"] == "2020-01-01"
    assert c["possible_period_end"] == "2021-12-31"
    assert c["corporate_matches"][0]["strength"] == "possible"
    assert c["employment_status"] == "confirmed"
    assert "organizational_transfer_candidate" in c["interpretations"]


def test_permutation_and_raw_row_positions_do_not_change_meaning_or_candidate_ids():
    i = IdentityResolver().resolve(inventor_id="i")
    j = IdentityResolver().resolve(inventor_id="j")
    rows = tuple(
        PatentObservation(
            r,
            (i, j),
            parse_observation_date(d, kind="filing"),
            applicant_ids=(a,),
            source_ids=("s", "job"),
            classifications=(("IPC", "H01"), ("IPC", "G01")),
            source_ordinal=n,
        )
        for n, (r, d, a) in enumerate([("r1", "2020", "A"), ("r2", "2021", "B")], 1)
    )
    s = job_snapshot(events=[event()])
    reversed_snapshot = SidecarSnapshot(
        s.version,
        MappingProxyType(
            {
                k: tuple(
                    MappingProxyType(
                        {f: tuple(reversed(v)) if isinstance(v, tuple) else v for f, v in r.items()}
                    )
                    for r in reversed(values)
                )
                for k, values in s.tables.items()
            }
        ),
        (),
        (),
    )
    shuffled = tuple(
        replace(
            o,
            inventors=tuple(reversed(o.inventors)),
            source_ordinal=10 + n,
            source_fields=("raw order changed",),
        )
        for n, o in enumerate(reversed(rows))
    )
    assert build_mobility(rows, s) == build_mobility(shuffled, reversed_snapshot)
    assert build_mobility_flow(rows, s) == build_mobility_flow(shuffled, reversed_snapshot)


def test_identical_records_dedup_but_different_applicants_reject():
    rows = change_rows()
    assert build_mobility(rows) == build_mobility(rows + (replace(rows[0], source_ordinal=99),))
    with pytest.raises(DatasetInputError):
        build_mobility(rows + (replace(rows[0], applicant_ids=("C",)),))


@pytest.mark.parametrize("which", ["persons", "observations", "associations"])
def test_hard_row_and_person_limits_are_not_top_pruned(which):
    if which == "persons":
        rows = tuple(obs(f"r{i}", None, person=f"i{i}") for i in range(201))
    elif which == "observations":
        rows = (obs("r", None),) * 5001
    else:
        people = tuple(IdentityResolver().resolve(inventor_id=f"i{i}") for i in range(64))
        rows = tuple(
            PatentObservation(f"r{i}", people, parse_observation_date(None, kind="filing"))
            for i in range(79)
        )
    with pytest.raises(DatasetInputError, match="limits"):
        build_mobility(rows)


def test_preflight_observation_limit_accepts_5000_identical_duplicates():
    assert build_mobility((obs("r", None),) * 5000)["coverage"]["observations"] == 1


def test_parsed_p1_snapshot_contract_and_no_input_mutation(tmp_path):
    tables = {k: [] for k in TABLE_IDS}
    tables.update(
        sources=[
            dict(
                source_id="job",
                kind="employment_record",
                citation="local",
                checked_date="2022-01-01",
                url=None,
            )
        ],
        entities=[dict(entity_id=i, display_name=i, source_ids=["job"]) for i in ("A", "B")],
        personal_evidence=[evidence()],
        reviews=[review()],
    )
    raw = json.dumps(dict(version="1.0.0", tables=tables)).encode("utf-8")
    path = tmp_path / "synthetic.json"
    path.write_bytes(raw)
    s = read_inventor_sidecar(
        "synthetic.json", allowed_root=tmp_path, inventor_ids=("i",), record_ids=("r1", "r2")
    )
    result = build_mobility_evidence(change_rows(), s)
    assert result["candidates"][0]["employment_status"] == "confirmed"
    text = json.dumps(result)
    assert "raw_snapshots" not in text and str(tmp_path) not in text
    assert path.read_bytes() == raw
    assert isinstance(s.tables["reviews"][0], MappingProxyType)


@pytest.mark.parametrize(
    "kind,scope,status",
    [
        ("patent_rights_transfer", "patents_only", "completed"),
        ("acquisition", "whole_entity", "announced"),
        ("business_transfer", "partial_business", "completed"),
    ],
)
def test_rights_announced_and_unscoped_partial_are_not_organizational_flows(kind, scope, status):
    s = job_snapshot(
        evidences=[], reviews=[], events=[event(type=kind, scope=scope, status=status)]
    )
    flow = build_mobility_flow(change_rows(), s, layer="organizational_transfer_candidate")
    assert flow["flows"] == []
    assert flow["candidates"][0]["employment_status"] == "unknown"
    assert flow["unallocated"][0]["reason"] == "no_organizational_transfer_support"


def test_scoped_business_transfer_can_flow_in_corporate_layer_only():
    s = job_snapshot(
        evidences=[],
        reviews=[],
        events=[event(type="business_transfer", scope="partial_business", record_ids=("r2",))],
    )
    result = build_mobility_flow(change_rows(), s, layer="organizational_transfer_candidate")
    assert result["flows"][0]["transition_events"] == 1
    assert build_mobility_flow(change_rows(), s, layer="confirmed_employment_move")["flows"] == []


def test_user_asserted_review_is_not_unknown_or_confirmed():
    c = build_mobility(change_rows(), job_snapshot(reviews=[review(status="user_asserted")]))[
        "candidates"
    ][0]
    assert c["employment_status"] == "user_asserted"


def test_unbound_review_supersession_still_preserves_active_history():
    s = job_snapshot(
        reviews=[
            review(review_id="old", record_ids=(), evidence_ids=(), status="pending"),
            review(record_ids=(), evidence_ids=(), status="withdrawn", supersedes_review_id="old"),
        ]
    )
    result = build_mobility(change_rows(), s)
    assert [(r["review_id"], r["active"]) for r in result["unbound_reviews"]] == [
        ("old", False),
        ("v", True),
    ]


def test_corporate_review_branches_conflict_independently_of_employment():
    reviews = [
        review(
            review_id="old",
            claim="corporate_event",
            status="pending",
            evidence_ids=(),
            event_ids=("e",),
        ),
        review(
            review_id="a",
            claim="corporate_event",
            evidence_ids=(),
            event_ids=("e",),
            supersedes_review_id="old",
        ),
        review(
            review_id="b",
            claim="corporate_event",
            evidence_ids=(),
            event_ids=("e",),
            supersedes_review_id="old",
        ),
    ]
    c = build_mobility(change_rows(), job_snapshot(reviews=reviews, events=[event()]))[
        "candidates"
    ][0]
    assert c["corporate_status"] == "conflicting"
    assert c["corporate_conflicts"] == ["a", "b"]
    assert c["employment_status"] == "unknown"


def test_mixed_date_kinds_do_not_create_a_false_chronology():
    rows = change_rows()
    mixed = replace(rows[1], observed_date=parse_observation_date("2020-12-31", kind="publication"))
    with pytest.raises(DatasetInputError):
        build_mobility((rows[0], mixed))


def test_missing_identity_rows_stay_coverage_not_person_cessation():
    no_person = PatentObservation(
        "empty", (), parse_observation_date("2022", kind="filing"), applicant_ids=("B",)
    )
    result = build_mobility((obs("r1", "2020"), no_person))
    assert result["coverage"]["missing_inventors"] == 1
    assert result["coverage"]["name_only_associations"] == 0
    assert result["candidates"] == []
    assert result["coverage"]["persons"] == 1


def test_rights_only_context_never_allocates_a_personal_move_without_direct_evidence():
    s = job_snapshot(
        evidences=[],
        reviews=[],
        events=[event(type="patent_rights_transfer", scope="patents_only")],
    )
    result = build_mobility_flow(change_rows(), s, layer="individual_move_candidate")
    assert result["flows"] == []
    assert result["unallocated"][0]["reason"] == "rights_only_without_personal_evidence"
    assert not result["candidates"][0]["default_flow_adoption"]["individual_move_candidate"]
    both = build_mobility_flow(
        change_rows(),
        job_snapshot(events=[event(type="patent_rights_transfer", scope="patents_only")]),
        layer="confirmed_employment_move",
    )
    assert both["flows"][0]["transition_events"] == 1
