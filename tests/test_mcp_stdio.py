from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import anyio
import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "mcp"
RANKING_SPEC = json.loads((FIXTURE_ROOT / "ranking-spec.json").read_text(encoding="utf-8"))


def _server_parameters(input_root: Path, output_root: Path) -> StdioServerParameters:
    args = [
        "-m",
        "patent_analysis_mcp.server",
        "--input-root",
        f"input={input_root}",
        "--output-root",
        f"output={output_root}",
    ]
    node = shutil.which("node")
    if sys.platform in {"win32", "darwin"} and node:
        args.extend(("--node", node))
    return StdioServerParameters(command=sys.executable, args=args, cwd=Path.cwd())


def test_real_stdio_initializes_lists_and_calls_the_shared_core(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    input_root.mkdir()
    output_root.mkdir()
    (input_root / "input.csv").write_bytes((FIXTURE_ROOT / "input.csv").read_bytes())

    async def scenario() -> None:
        with anyio.fail_after(20):
            async with stdio_client(_server_parameters(input_root, output_root)) as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    initialized = await session.initialize()
                    assert initialized.server_info.name == "patent-analysis-cli"
                    tools = await session.list_tools()
                    assert tuple(tool.name for tool in tools.tools) == (
                        "patent_analysis.capabilities",
                        "patent_analysis.schema",
                        "patent_analysis.inspect",
                        "patent_analysis.validate_spec",
                        "patent_analysis.analyze",
                        "patent_analysis.render",
                    )
                    inspection = await session.call_tool(
                        "patent_analysis.inspect",
                        {"input_root_id": "input", "path": "input.csv"},
                    )
                    assert inspection.is_error is False
                    assert inspection.structured_content["ok"] is True
                    analysis = await session.call_tool(
                        "patent_analysis.analyze",
                        {
                            "input_root_id": "input",
                            "path": "input.csv",
                            "spec": RANKING_SPEC,
                        },
                    )
                    assert analysis.is_error is False
                    assert analysis.structured_content["content"]["result"]["rows"][0][
                        "label"
                    ] == "A社"
                    assert "receipt" not in analysis.structured_content["content"]
                    assert "sha256" not in repr(
                        analysis.structured_content["content"]
                    ).casefold()
                    render_handle = analysis.structured_content["content"]["render_handle"]

                    node = shutil.which("node")
                    if sys.platform in {"win32", "darwin"} and node:
                        rendered = await session.call_tool(
                            "patent_analysis.render",
                            {
                                "output_root_id": "output",
                                "output_path": "session-1",
                                "analysis_handle": render_handle,
                                "mark": "ranking-svg.v1",
                            },
                        )
                        assert rendered.is_error is False
                        assert rendered.structured_content["content"]["status"] == "created"

    anyio.run(scenario)


@pytest.mark.parametrize(
    "root_kind,arrangement,expected_code",
    [
        pytest.param("input", "parent-first", 2, id="nested-input-parent-first"),
        pytest.param("input", "child-first", 2, id="nested-input-child-first"),
        pytest.param("output", "parent-first", 2, id="nested-output-parent-first"),
        pytest.param("output", "child-first", 2, id="nested-output-child-first"),
        pytest.param("input", "siblings", 0, id="disjoint-inputs"),
        pytest.param("output", "siblings", 0, id="disjoint-outputs"),
    ],
)
def test_stdio_startup_requires_disjoint_roots(
    tmp_path: Path, root_kind: str, arrangement: str, expected_code: int,
) -> None:
    declarations = {kind: [tmp_path / kind] for kind in ("input", "output")}
    extra = (
        tmp_path / f"{root_kind}-sibling"
        if arrangement == "siblings"
        else declarations[root_kind][0] / "child"
    )
    declarations[root_kind].append(extra)
    for paths in declarations.values():
        for path in paths:
            path.mkdir(parents=True, exist_ok=True)
    if arrangement == "child-first":
        declarations[root_kind].reverse()
    args = [sys.executable, "-m", "patent_analysis_mcp.server"]
    for kind, paths in declarations.items():
        for index, path in enumerate(paths):
            args.extend((f"--{kind}-root", f"{kind}{index}={path}"))

    completed = subprocess.run(
        args, input=b"", capture_output=True, check=False, timeout=20,
    )

    assert completed.returncode == expected_code
    assert completed.stdout == b""
    assert completed.stderr.splitlines() == (
        [b"MCP startup configuration is invalid"] if expected_code else []
    )


@pytest.mark.parametrize(
    "wire_input",
    [
        pytest.param(b"{not-json}\n", id="malformed"),
        pytest.param(
            b'{"padding":"' + (b"x" * (2 * 1024 * 1024 + 65537)) + b'"}\n',
            id="oversized",
        ),
    ],
)
def test_stdio_malformed_or_oversized_input_exits_on_eof_without_echo(
    tmp_path: Path,
    wire_input: bytes,
) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    input_root.mkdir()
    output_root.mkdir()
    parameters = _server_parameters(input_root, output_root)

    completed = subprocess.run(
        [parameters.command, *parameters.args],
        cwd=parameters.cwd,
        input=wire_input,
        capture_output=True,
        check=False,
        timeout=20,
    )

    assert completed.returncode == 0
    assert len(completed.stdout) <= 64 * 1024
    assert len(completed.stderr) <= 64 * 1024
    assert b"padding" not in completed.stdout
    assert b"padding" not in completed.stderr
