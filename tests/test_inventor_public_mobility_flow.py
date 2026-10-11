import json

from test_inventor_public import spec, write_patents

from patent_analysis.analysis_runner import run_analysis


def test_group_flow_missing_mapping_not_current_parent_backfill(tmp_path):
    from test_inventor_foundation_sidecars import bundle, save

    write_patents(tmp_path)
    save(tmp_path, bundle())
    request = spec(
        "inventor-mobility-flow.v1",
        {
            "axis": "group",
            "mode": "candidate_moves",
            "auxiliary": {"format": "json", "path": "sidecar.json"},
        },
    )
    result = run_analysis("patents.json", json.dumps(request).encode(), allowed_root=tmp_path)
    assert result["data"]["statistics"]["flows"] == []
    assert result["data"]["statistics"]["unallocated"][0]["reason"] == "missing_group_mapping"


def test_recurrence_retains_cycles_unique_people_and_event_counts(tmp_path):
    rows = [
        dict(
            record=f"r{i}",
            people='["B"]',
            day=f"202{i}-01-01",
            ipc="A01B 1/00",
            org=json.dumps([org]),
        )
        for i, org in enumerate(["e1", "e2", "e1", "e2"])
    ]
    (tmp_path / "patents.json").write_text(json.dumps(rows), encoding="utf-8")
    result = run_analysis(
        "patents.json",
        json.dumps(spec("inventor-mobility-flow.v1")).encode(),
        allowed_root=tmp_path,
    )
    s = result["data"]["statistics"]
    assert len(s["candidates"]) == 3 and len(s["flows"]) == 2
    forward = next(f for f in s["flows"] if f["from_id"] == "e1")
    assert forward["unique_inventors"] == 1 and forward["transition_events"] == 2
    assert len(forward["candidate_ids"]) == 2


def test_fractional_multientity_mass_is_exact_and_not_unique_headcount(tmp_path):
    rows = [
        dict(record="r1", people='["B"]', day="2023-01-01", ipc="A01B 1/00", org='["e1","e2"]'),
        dict(record="r2", people='["B"]', day="2024-01-01", ipc="A01B 1/00", org='["e3","e4"]'),
    ]
    (tmp_path / "patents.json").write_text(json.dumps(rows), encoding="utf-8")
    request = spec(
        "inventor-mobility-flow.v1",
        {"axis": "legal_entity", "mode": "observations", "allocation": "fractional_flows"},
    )
    result = run_analysis("patents.json", json.dumps(request).encode(), allowed_root=tmp_path)
    s = result["data"]["statistics"]
    assert len(s["flows"]) == 4
    assert all(
        f["flow_weight"]["numerator"] == "1" and f["flow_weight"]["denominator"] == "4"
        for f in s["flows"]
    )
    assert s["allocation_summary"]["allocated_event_mass"]["value"] == 1
    assert s["allocation_summary"]["total_event_mass"]["value"] == 1
    assert all(f["candidate_ids"] == [s["candidates"][0]["candidate_id"]] for f in s["flows"])
    request["parameters"]["allocation"] = "unique_inventors"
    unique = run_analysis("patents.json", json.dumps(request).encode(), allowed_root=tmp_path)
    assert unique["data"]["statistics"]["flows"] == []
    assert (
        unique["data"]["statistics"]["allocation_summary"]["unallocated_event_mass"]["value"] == 1
    )


def test_mobility_flow_allocates_literal_candidate_references(tmp_path):
    write_patents(tmp_path)
    result = run_analysis(
        "patents.json",
        json.dumps(
            spec(
                "inventor-mobility-flow.v1",
                {
                    "axis": "legal_entity",
                    "mode": "candidate_moves",
                    "allocation": "unique_inventors",
                },
            )
        ).encode(),
        allowed_root=tmp_path,
    )
    stats = result["data"]["statistics"]
    assert len(stats["flows"]) == 1
    assert stats["flows"][0]["from_id"] == "e1" and stats["flows"][0]["to_id"] == "e2"
    assert stats["flows"][0]["inventor_ids"] == ["B"]
    assert stats["flows"][0]["candidate_ids"] == [stats["candidates"][0]["candidate_id"]]
    assert stats["candidates"][0]["employment_status"] == "unknown"
