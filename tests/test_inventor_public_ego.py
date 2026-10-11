import json

import pytest
from test_inventor_public import spec, write_patents

from patent_analysis.analysis_runner import run_analysis
from patent_analysis.errors import DatasetInputError


def test_ego_retains_full_graph_metrics(tmp_path):
    write_patents(tmp_path)
    request = spec("inventor-ego-network.v1", {"focus": ["id", "A"], "hops": 1})
    result = run_analysis("patents.json", json.dumps(request).encode(), allowed_root=tmp_path)
    graph = result["data"]["statistics"]
    assert [n["inventor_id"] for n in graph["nodes"]] == ["A", "B"]
    assert graph["nodes"][1]["degree"] == 2
    assert graph["omitted_nodes"] == 2
    assert graph["basis"]["metrics_scope"] == "full_graph"


def test_ego_unknown_literal_focus_is_private(tmp_path):
    write_patents(tmp_path)
    with pytest.raises(DatasetInputError) as e:
        run_analysis(
            "patents.json",
            json.dumps(
                spec("inventor-ego-network.v1", {"focus": ["id", "SECRET MISSING"]})
            ).encode(),
            allowed_root=tmp_path,
        )
    assert "SECRET" not in str(e.value)
