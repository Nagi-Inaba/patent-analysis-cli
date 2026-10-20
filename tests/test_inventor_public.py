import json
from decimal import ROUND_UP, Context, Inexact, localcontext

import pytest

from patent_analysis.analysis_runner import run_analysis


def spec(analysis_id="inventor-network.v1", parameters=None):
    return {
        "analysis_contract_version": "2.0.0",
        "analysis_id": analysis_id,
        "resolution": {
            "bindings": {
                "record_id": "record",
                "inventor_ids": "people",
                "date": "day",
                "classification": "ipc",
                "applicant_ids": "org",
            }
        },
        "normalization": {"profiles": []},
        "population": {"family_mode": "records", "filters": [], "selection_sets": []},
        "parameters": parameters or {},
    }


def write_patents(root):
    rows = [
        {
            "record": "r1",
            "people": '["A","B"]',
            "day": "2023-01-01",
            "ipc": "A01B 1/00",
            "org": '["e1"]',
        },
        {
            "record": "r2",
            "people": '["B","C"]',
            "day": "2024-01-01",
            "ipc": "C02F 1/00",
            "org": '["e2"]',
        },
        {"record": "r3", "people": '["D"]', "day": "", "ipc": "", "org": "[]"},
    ]
    (root / "patents.json").write_text(json.dumps(rows), encoding="utf-8")


def test_public_network_keeps_isolates_and_missing_date_evidence(tmp_path):
    write_patents(tmp_path)
    result = run_analysis("patents.json", json.dumps(spec()).encode(), allowed_root=tmp_path)
    assert result["analysis_id"] == "inventor-network.v1"
    assert result["result_variant"] == "network"
    assert result["population"] == {"input_rows": 3, "analyzed_rows": 3, "excluded_rows": 0}
    graph = result["data"]["statistics"]
    assert [(n["inventor_id"], n["degree"]) for n in graph["nodes"]] == [
        ("A", 1),
        ("B", 2),
        ("C", 1),
        ("D", 0),
    ]
    assert graph["basis"]["metrics_scope"] == "full_graph"
    assert result["data"]["input_coverage"]["missing_date"] == 1
    assert all(e["record_ids"] for e in graph["edges"])
    assert result["data"]["family_basis"]["family_mode"] == "records"


@pytest.mark.parametrize(
    "caller_context",
    [Context(rounding=ROUND_UP), Context(traps=[Inexact])],
    ids=["round-up", "inexact-trap"],
)
def test_public_fractional_analysis_ignores_caller_decimal_context(tmp_path, caller_context):
    source = tmp_path / "patents.json"
    raw = json.dumps([
        dict(record="r1", people='["A","B","C"]', day="2023-01-01", ipc="A01B", org="[]")
    ]).encode()
    source.write_bytes(raw)
    request = json.dumps(spec(parameters={"person_weight": "fractional"})).encode()
    with localcontext(Context()):
        expected = run_analysis(source.name, request, allowed_root=tmp_path)
    with localcontext(caller_context):
        result = run_analysis(source.name, request, allowed_root=tmp_path)
    assert result == expected
    assert [node["activity"] for node in result["data"]["statistics"]["nodes"]] == [
        {"value": 0.333333333333, "numerator": "1", "denominator": "3"}
    ] * 3
    assert source.read_bytes() == raw


def test_public_curated_alias_filters_on_resolved_identity(tmp_path):
    from test_inventor_foundation_sidecars import bundle, save

    write_patents(tmp_path)
    document = bundle()
    document["tables"]["identities"][0]["raw_alias"] = "A"
    save(tmp_path, document)
    request = spec(parameters={"auxiliary": {"format": "json", "path": "sidecar.json"}})
    request["population"]["filters"] = [
        {"role": "inventor_id", "effect": "include", "match": "exact", "value": "p1"}
    ]
    result = run_analysis("patents.json", json.dumps(request).encode(), allowed_root=tmp_path)
    assert result["population"]["analyzed_rows"] == 1
    assert [n["inventor_id"] for n in result["data"]["statistics"]["nodes"]] == ["B", "p1"]
    assert result["data"]["provenance"]["sidecar_state"] == "provided"
    assert result["data"]["provenance"]["sidecars"][0]["format"] == "json"
