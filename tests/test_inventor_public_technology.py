import json

from test_inventor_public import spec, write_patents

from patent_analysis.analysis_runner import run_analysis


def test_technology_full_reference_and_missing_profile(tmp_path):
    write_patents(tmp_path)
    request = spec("inventor-technology.v1", {"classification_weight": "fractional"})
    result = run_analysis("patents.json", json.dumps(request).encode(), allowed_root=tmp_path)
    stats = result["data"]["statistics"]
    assert stats["coverage"]["classification_mass"]["numerator"] == "4"
    assert stats["classifications"][0]["reference_share"] == 0.5
    assert stats["profiles"][-1]["undefined_reason"] == "missing_classification"
    assert result["data"]["provenance"]["sidecar_state"] == "input_not_provided"
