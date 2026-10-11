import json

from test_inventor_public import spec, write_patents

from patent_analysis.analysis_runner import run_analysis


def test_mobility_observations_are_not_employment(tmp_path):
    write_patents(tmp_path)
    result = run_analysis(
        "patents.json", json.dumps(spec("inventor-mobility.v1")).encode(), allowed_root=tmp_path
    )
    stats = result["data"]["statistics"]
    assert len(stats["associations"]) == 5
    assert len(stats["candidates"]) == 1
    candidate = stats["candidates"][0]
    assert candidate["person_key"] == ["id", "B"]
    assert candidate["from_ids"] == ["e1"] and candidate["to_ids"] == ["e2"]
    assert candidate["period_start"] == "2023-01-01"
    assert candidate["employment_status"] == "unknown"
    assert candidate["candidate_status"] == "candidate"
    assert stats["coverage"]["missing_dates"] == 1
    assert stats["coverage"]["sidecar"] == "input_not_provided"
