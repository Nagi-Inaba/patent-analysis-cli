import json

import pytest
from test_inventor_public import spec, write_patents

from patent_analysis.analysis_registry import get_analysis_definition
from patent_analysis.api import get_public_schema, run_analysis_table
from patent_analysis_mcp.exposure import visible_analysis_ids, visible_schema_names

IDS = (
    "inventor-network.v1",
    "inventor-ego-network.v1",
    "inventor-technology.v1",
    "inventor-activity.v1",
    "inventor-cluster-flow.v1",
    "inventor-similarity.v1",
    "inventor-impact.v1",
    "inventor-mobility.v1",
    "inventor-mobility-flow.v1",
    "inventor-mobility-evidence.v1",
)


@pytest.mark.parametrize("analysis_id", IDS)
def test_native_schemas_explicitly_visible(analysis_id):
    assert analysis_id in visible_analysis_ids()
    for kind in ("parameters", "result"):
        name = analysis_id[:-3] + "-" + kind + "-v1.schema.json"
        assert get_public_schema(name)["properties"]["analysis_id"]["const"] == analysis_id
        assert name in visible_schema_names()


def test_sidecar_schema_explicitly_visible():
    assert (
        get_public_schema("inventor-sidecar-v1.schema.json")["properties"]["version"]["const"]
        == "1.0.0"
    )
    assert "inventor-sidecar-v1.schema.json" in visible_schema_names()


def test_evidence_table_without_svg(tmp_path):
    write_patents(tmp_path)
    raw = json.dumps(spec("inventor-mobility-evidence.v1")).encode()
    table = run_analysis_table("patents.json", raw, allowed_root=tmp_path)
    assert "candidate_id" in table and "employment_status" in table and "mc_" in table
    assert get_analysis_definition("inventor-mobility-evidence.v1").compatible_render_marks == ()
