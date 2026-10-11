"""Execute the public inventor-analysis documentation examples."""

from pathlib import Path

import pytest

from patent_analysis.api import run_analysis

ROOT = Path(__file__).resolve().parents[1] / "examples"
INVENTOR_IDS = (
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


@pytest.mark.parametrize("analysis_id", INVENTOR_IDS)
def test_documented_inventor_example_executes(analysis_id):
    spec = ROOT / "inventor-analysis" / f"{analysis_id}.json"
    result = run_analysis(
        "inventor-analysis/patents.json",
        spec.read_bytes(),
        allowed_root=ROOT,
    )
    assert result["analysis_id"] == analysis_id
    assert result["population"] == {"input_rows": 4, "analyzed_rows": 4, "excluded_rows": 0}
    assert result["data"]["provenance"]["sidecar_state"] == "input_not_provided"
    assert result["data"]["statistics"]
    assert result["data"]["input_coverage"]["missing_date"] == 1
