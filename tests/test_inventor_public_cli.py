import json
import sys
from io import StringIO

import pytest
from test_inventor_public import write_patents
from test_inventor_public_contract import request_for
from test_inventor_public_exposure import IDS

from patent_analysis.cli import main


@pytest.mark.parametrize("aid", IDS)
def test_real_native_cli_json_and_table(tmp_path, monkeypatch, capsys, aid):
    write_patents(tmp_path)
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))
    raw = json.dumps(request_for(aid))
    monkeypatch.setattr(sys, "stdin", StringIO(raw))
    assert main(["analyze", "patents.json", "--spec", "-", "--json"]) == 0
    output = capsys.readouterr()
    document = json.loads(output.out)
    assert output.err == "" and document["analysis_id"] == aid
    assert document["population"]["analyzed_rows"] == 3
    assert (
        document["data"]["statistics"]
        and document["data"]["provenance"]["sidecar_state"] == "input_not_provided"
    )
    monkeypatch.setattr(sys, "stdin", StringIO(raw))
    assert main(["analyze", "patents.json", "--spec", "-", "--format", "csv"]) == 0
    table = capsys.readouterr()
    assert table.err == "" and table.out.startswith("analysis_id,table,")
    assert aid in table.out


@pytest.mark.parametrize("aid", IDS)
def test_real_native_cli_invalid_auxiliary_private_error(tmp_path, monkeypatch, capsys, aid):
    write_patents(tmp_path)
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))
    monkeypatch.setattr(
        sys,
        "stdin",
        StringIO(
            json.dumps(request_for(aid, auxiliary=dict(format="json", path="../SECRET.json")))
        ),
    )
    assert main(["analyze", "patents.json", "--spec", "-", "--json"]) == 3
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["error"]["code"] == "input.invalid"
    assert "SECRET" not in captured.out and str(tmp_path) not in captured.out
    assert captured.err == ""
