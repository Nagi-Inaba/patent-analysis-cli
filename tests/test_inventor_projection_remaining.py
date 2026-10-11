from copy import deepcopy

import pytest
from test_inventor_graph import obs

from patent_analysis.advanced_projection import project_advanced_data
from patent_analysis.inventor_activity import cluster_flow
from patent_analysis.inventor_units import form_units


def test_cluster_flow_preserves_membership_widths_and_boundary_buckets():
    rows = (
        obs("1", ("A", "B", "C"), "2020"),
        obs("2", ("A", "B"), "2021"),
        obs("3", ("C",), "2021"),
        obs("4", ("A", "B", "C"), "2022"),
        obs("5", ("A", "B"), "2024"),
    )
    stats = cluster_flow(form_units(rows, unit="records"), rows)
    data = {"analysis_id": "inventor-cluster-flow.v1", "statistics": stats}
    before = deepcopy(data)
    projection = project_advanced_data(data["analysis_id"], data)
    assert projection["kind"] == "inventor-alluvial"
    assert projection["years"] == [2020, 2021, 2022, 2023, 2024]
    assert {"split", "merge", "newly_observed", "not_observed"} <= {
        e["kind"] for e in projection["links"]
    }
    for i, n in enumerate(projection["nodes"]):
        if n["kind"] == "cluster":
            if n["year"] != projection["years"][-1]:
                assert (
                    sum(e["value"] for e in projection["links"] if e["source"] == i) == n["members"]
                )
            if n["year"] != projection["years"][0]:
                assert (
                    sum(e["value"] for e in projection["links"] if e["target"] == i) == n["members"]
                )
    assert not any(e["kind"] == "gap" for e in projection["links"])
    assert data == before
    assert all(
        projection["nodes"][e["source"]]["year"] < projection["nodes"][e["target"]]["year"]
        for e in projection["links"]
    )
    assert "範囲境界" in projection["context"]


def test_similarity_uses_full_feature_ordination_and_real_coinvention_overlay():
    from patent_analysis.inventor_numeric import project_features
    from patent_analysis.inventor_profiles import technology_similarity

    rows = (
        obs("1", ("A", "B"), "2020", ("X",)),
        obs("2", ("C",), "2020", ("Y",)),
        obs("3", ("D",), "2020"),
    )
    stats = technology_similarity(form_units(rows, unit="records"), rows, co_inventor_overlay=True)
    data = {"analysis_id": "inventor-similarity.v1", "statistics": stats}
    before = deepcopy(data)
    projection = project_advanced_data(data["analysis_id"], data)
    assert projection["kind"] == "inventor-scatter"
    assert [p["label"] for p in projection["unplottable"]] == ["D"]
    assert projection["unplottable"][0]["reason"] == "zero_vector"
    layout = project_features(stats["features"])
    assert [(p["x"], p["y"]) for p in projection["points"]] == [
        tuple(a + b for a, b in zip(p["raw_coordinates"], p["display_offset"], strict=True))
        for p in layout["points"]
        if p["raw_coordinates"] is not None
    ]
    assert len(projection["edges"]) == 1
    assert "stress" in projection["context"] and "MDS" in projection["context"]
    assert "ずれ" in projection["context"]
    assert data == before
    assert project_advanced_data(data["analysis_id"], data) == projection


def test_impact_keeps_defined_zero_and_excludes_unknown_adjusted_citations():
    from test_inventor_citations import citation

    from patent_analysis.inventor_citations import citation_metrics

    rows = tuple(obs(str(i), (chr(65 + i),), "2022", ("X",)) for i in range(5)) + (
        obs("missing", ("Z",), "2022", ("X",)),
    )
    stats = citation_metrics(
        form_units(rows, unit="records"),
        rows,
        tuple(citation(str(i), i) for i in range(5)),
        snapshot_date="2025-01-01",
    )
    data = {"analysis_id": "inventor-impact.v1", "statistics": stats}
    before = deepcopy(data)
    projection = project_advanced_data(data["analysis_id"], data)
    a = next(p for p in projection["points"] if p["label"] == "A")
    assert a["x"] == 1 and a["y"] == 0 and a["size"] == 0
    assert [p["label"] for p in projection["unplottable"]] == ["Z"]
    assert "missing_citations" in projection["unplottable"][0]["reason"]
    assert projection["edges"] == []
    assert "同一出願年" in projection["context"] and "2025-01-01" in projection["context"]
    assert "既知 5/6" in projection["context"] and "能力" in projection["context"]
    assert data == before


def test_impact_recent_unknown_keeps_citations_but_not_missing_adjustment():
    from test_inventor_citations import citation

    from patent_analysis.inventor_citations import citation_metrics

    rows = (
        obs("r1", ("A",), None, ("X",), family_id="f"),
        obs("r2", ("B",), "2024", ("X",), family_id="f"),
    )
    stats = citation_metrics(
        form_units(rows, unit="family"),
        rows,
        tuple(citation(row.record_id, 1, citing_ids=("c",)) for row in rows),
        snapshot_date="2025-01-01",
        citation_basis="unique_citing_ids",
        min_cohort_units=1,
        recent_start_year=2023,
    )
    people = {row["inventor_id"]: row for row in stats["people"]}
    assert people["A"]["recent_activity"] is None
    assert people["A"]["raw_sum"]["value"] == 1
    assert people["A"]["adjusted_mean"] is None
    assert "missing_activity_date" in people["A"]["unplottable_reasons"]
    before = deepcopy(stats)
    p = project_advanced_data(
        "inventor-impact.v1", {"analysis_id": "inventor-impact.v1", "statistics": stats}
    )
    assert not p["points"]  # Missing unit filing-year adjustment is not drawn as analytical zero.
    assert {point["label"] for point in p["unplottable"]} == {"A", "B"}
    assert stats == before and people["A"]["recent_activity"] is None


def test_mobility_observation_intervals_separate_candidate_and_corporate_facts():
    from test_corporate_history import event, snapshot
    from test_inventor_mobility import obs as mobility_obs

    from patent_analysis.inventor_mobility import build_mobility

    rows = (
        mobility_obs("r1", "2020-01"),
        mobility_obs("r2", "2022", ("B",)),
        mobility_obs("r3", None, ("C",)),
    )
    sidecar = snapshot(
        events=[event(effective_date="2021-06")],
        sources=[dict(source_id="s", kind="corporate_record")],
    )
    stats = build_mobility(rows, sidecar)
    data = {"analysis_id": "inventor-mobility.v1", "statistics": stats}
    before = deepcopy(data)
    p = project_advanced_data(data["analysis_id"], data)
    assert p["kind"] == "inventor-timeline"
    assert p["years"] == [2020, 2021, 2022]
    assert any("2020-01" in n["label"] for n in p["nodes"])
    assert not any("C" in n["label"] for n in p["nodes"])
    assert any(e["state"] == "inferred" and e["gap"] for e in p["links"])
    assert not any(e["state"] == "confirmed" for e in p["links"])
    assert p["bands"][0]["kind"] == "acquisition" and p["bands"][0]["status"] == "completed"
    assert "雇用" in p["context"] and "欠損 1" in p["context"]
    assert data == before


def test_corporate_flow_is_directed_observed_association_not_confirmed_jobs():
    from test_inventor_mobility import obs as mobility_obs

    from patent_analysis.inventor_mobility import build_mobility_flow

    rows = (
        mobility_obs("r1", "2020"),
        mobility_obs("r2", "2021", ("B",)),
        mobility_obs("r3", "2022"),
        mobility_obs("r4", "2023", ("B",)),
        mobility_obs("missing", "2023", (), person="j"),
    )
    stats = build_mobility_flow(rows)
    data = {"analysis_id": "inventor-mobility-flow.v1", "statistics": stats}
    before = deepcopy(data)
    p = project_advanced_data(data["analysis_id"], data)
    assert p["kind"] == "inventor-network" and p["focus"] is None
    assert {n["label"] for n in p["nodes"]} == {"A", "B"}
    assert len(p["edges"]) == 2
    assert all(e["directed"] and e["state"] == "observed" and e["value"] == 1 for e in p["edges"])
    assert "雇用" in p["context"] and "観測出願人" in p["context"]
    assert data == before


def test_mobility_deduplicates_shared_event_facts_not_candidate_specific_matches():
    from test_corporate_history import event, snapshot
    from test_inventor_mobility import obs as mobility_obs

    from patent_analysis.inventor_mobility import build_mobility

    rows = (
        mobility_obs("r1", "2020"),
        mobility_obs("r2", "2022", ("B",)),
        mobility_obs("r3", "2020", person="j"),
        mobility_obs("r4", "2022", ("B",), person="j"),
    )
    sidecar = snapshot(
        events=[event(effective_date="2021", record_ids=("r1", "r2"))],
        sources=[dict(source_id="s", kind="corporate_record")],
    )
    stats = build_mobility(rows, sidecar)
    assert len(stats["candidates"]) == 2
    assert (
        stats["candidates"][0]["corporate_matches"] != stats["candidates"][1]["corporate_matches"]
    )
    p = project_advanced_data(
        "inventor-mobility.v1", {"analysis_id": "inventor-mobility.v1", "statistics": stats}
    )
    assert len(p["bands"]) == 1


def test_mobility_name_only_identity_does_not_become_movement_evidence():
    from dataclasses import replace

    from test_inventor_mobility import obs as mobility_obs

    from patent_analysis.inventor_identity import IdentityResolver
    from patent_analysis.inventor_mobility import build_mobility

    identity = IdentityResolver().resolve(name="Same Name")
    rows = tuple(
        replace(row, inventors=(identity,))
        for row in (mobility_obs("r1", "2020"), mobility_obs("r2", "2021", ("B",)))
    )
    stats = build_mobility(rows)
    assert stats["candidates"][0]["canonical_inventor_id"] is None
    p = project_advanced_data(
        "inventor-mobility.v1", {"analysis_id": "inventor-mobility.v1", "statistics": stats}
    )
    assert p["nodes"]
    assert not any(e["state"] in {"inferred", "confirmed"} for e in p["links"])
    assert "氏名一致" in p["context"]


def test_corporate_flow_cannot_promote_observation_layer_to_confirmed_jobs():
    from test_inventor_mobility import obs as mobility_obs

    from patent_analysis.inventor_mobility import build_mobility_flow

    rows = (mobility_obs("r1", "2020"), mobility_obs("r2", "2021", ("B",)))
    stats = build_mobility_flow(rows)
    stats["provenance"]["layer"] = "confirmed_employment_move"
    for flow in stats["flows"]:
        flow["layer"] = "confirmed_employment_move"
    with pytest.raises(ValueError, match="inconsistent"):
        project_advanced_data(
            "inventor-mobility-flow.v1",
            {"analysis_id": "inventor-mobility-flow.v1", "statistics": stats},
        )


def test_mobility_cannot_promote_unreviewed_candidate_to_confirmed_employment():
    from test_inventor_mobility import change_rows

    from patent_analysis.inventor_mobility import build_mobility

    stats = build_mobility(change_rows())
    stats["candidates"][0]["employment_status"] = "confirmed"
    with pytest.raises(ValueError, match="inconsistent"):
        project_advanced_data(
            "inventor-mobility.v1", {"analysis_id": "inventor-mobility.v1", "statistics": stats}
        )


def test_mobility_rejected_claim_keeps_observation_not_inferred_job_link():
    from test_inventor_mobility import change_rows, job_snapshot, review

    from patent_analysis.inventor_mobility import build_mobility

    stats = build_mobility(change_rows(), job_snapshot(reviews=[review(status="rejected")]))
    p = project_advanced_data(
        "inventor-mobility.v1", {"analysis_id": "inventor-mobility.v1", "statistics": stats}
    )
    assert not any(e["state"] in {"inferred", "confirmed"} for e in p["links"])
    assert any("rejected" in n["label"] for n in p["nodes"])


def test_fractional_corporate_flow_rejects_tampered_mass_conservation():
    from test_inventor_mobility import obs as mobility_obs

    from patent_analysis.inventor_mobility import build_mobility, organization_flows

    rows = (mobility_obs("r1", "2020", ("A", "B")), mobility_obs("r2", "2021", ("C", "D")))
    stats = organization_flows(build_mobility(rows), rows, None, allocation="fractional_flows")
    stats["allocation_summary"]["allocated_event_mass"] = {
        "value": 2.0,
        "numerator": "2",
        "denominator": "1",
    }
    with pytest.raises(ValueError, match="inconsistent"):
        project_advanced_data(
            "inventor-mobility-flow.v1",
            {"analysis_id": "inventor-mobility-flow.v1", "statistics": stats},
        )


def test_fractional_corporate_flow_rejects_wrong_pair_weights_with_same_total():
    from test_inventor_mobility import obs as mobility_obs

    from patent_analysis.inventor_mobility import build_mobility, organization_flows

    rows = (mobility_obs("r1", "2020", ("A", "B")), mobility_obs("r2", "2021", ("C", "D")))
    stats = organization_flows(build_mobility(rows), rows, None, allocation="fractional_flows")
    for flow, n in zip(stats["flows"][:2], [3, 1], strict=True):
        flow["flow_weight"] = flow["event_mass"] = {
            "value": n / 8,
            "numerator": str(n),
            "denominator": "8",
        }
    with pytest.raises(ValueError, match="inconsistent"):
        project_advanced_data(
            "inventor-mobility-flow.v1",
            {"analysis_id": "inventor-mobility-flow.v1", "statistics": stats},
        )


def test_fractional_historical_group_flow_discloses_excluded_mass_and_axis():
    from test_corporate_history import group, snapshot
    from test_inventor_mobility import obs as mobility_obs

    from patent_analysis.inventor_mobility import build_mobility, organization_flows

    rows = (mobility_obs("r1", "2020", ("A", "B")), mobility_obs("r2", "2021", ("C", "D")))
    sidecar = snapshot(
        entities=[
            dict(entity_id=i, display_name=i, source_ids=("s",))
            for i in ("A", "B", "C", "D", "P", "Q", "R")
        ],
        groups=[
            dict(group(), group_id=f"g{i}", child_id=i, parent_id=p)
            for i, p in [("A", "P"), ("B", "Q"), ("C", "P"), ("D", "R")]
        ],
    )
    stats = organization_flows(
        build_mobility(rows, sidecar), rows, sidecar, axis="group", allocation="fractional_flows"
    )
    before = deepcopy(stats)
    p = project_advanced_data(
        "inventor-mobility-flow.v1",
        {"analysis_id": "inventor-mobility-flow.v1", "statistics": stats},
    )
    assert len(p["edges"]) == 3 and all(e["value"] == 0.25 for e in p["edges"])
    assert "axis=group" in p["context"] and "allocation=fractional_flows" in p["context"]
    assert "未配分質量 1/4" in p["context"]
    assert "未配分 1 行" in p["context"]
    assert stats == before
    for flow, n in zip(stats["flows"][:2], [3, 1], strict=True):
        flow["flow_weight"] = flow["event_mass"] = {
            "value": n / 8,
            "numerator": str(n),
            "denominator": "8",
        }
    with pytest.raises(ValueError, match="inconsistent"):
        project_advanced_data(
            "inventor-mobility-flow.v1",
            {"analysis_id": "inventor-mobility-flow.v1", "statistics": stats},
        )


def test_scatter_display_budget_retains_large_unplottable_neutral_population():
    from patent_analysis.chart_models._common import validate_schema
    from patent_analysis.inventor_profiles import technology_similarity

    rows = tuple(obs(str(i), (f"person-{i}",), "2020") for i in range(40))
    stats = technology_similarity(form_units(rows, unit="records"), rows)
    data = {"analysis_id": "inventor-similarity.v1", "statistics": stats}
    before = deepcopy(data)
    p = project_advanced_data(data["analysis_id"], data)
    validate_schema(p, "advanced-projection-v1.schema.json")
    assert not p["points"] and len(p["unplottable"]) == 24
    assert "24/40" in p["context"] and "省略は表示のみ" in p["context"]
    assert len(stats["features"]) == 40 and data == before


def test_fractional_corporate_flow_displays_exact_event_mass_not_people():
    from test_inventor_mobility import obs as mobility_obs

    from patent_analysis.inventor_mobility import build_mobility, organization_flows

    rows = (mobility_obs("r1", "2020", ("A", "B")), mobility_obs("r2", "2021", ("C", "D")))
    stats = organization_flows(build_mobility(rows), rows, None, allocation="fractional_flows")
    data = {"analysis_id": "inventor-mobility-flow.v1", "statistics": stats}
    before = deepcopy(data)
    p = project_advanced_data(data["analysis_id"], data)
    assert len(p["edges"]) == 4 and all(e["value"] == 0.25 for e in p["edges"])
    assert "イベント質量" in p["context"] and "人数ではない" in p["context"]
    assert data == before
