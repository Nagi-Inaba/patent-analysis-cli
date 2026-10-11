import json

import pytest
from test_inventor_foundation_sidecars import bundle, save
from test_inventor_public import spec, write_patents

from patent_analysis.analysis_runner import run_analysis
from patent_analysis.errors import DatasetInputError


@pytest.mark.parametrize(
    "aid", ["inventor-mobility.v1", "inventor-mobility-flow.v1", "inventor-mobility-evidence.v1"]
)
def test_direct_person_review_not_corporate_status_and_unknown_review_rejected(tmp_path, aid):
    write_patents(tmp_path)
    request = spec(aid)
    baseline = run_analysis("patents.json", json.dumps(request).encode(), allowed_root=tmp_path)
    cid = baseline["data"]["statistics"]["candidates"][0]["candidate_id"]
    d = bundle()
    d["tables"]["sources"][0]["kind"] = "employment_record"
    d["tables"]["personal_evidence"] = [
        dict(
            evidence_id="peB",
            inventor_id="B",
            from_entity_id="e1",
            to_entity_id="e2",
            valid_from="2023-01-01",
            valid_to="2024-01-01",
            type="employment_move",
            claim_status="reported",
            source_ids=["s1"],
        )
    ]
    d["tables"]["reviews"] = [
        dict(
            review_id="rvB",
            inventor_id="B",
            claim="employment_move",
            status="accepted",
            reason="Synthetic direct support",
            reviewed_date="2025",
            evidence_ids=["peB"],
            event_ids=[],
            record_ids=[],
            source_ids=["s1"],
            supersedes_review_id=None,
        )
    ]
    save(tmp_path, d)
    request["parameters"] = {
        "auxiliary": {"format": "json", "path": "sidecar.json"},
        "review_bindings": {cid: ["rvB"]},
    }
    reviewed = run_analysis("patents.json", json.dumps(request).encode(), allowed_root=tmp_path)
    c = reviewed["data"]["statistics"]["candidates"][0]
    assert c["candidate_id"] == cid and c["employment_status"] == "confirmed"
    assert c["corporate_status"] == "unknown"
    assert c["reviews"][0]["active"] and c["evidence"][0]["direct_employment_support"]
    request["parameters"]["review_bindings"][cid] = ["SECRET-UNKNOWN-REVIEW"]
    with pytest.raises(DatasetInputError) as caught:
        run_analysis("patents.json", json.dumps(request).encode(), allowed_root=tmp_path)
    assert "SECRET" not in str(caught.value)


def test_evidence_stable_candidate_key_bound_review_reinput(tmp_path):
    write_patents(tmp_path)
    request = spec("inventor-mobility-evidence.v1")
    baseline = run_analysis("patents.json", json.dumps(request).encode(), allowed_root=tmp_path)
    candidate = baseline["data"]["statistics"]["candidates"][0]
    d = bundle()
    d["tables"]["reviews"] = [
        dict(
            review_id="rvB",
            inventor_id="B",
            claim="employment_move",
            status="accepted",
            reason="User-only assessment",
            reviewed_date="2025",
            evidence_ids=[],
            event_ids=[],
            record_ids=[],
            source_ids=["s1"],
            supersedes_review_id=None,
        )
    ]
    save(tmp_path, d)
    request["parameters"] = {
        "auxiliary": {"format": "json", "path": "sidecar.json"},
        "review_bindings": {candidate["candidate_id"]: ["rvB"]},
    }
    reviewed = run_analysis("patents.json", json.dumps(request).encode(), allowed_root=tmp_path)
    result = reviewed["data"]["statistics"]["candidates"][0]
    assert result["candidate_id"] == candidate["candidate_id"]
    assert result["employment_status"] == "user_asserted"
    assert result["reviews"][0]["review_id"] == "rvB"
    assert reviewed["result_variant"] == "grouped-metrics"
    request["parameters"]["review_bindings"] = {"unknown-secret": ["rvB"]}
    with pytest.raises(DatasetInputError) as e:
        run_analysis("patents.json", json.dumps(request).encode(), allowed_root=tmp_path)
    assert "secret" not in str(e.value)
