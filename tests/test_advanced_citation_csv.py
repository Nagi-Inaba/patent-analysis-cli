"""Real CSV/API/CLI/MCP-handler regressions for citation numeric validation.

Requires the complete repository. No CSV pipeline, calculation, API or handler
is mocked; this file is not part of a kernel-only verification run.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from patent_analysis import api, cli
from patent_analysis_mcp.roots import ApprovedRoot, RootRegistry
from patent_analysis_mcp.tool_handlers import ToolHandlers


@pytest.mark.parametrize(("values", "expected"), [
    (
        ("1,000", "99,99", "1000000000000.00001", "cited by: 12.5",
         "ci,tations: 7", "0", "1,000.0,1"),
        [("record0", 1000), ("record3", 12.5), ("record5", 0)],
    ),
    (("1,2", "1000000000000.00001"), []),
    (
        ("1,000,000,000,000.000", "1,000", "0"),
        [("record0", 1000000000000), ("record1", 1000), ("record2", 0)],
    ),
])
def test_citation_numeric_validation_agrees_across_real_csv_entrypoints(
    values: tuple[str, ...], expected: list[tuple[str, float]], tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    input_root, output_root = tmp_path / "input", tmp_path / "output"
    input_root.mkdir()
    output_root.mkdir()
    source = input_root / "patents.csv"
    with source.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("year", "label", "cites"))
        writer.writerows((2024, f"record{i}", value) for i, value in enumerate(values))
    spec = {
        "analysis_contract_version": "2.0.0", "analysis_id": "citation.v1",
        "resolution": {"bindings": {"year": "year", "label": "label", "cites": "cites"}},
        "normalization": {"profiles": []},
        "population": {"filters": [], "selection_sets": [], "family_mode": "records"},
        "parameters": {"date_role": "year", "label_role": "label", "citation_role": "cites"},
    }
    spec_bytes = json.dumps(spec, ensure_ascii=False).encode("utf-8")
    spec_path = input_root / "spec.json"
    spec_path.write_bytes(spec_bytes)
    source_before = source.read_bytes()
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(input_root))

    direct = api.run_analysis_csv(source.name, spec_bytes, allowed_root=input_root)
    assert [(p["label"], p["citation_value"]) for p in direct["data"]["points"]] == expected
    assert direct["population"] == {
        "input_rows": len(values), "analyzed_rows": len(expected),
        "excluded_rows": len(values) - len(expected),
    }
    assert direct["data"]["contributions"] == len(expected)
    assert api.run_analysis_csv(source.name, spec_bytes, allowed_root=input_root) == direct

    assert cli.main(["analyze", source.name, "--spec", spec_path.name, "--json"]) == 0
    captured = capsys.readouterr()
    assert not captured.err
    assert json.loads(captured.out) == direct

    handlers = ToolHandlers(roots=RootRegistry(
        input_roots=(ApprovedRoot("input", input_root),),
        output_roots=(ApprovedRoot("output", output_root),),
    ))
    via_mcp = handlers.call("patent_analysis.analyze", {
        "input_root_id": "input", "path": source.name, "spec": spec,
    })
    assert via_mcp["ok"] is True, via_mcp
    assert via_mcp["content"]["data"] == direct["data"]
    assert via_mcp["content"]["population"] == direct["population"]
    assert source.read_bytes() == source_before
    assert spec_path.read_bytes() == spec_bytes
