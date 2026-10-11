import json

from test_inventor_public import spec, write_patents

from patent_analysis.analysis_runner import run_analysis


def test_cluster_flow_memberships_and_missing_date(tmp_path):
    write_patents(tmp_path)
    result = run_analysis(
        "patents.json", json.dumps(spec("inventor-cluster-flow.v1")).encode(), allowed_root=tmp_path
    )
    stats = result["data"]["statistics"]
    shared = [link for link in stats["links"] if link["kind"] == "shared_members"]
    assert len(shared) == 1 and shared[0]["members"] == ['["id","B"]']
    assert stats["unplottable"][0]["inventor_id"] == "D"
    assert stats["unplottable"][0]["reasons"] == ["missing_date"]
    assert stats["missing_date_record_ids"] == ["r3"]
