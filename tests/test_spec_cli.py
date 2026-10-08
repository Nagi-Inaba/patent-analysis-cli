from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path

import pytest

from patent_analysis import AnalysisContractError, api, cli

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def _spec(name="growth"):
    return json.loads((EXAMPLES / "basic" / f"{name}.json").read_bytes())


@pytest.mark.parametrize(
    "case", ["selection", "year", "padded-role", "timeline-range", "same-role",
             "missing-binding", "filter-binding", "family-binding", "unknown-profile",
             "duplicate-column"]
)
def test_spec_validation_rejects_unexecutable_conditions_before_csv_access(case, tmp_path):
    spec = _spec({"timeline-range": "timeline", "same-role": "concentration"}.get(case, "growth"))
    if case == "selection":
        spec["population"]["selection_sets"] = [
            {"dimension_role": "group", "mode": "include", "values": []}
        ]
    elif case == "year":
        spec["population"]["filters"] = [
            {"role": "year", "effect": "include", "match": "year", "value": 1799}
        ]
    elif case == "padded-role":
        spec["population"]["filters"] = [
            {"role": " year ", "effect": "include", "match": "exact", "value": "2020"}
        ]
    elif case == "timeline-range":
        spec["parameters"].update(start_year=2025, end_year=2020)
    elif case == "missing-binding":
        spec["resolution"] = {"bindings": {}}
    elif case == "unknown-profile":
        spec["resolution"] = {"profile": "PRIVATE", "bindings": {}}
    elif case == "duplicate-column":
        spec["resolution"]["bindings"] = {"group": "PRIVATE", "year": "PRIVATE"}
    elif case == "filter-binding":
        spec["population"]["filters"] = [
            {"role": "missing", "effect": "include", "match": "exact", "value": "2020"}
        ]
    elif case == "family-binding":
        spec["population"].update(family_mode="earliest", family_role="missing")
    else:
        spec["parameters"]["category_role"] = spec["parameters"]["date_role"]
    raw = json.dumps(spec).encode()
    with pytest.raises(AnalysisContractError) as validated:
        api.validate_analysis_spec_bytes(raw)
    with pytest.raises(AnalysisContractError) as executed:
        api.run_analysis_csv("not-present.csv", raw, allowed_root=tmp_path)
    assert validated.value.code == executed.value.code == "analysis.invalid"
    assert "PRIVATE" not in str(validated.value)


def test_growth_label_budget_uses_public_cli_error(tmp_path, monkeypatch, capsys):
    source = b"year,group\n2020," + b"A" * 5000 + b"\n"
    (tmp_path / "input.csv").write_bytes(source)
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))
    monkeypatch.setattr(sys, "stdin", StringIO(json.dumps(_spec())))
    assert cli.main(["analyze", "input.csv", "--spec", "-", "--json"]) == 2
    captured = capsys.readouterr()
    assert captured.err == ""
    result = json.loads(captured.out)
    assert result["error"]["code"] == "analysis.invalid"
    assert result["error"]["details"] == {}
    assert "AAAA" not in captured.out
    assert (tmp_path / "input.csv").read_bytes() == source


def test_validate_spec_stdin_and_schema_need_no_root(monkeypatch, capsys):
    monkeypatch.delenv("PATENT_ANALYSIS_ALLOWED_ROOT", raising=False)
    raw = json.dumps(_spec())
    monkeypatch.setattr(sys, "stdin", StringIO(raw))
    assert cli.main(["validate-spec", "-", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == api.validate_analysis_spec_bytes(raw.encode())
    name = "growth-parameters-v1.schema.json"
    assert cli.main(["schema", name, "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "schema_name": name, "schema": api.get_public_schema(name),
    }


@pytest.mark.parametrize(
    ("arguments", "stdin", "code", "error"),
    [
        (["validate-spec", "spec.json", "--json"], "", 3, "input.invalid"),
        (["validate-spec", "-", "--json"], "{", 3, "input.invalid"),
        (["validate-spec", "-", "--json"], "{}", 2, "analysis.invalid"),
        (["schema", "../PRIVATE", "--json"], "", 2, "analysis.invalid"),
    ],
)
def test_spec_cli_errors_are_safe(arguments, stdin, code, error, monkeypatch, capsys):
    monkeypatch.delenv("PATENT_ANALYSIS_ALLOWED_ROOT", raising=False)
    monkeypatch.setattr(sys, "stdin", StringIO(stdin))
    assert cli.main(arguments) == code
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out)["error"]["code"] == error
    assert "PRIVATE" not in captured.out


def test_validate_spec_file_resolves_against_allowed_root(tmp_path, monkeypatch, capsys):
    raw = json.dumps(_spec()).encode()
    (tmp_path / "spec.json").write_bytes(raw)
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))
    assert cli.main(["validate-spec", "spec.json", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["valid"] is True
    assert (tmp_path / "spec.json").read_bytes() == raw
