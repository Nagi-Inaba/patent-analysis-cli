"""Exercise all ten approved JSON analyses through the real local MCP SDK.

The client launches the actual server in a child process. This verifies JSON
transport, not Windows SVG rendering, remote hosting or whole-product acceptance.
"""
from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path

import anyio
import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from patent_analysis import api

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "advanced"
ANALYSES = (
    "growth-quadrant.v1", "entry-exit.v1", "citation.v1", "matrix-composition.v1",
    "new-entrants.v1", "compara.v1", "cooccurrence.v1", "collaboration-network.v1",
    "uniqueness.v1", "shared-involvement.v1",
)


def _assert_public_result(value: object) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            assert key not in {"receipt", "source_fields", "raw_rows", "absolute_path"}
            assert not key.casefold().endswith("sha256")
            _assert_public_result(child)
    elif isinstance(value, list):
        for child in value:
            _assert_public_result(child)


async def _call(session: ClientSession, name: str, arguments: dict) -> dict:
    result = await session.call_tool(name, arguments)
    assert result.is_error is False, result
    envelope = result.structured_content
    assert isinstance(envelope, dict) and envelope["ok"] is True
    return envelope["content"]


@pytest.mark.parametrize("analysis_id", ANALYSES)
def test_advanced_json_sdk_stdio_discovery_and_results_match_public_api(
    analysis_id: str, tmp_path: Path,
) -> None:
    input_root, output_root = tmp_path / "input", tmp_path / "output"
    input_root.mkdir()
    output_root.mkdir()
    source = input_root / "patents.csv"
    source_before = (EXAMPLES / "patents.csv").read_bytes()
    source.write_bytes(source_before)
    spec_bytes = (EXAMPLES / f"{analysis_id[:-3]}.json").read_bytes()
    spec = json.loads(spec_bytes)
    original_spec = deepcopy(spec)
    direct = api.run_analysis_csv(source.name, spec_bytes, allowed_root=input_root)
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "patent_analysis_mcp.server",
              "--input-root", f"input={input_root}",
              "--output-root", f"output={output_root}"],
        cwd=ROOT,
    )

    async def scenario() -> None:
        with anyio.fail_after(20):
            async with stdio_client(parameters) as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    initialized = await session.initialize()
                    assert initialized.server_info.name == "patent-analysis-cli"
                    tools = await session.list_tools()
                    assert {"patent_analysis.capabilities", "patent_analysis.schema",
                            "patent_analysis.validate_spec", "patent_analysis.analyze"} <= {
                        tool.name for tool in tools.tools
                    }
                    capabilities = await _call(session, "patent_analysis.capabilities", {})
                    by_id = {item["analysis_id"]: item for item in capabilities["analyses"]}
                    assert set(ANALYSES) <= set(by_id)
                    for kind in ("parameters", "result"):
                        name = f"{analysis_id[:-3]}-{kind}-v1.schema.json"
                        exposed = await _call(session, "patent_analysis.schema", {
                            "schema_name": name,
                        })
                        assert exposed["schema"] == api.get_public_schema(name)
                    validated = await _call(session, "patent_analysis.validate_spec", {
                        "spec": spec,
                    })
                    assert validated["analysis_id"] == analysis_id

                    # A rejected request must neither run a different analysis
                    # nor destroy the live session before the next valid call.
                    invalid = deepcopy(spec)
                    invalid["parameters"]["top_n"] = True
                    rejected = await session.call_tool("patent_analysis.validate_spec", {
                        "spec": invalid,
                    })
                    assert rejected.is_error is True
                    assert rejected.structured_content["ok"] is False
                    assert rejected.structured_content["error"]["code"] == "input.invalid"
                    assert str(input_root) not in repr(rejected.structured_content)
                    handles = []
                    for _ in range(2):
                        result = await _call(session, "patent_analysis.analyze", {
                            "input_root_id": "input", "path": source.name, "spec": spec,
                        })
                        assert result["analysis_id"] == analysis_id
                        assert result["data"] == direct["data"]
                        assert result["population"] == direct["population"]
                        renderable = bool(by_id[analysis_id]["render_marks"])
                        assert ("render_handle" in result) == renderable
                        if renderable:
                            handle = result["render_handle"]
                            assert isinstance(handle, str) and handle not in handles
                            handles.append(handle)
                        _assert_public_result(result)
                        assert str(tmp_path) not in repr(result)

    anyio.run(scenario)
    assert source.read_bytes() == source_before
    assert spec == original_spec
    assert list(output_root.iterdir()) == []
