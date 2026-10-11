import json

import pytest
from test_inventor_foundation_sidecars import save
from test_inventor_public import write_patents
from test_inventor_public_contract import request_for
from test_inventor_public_exposure import IDS
from test_inventor_public_impact import citation_bundle

from patent_analysis_mcp.roots import ApprovedRoot, RootRegistry
from patent_analysis_mcp.tool_handlers import ToolHandlers


def roots_for(tmp_path):
    source, output = tmp_path / "input", tmp_path / "output"
    source.mkdir()
    output.mkdir()
    return RootRegistry(
        input_roots=(ApprovedRoot("input", source),), output_roots=(ApprovedRoot("output", output),)
    ), source


@pytest.mark.parametrize("aid", IDS)
def test_real_mcp_native_analysis_strips_hashes_not_evidence(tmp_path, aid):
    roots, source = roots_for(tmp_path)
    write_patents(source)
    document = citation_bundle()
    document["tables"]["identities"][0]["raw_alias"] = "A"
    save(source, document)
    result = ToolHandlers(roots=roots).call(
        "patent_analysis.analyze",
        dict(
            input_root_id="input",
            path="patents.json",
            spec=request_for(aid, auxiliary=dict(format="json", path="sidecar.json")),
        ),
    )
    assert result["ok"] is True
    text = json.dumps(result["content"])
    assert result["content"]["analysis_id"] == aid
    assert "sha256" not in text and "receipt" not in text
    assert str(tmp_path) not in text
    assert "s1" in text


@pytest.mark.parametrize("aid", IDS)
def test_real_mcp_bad_auxiliary_path_safe_error(tmp_path, aid):
    roots, source = roots_for(tmp_path)
    write_patents(source)
    result = ToolHandlers(roots=roots).call(
        "patent_analysis.analyze",
        dict(
            input_root_id="input",
            path="patents.json",
            spec=request_for(aid, auxiliary=dict(format="json", path="../SECRET.json")),
        ),
    )
    assert result["ok"] is False and result["error"]["code"] == "input.invalid"
    assert "SECRET" not in json.dumps(result)
