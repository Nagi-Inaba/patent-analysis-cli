from __future__ import annotations

import json
import sys
from pathlib import Path
from xml.etree import ElementTree

import anyio
import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.mark.parametrize("name", ["matrix", "timeline", "composition"])
def test_real_stdio_categorical_analysis_and_render(name, tmp_path):
    analysis_id = f"{name}.v1"
    spec = json.loads((EXAMPLES / "basic" / f"{name}.json").read_bytes())
    expected = json.loads((EXAMPLES / "expected-aggregates.json").read_bytes())[analysis_id]
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "patent_analysis_mcp.server", "--input-root", f"input={EXAMPLES}",
              "--output-root", f"output={tmp_path}"],
    )

    async def scenario():
        with anyio.fail_after(60):
            async with stdio_client(params) as streams:
                async with ClientSession(*streams) as session:
                    await session.initialize()
                    caps = await session.call_tool("patent_analysis.capabilities", {})
                    definitions = {
                        item["analysis_id"]: item
                        for item in caps.structured_content["content"]["analyses"]
                    }
                    assert analysis_id in definitions
                    for kind in ("parameters", "result"):
                        schema = await session.call_tool(
                            "patent_analysis.schema",
                            {"schema_name": f"{name}-{kind}-v1.schema.json"},
                        )
                        assert not schema.is_error
                    validation = await session.call_tool(
                        "patent_analysis.validate_spec", {"spec": spec}
                    )
                    assert not validation.is_error
                    reply = await session.call_tool(
                        "patent_analysis.analyze",
                        {"input_root_id": "input", "path": "advanced/patents.csv", "spec": spec},
                    )
                    assert not reply.is_error, reply
                    content = reply.structured_content["content"]
                    assert content["data"] == expected
                    assert "receipt" not in content and "sha256" not in repr(content)
                    assert str(EXAMPLES) not in repr(content)
                    request = {
                        "output_root_id": "output", "output_path": name,
                        "analysis_handle": content["render_handle"], "mark": "ranking-svg.v1",
                    }
                    rejected = await session.call_tool("patent_analysis.render", request)
                    assert rejected.is_error
                    assert not (tmp_path / name).exists()
                    if sys.platform in {"win32", "darwin"}:
                        for mark in definitions[analysis_id]["render_marks"]:
                            request.update(output_path=mark, mark=mark)
                            rendered = await session.call_tool("patent_analysis.render", request)
                            assert not rendered.is_error, rendered
                            receipt = rendered.structured_content["content"]
                            svg = (tmp_path / mark / receipt["svg"]).read_bytes()
                            assert svg.startswith(b"<svg")
                            root = ElementTree.fromstring(svg)
                            assert root.attrib["role"] == "img"
                            for attr, tag in (("aria-labelledby", "title"),
                                              ("aria-describedby", "desc")):
                                node = root.find(f"{{http://www.w3.org/2000/svg}}{tag}")
                                assert node is not None and node.text
                                assert node.attrib["id"] == root.attrib[attr]
    anyio.run(scenario)
