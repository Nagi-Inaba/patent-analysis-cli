import json
from copy import deepcopy

import pytest
from test_inventor_public import spec, write_patents

from patent_analysis._render_canonical import canonical_json_bytes, sha256_bytes
from patent_analysis.analysis_runner import run_analysis
from patent_analysis.chart_models.advanced import build_advanced_chart_model


def test_network_public_result_builds_model_without_legacy_inner_population(tmp_path):
    write_patents(tmp_path)
    result = run_analysis("patents.json", json.dumps(spec()).encode(), allowed_root=tmp_path)
    before = deepcopy(result)
    model, receipt = build_advanced_chart_model(result, analysis_id=result["analysis_id"])
    assert model["projection"]["kind"] == "inventor-network"
    assert model["analysis_result_sha256"] == sha256_bytes(canonical_json_bytes(result))
    assert receipt["result_data_sha256"] == sha256_bytes(canonical_json_bytes(result["data"]))
    assert model["population"] == result["population"]
    assert result == before
    assert build_advanced_chart_model(result, analysis_id=result["analysis_id"]) == (model, receipt)


def test_persisted_model_rejects_duplicate_network_ids(tmp_path):
    import pytest

    from patent_analysis.chart_models.advanced import validate_advanced_chart_model

    write_patents(tmp_path)
    result = run_analysis("patents.json", json.dumps(spec()).encode(), allowed_root=tmp_path)
    model, _ = build_advanced_chart_model(result, analysis_id=result["analysis_id"])
    validate_advanced_chart_model(model)
    model["projection"]["nodes"][1]["id"] = model["projection"]["nodes"][0]["id"]
    with pytest.raises(ValueError, match="inconsistent"):
        validate_advanced_chart_model(model)


def test_persisted_timeline_rejects_lane_references_outside_display(tmp_path):
    import pytest

    from patent_analysis.chart_models.advanced import validate_advanced_chart_model

    model = public_model(tmp_path, "inventor-activity.v1")
    validate_advanced_chart_model(model)
    model["projection"]["nodes"][0]["y"] = len(model["projection"]["lanes"])
    with pytest.raises(ValueError, match="inconsistent"):
        validate_advanced_chart_model(model)


def test_persisted_activity_rejects_corporate_event_bands(tmp_path):
    from patent_analysis.chart_models.advanced import validate_advanced_chart_model

    model = public_model(tmp_path, "inventor-activity.v1")
    year = model["projection"]["years"][0]
    model["projection"]["bands"] = [
        {
            "id": "event",
            "start": year,
            "end": year,
            "label": "event",
            "kind": "acquisition",
            "status": "announced",
        }
    ]
    with pytest.raises(ValueError, match="invalid"):
        validate_advanced_chart_model(model)


def test_persisted_timeline_rejects_nonconsecutive_calendar(tmp_path):
    import pytest

    from patent_analysis.chart_models.advanced import validate_advanced_chart_model

    model = public_model(tmp_path, "inventor-activity.v1")
    model["projection"]["years"][1] += 1
    with pytest.raises(ValueError, match="inconsistent"):
        validate_advanced_chart_model(model)


@pytest.mark.parametrize(
    "tamper", ["duplicate_id", "outside_year", "edge_reference", "band_interval"]
)
def test_persisted_timeline_geometry_and_relations_are_consistent(tmp_path, tamper):
    from patent_analysis.chart_models.advanced import validate_advanced_chart_model

    model = public_model(tmp_path, "inventor-mobility.v1")
    p = model["projection"]
    validate_advanced_chart_model(model)
    if tamper == "duplicate_id":
        p["nodes"][1]["id"] = p["nodes"][0]["id"]
    elif tamper == "outside_year":
        p["nodes"][0]["x"] = p["years"][0] - 1
    elif tamper == "edge_reference":
        p["links"] = [{"source": 0, "target": len(p["nodes"]), "gap": False, "state": "observed"}]
    else:
        p["bands"] = [
            {
                "id": "band",
                "start": p["years"][1],
                "end": p["years"][0],
                "label": "event",
                "kind": "acquisition",
                "status": "announced",
            }
        ]
    with pytest.raises(ValueError, match="inconsistent"):
        validate_advanced_chart_model(model)


@pytest.mark.parametrize("tamper", ["mass", "backward", "kind", "duplicate"])
def test_persisted_alluvial_rejects_invalid_membership_flow(tmp_path, tamper):
    from patent_analysis.chart_models.advanced import validate_advanced_chart_model

    model = public_model(tmp_path, "inventor-cluster-flow.v1")
    p = model["projection"]
    validate_advanced_chart_model(model)
    if tamper == "mass":
        p["links"][0]["value"] = 100
    elif tamper == "backward":
        p["links"][0]["source"], p["links"][0]["target"] = (
            p["links"][0]["target"],
            p["links"][0]["source"],
        )
    elif tamper == "kind":
        p["links"][0]["kind"] = "gap"
    else:
        p["nodes"][1]["id"] = p["nodes"][0]["id"]
    with pytest.raises(ValueError, match="inconsistent"):
        validate_advanced_chart_model(model)


@pytest.mark.parametrize("tamper", ["mixed_id", "self_loop", "edge_reference"])
def test_persisted_scatter_preserves_defined_vs_unplottable_identity(tmp_path, tamper):
    from patent_analysis.chart_models.advanced import validate_advanced_chart_model

    model = public_model(tmp_path, "inventor-similarity.v1")
    p = model["projection"]
    validate_advanced_chart_model(model)
    if tamper == "mixed_id":
        p["unplottable"][0]["id"] = p["points"][0]["id"]
    else:
        p["edges"] = [
            {"source": 0, "target": 0 if tamper == "self_loop" else len(p["points"]), "value": 1}
        ]
    with pytest.raises(ValueError, match="inconsistent"):
        validate_advanced_chart_model(model)


@pytest.mark.parametrize(
    "analysis_id,parameters",
    [
        ("inventor-network.v1", {}),
        ("inventor-ego-network.v1", {"focus": ["id", "A"], "hops": 1}),
        ("inventor-technology.v1", {}),
        ("inventor-activity.v1", {}),
        ("inventor-cluster-flow.v1", {}),
        ("inventor-similarity.v1", {"co_inventor_overlay": True}),
        ("inventor-impact.v1", {"snapshot_date": "2025-01-01"}),
        ("inventor-mobility.v1", {}),
        ("inventor-mobility-flow.v1", {}),
        ("inventor-mobility-flow.v1", {"allocation": "fractional_flows"}),
    ],
)
def test_all_nine_public_results_build_closed_models_without_source_mutation(
    tmp_path, analysis_id, parameters, monkeypatch
):
    from patent_analysis import advanced_presentation
    from patent_analysis.advanced_presentation import advanced_marks_for
    from patent_analysis.chart_models.advanced import validate_advanced_chart_model

    # Model creation must not activate an unbuilt mark, regardless of checkout assets.
    monkeypatch.setattr(advanced_presentation, "ADVANCED_BUILD", None)
    write_patents(tmp_path)
    result = run_analysis(
        "patents.json", json.dumps(spec(analysis_id, parameters)).encode(), allowed_root=tmp_path
    )
    before = deepcopy(result)
    model, receipt = build_advanced_chart_model(result, analysis_id=analysis_id)
    validate_advanced_chart_model(model)
    assert model["mark"] == analysis_id.removesuffix(".v1") + "-svg.v1"
    assert model["population"] == result["population"]
    assert receipt["chart_model_sha256"] == sha256_bytes(canonical_json_bytes(model))
    assert result == before
    assert advanced_marks_for(analysis_id) == ()


def public_model(tmp_path, analysis_id, parameters=None):
    write_patents(tmp_path)
    result = run_analysis(
        "patents.json", json.dumps(spec(analysis_id, parameters)).encode(), allowed_root=tmp_path
    )
    return build_advanced_chart_model(result, analysis_id=analysis_id)[0]


def test_persisted_heatmap_requires_every_axis_pair_exactly_once(tmp_path):
    import pytest

    from patent_analysis.chart_models.advanced import validate_advanced_chart_model

    model = public_model(tmp_path, "inventor-technology.v1")
    validate_advanced_chart_model(model)
    model["projection"]["cells"][1] = deepcopy(model["projection"]["cells"][0])
    with pytest.raises(ValueError, match="inconsistent"):
        validate_advanced_chart_model(model)
