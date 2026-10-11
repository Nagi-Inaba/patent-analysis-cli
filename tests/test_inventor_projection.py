from copy import deepcopy

import pytest
from test_inventor_public import write_patents

from patent_analysis.advanced_projection import project_advanced_data
from patent_analysis.inventor_graph import co_inventor_graph
from patent_analysis.inventor_inputs import prepare_inventor_inputs
from patent_analysis.inventor_units import form_units


def prepared_patents(tmp_path):
    write_patents(tmp_path)
    return prepare_inventor_inputs(
        "patents.json",
        allowed_root=tmp_path,
        bindings={
            "record_id": "record",
            "inventor_ids": "people",
            "date": "day",
            "classification": "ipc",
            "applicant_ids": "org",
        },
    )


def network_data(tmp_path):
    prepared = prepared_patents(tmp_path)
    graph = co_inventor_graph(
        form_units(prepared.observations, unit="records"), prepared.observations
    )
    return {
        "analysis_id": "inventor-network.v1",
        "statistics": graph,
        "family_basis": {"family_mode": "records", "unit": "records"},
        "input_coverage": dict(prepared.coverage),
    }


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf")])
def test_network_rejects_nonfinite_metrics_even_if_not_displayed(tmp_path, bad):
    data = network_data(tmp_path)
    data["statistics"]["nodes"][0]["pagerank"] = bad
    with pytest.raises(ValueError, match="inconsistent"):
        project_advanced_data(data["analysis_id"], data)


def test_network_rejects_forged_global_pagerank(tmp_path):
    data = network_data(tmp_path)
    data["statistics"]["nodes"][0]["pagerank"] += 0.1
    with pytest.raises(ValueError, match="inconsistent"):
        project_advanced_data(data["analysis_id"], data)


def test_network_projection_isolates_and_fixed_layout_do_not_change_metrics(tmp_path):
    data = network_data(tmp_path)
    before = deepcopy(data)
    projected = project_advanced_data("inventor-network.v1", data)
    assert projected["kind"] == "inventor-network"
    assert len(projected["nodes"]) == 4
    assert len(projected["edges"]) == 2
    assert projected["focus"] is None
    assert sorted(n["label"] for n in projected["nodes"]) == ["A", "B", "C", "D"]
    assert all(not e["directed"] and e["state"] == "observed" for e in projected["edges"])
    assert "距離" in projected["context"]
    assert data == before
    assert project_advanced_data("inventor-network.v1", data) == projected


def test_ego_focus_and_hops_preserve_the_full_graph_metrics(tmp_path):
    from patent_analysis.inventor_graph import ego_network

    data = network_data(tmp_path)
    data["analysis_id"] = "inventor-ego-network.v1"
    data["statistics"] = ego_network(data["statistics"], focus=("id", "A"), hops=1)
    before = deepcopy(data)
    projected = project_advanced_data("inventor-ego-network.v1", data)
    nodes = {node["label"]: node for node in projected["nodes"]}
    assert set(nodes) == {"A", "B"}
    assert projected["focus"] == nodes["A"]["id"]
    assert nodes["A"]["hop"] == 0 and nodes["B"]["hop"] == 1
    assert data["statistics"]["nodes"][1]["degree"] == 2
    assert data == before


def test_technology_heatmap_distinguishes_missing_profiles_from_zero_cells(tmp_path):
    from patent_analysis.inventor_profiles import technology_profiles

    prepared = prepared_patents(tmp_path)
    stats = technology_profiles(
        form_units(prepared.observations, unit="records"), prepared.observations
    )
    data = {"analysis_id": "inventor-technology.v1", "statistics": stats}
    before = deepcopy(data)
    projected = project_advanced_data("inventor-technology.v1", data)
    assert projected["kind"] == "inventor-heatmap"
    assert len(projected["cells"]) == len(projected["x"]) * len(projected["y"])
    missing = projected["y"].index("D")
    assert all(c["value"] is None for c in projected["cells"] if c["y"] == missing)
    assert any(c["value"] == 0 for c in projected["cells"] if c["y"] != missing)
    assert data == before


def test_technology_rejects_zero_reference_mass_before_division(tmp_path):
    from patent_analysis.inventor_profiles import technology_profiles

    prepared = prepared_patents(tmp_path)
    stats = technology_profiles(
        form_units(prepared.observations, unit="records"), prepared.observations
    )
    stats["coverage"]["classification_mass"] = {"value": 0.0, "numerator": "0", "denominator": "1"}
    with pytest.raises(ValueError, match="inconsistent"):
        project_advanced_data(
            "inventor-technology.v1", {"analysis_id": "inventor-technology.v1", "statistics": stats}
        )


def test_activity_calendar_gaps_are_unknown_not_retirement():
    from test_inventor_graph import obs

    from patent_analysis.inventor_activity import annual_activity

    rows = (obs("1", ("A", "B"), "2020"), obs("2", ("A", "C"), "2022-03"), obs("3", ("D",), None))
    data = {
        "analysis_id": "inventor-activity.v1",
        "statistics": annual_activity(form_units(rows, unit="records"), rows),
    }
    before = deepcopy(data)
    projection = project_advanced_data("inventor-activity.v1", data)
    assert projection["years"] == [2020, 2021, 2022]
    assert "D" in projection["lanes"]
    assert projection["bands"] == []
    assert any(n["x"] == 2021 and n["state"] == "unknown" for n in projection["nodes"])
    assert all(not e["gap"] for e in projection["links"])
    assert "退職" in projection["context"] and "欠損" in projection["context"]
    assert data == before
