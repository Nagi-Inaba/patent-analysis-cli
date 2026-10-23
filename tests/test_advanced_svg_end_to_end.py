"""Real trusted-local SVG entrypoints for each approved advanced analysis.

Nothing here mocks calculation, CLI routing, Node rendering or publication.
Native rendering cases must be reported separately from portable model tests.
"""
from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from xml.etree import ElementTree

import pytest

from patent_analysis.advanced_renderer_build import ADVANCED_BUILD

ANALYSES = (
    "growth-quadrant.v1", "entry-exit.v1", "citation.v1", "matrix-composition.v1",
    "new-entrants.v1", "compara.v1", "cooccurrence.v1", "collaboration-network.v1",
    "uniqueness.v1", "shared-involvement.v1",
    "inventor-tracking.v1",
    "inventor-network.v1", "inventor-ego-network.v1", "inventor-technology.v1",
    "inventor-activity.v1", "inventor-cluster-flow.v1", "inventor-similarity.v1",
    "inventor-impact.v1", "inventor-mobility.v1", "inventor-mobility-flow.v1",
)
EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "advanced"


@lru_cache(maxsize=1)
def _exact_renderer_node() -> str | None:
    if sys.platform not in {"win32", "darwin"}:
        return None
    node = shutil.which("node")
    if node is None:
        return None
    try:
        probe = subprocess.run(
            [node, "-p", "process.versions.node + '/' + process.arch"],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return node if probe.returncode == 0 and probe.stdout.strip() == (
        "24.22.1/arm64" if platform.machine().lower() == "arm64" else "24.22.1/x64"
    ) else None


requires_renderer_node = pytest.mark.skipif(
    _exact_renderer_node() is None or ADVANCED_BUILD is None,
    reason="requires a built advanced bundle, Windows x64 or macOS and exact Node24.22.1",
)


def _input(tmp_path: Path, analysis_id: str):
    root = tmp_path / "input"
    root.mkdir()
    if analysis_id.startswith("inventor-") and analysis_id != "inventor-tracking.v1":
        examples = EXAMPLES.parent / "inventor-analysis"
        source = root / "patents.json"
        source.write_bytes((examples / source.name).read_bytes())
        spec_path = root / "spec.json"
        spec_path.write_bytes((examples / f"{analysis_id}.json").read_bytes())
        return root, source, spec_path
    source = root / "patents.csv"
    tracking = analysis_id == "inventor-tracking.v1"
    examples = EXAMPLES.parent / "inventor-tracking" if tracking else EXAMPLES
    source.write_bytes((examples / source.name).read_bytes())
    spec_path = root / "spec.json"
    spec_name = "spec.json" if tracking else f"{analysis_id.removesuffix('.v1')}.json"
    spec_path.write_bytes((examples / spec_name).read_bytes())
    return root, source, spec_path


def _assert_svg(receipt: dict, output: Path) -> bytes:
    assert receipt["ok"] is True
    name = receipt["svg"]
    assert isinstance(name, str) and name == Path(name).name and name.endswith(".svg")
    raw = (output / name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == receipt["svg_sha256"]
    root = ElementTree.fromstring(raw)
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    assert root.attrib["role"] == "img"
    for attribute, tag in (("aria-labelledby", "title"), ("aria-describedby", "desc")):
        node = root.find(f"{{http://www.w3.org/2000/svg}}{tag}")
        assert node is not None and node.text
        assert node.attrib["id"] == root.attrib[attribute]
    for element in root.iter():
        assert element.tag.rsplit("}", 1)[-1] not in {"script", "foreignObject", "iframe", "image"}
        for key, value in element.attrib.items():
            assert not key.rsplit("}", 1)[-1].casefold().startswith("on")
            if key.rsplit("}", 1)[-1] == "href":
                assert value.startswith("#")
    return raw


@pytest.mark.parametrize("analysis_id", ANALYSES)
@requires_renderer_node
@pytest.mark.parametrize("explicit", [False, True])
def test_real_advanced_api_and_cli_render_same_svg_and_reuse(
    analysis_id: str, explicit: bool, tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    from patent_analysis import api, cli
    from patent_analysis.analysis_registry import get_analysis_definition
    from patent_analysis.canonical_v2 import canonical_json_bytes

    input_root, source, spec_path = _input(tmp_path, analysis_id)
    original = source.read_bytes()
    original_spec = spec_path.read_bytes()
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(input_root))
    result = api.run_analysis_csv(source.name, spec_path.read_bytes(), allowed_root=input_root)
    document = canonical_json_bytes(result)
    analysis_path = input_root / "analysis.json"
    analysis_path.write_bytes(document)
    definition = get_analysis_definition(analysis_id)
    assert definition.compatible_render_marks, "approved analysis has no connected render mark"
    mark = definition.compatible_render_marks[0]
    api_output, cli_output = tmp_path / "api-output", tmp_path / "cli-output"
    api_output.mkdir()
    cli_output.mkdir()
    node = _exact_renderer_node()
    assert node is not None
    first = api.render_analysis_svg(
        document, mark=mark, output_directory=api_output, node_executable=node,
    )
    api_svg = _assert_svg(first, api_output)
    assert first["status"] == "created" and first["mark"] == mark
    reused = api.render_analysis_svg(
        document, mark=mark, output_directory=api_output, node_executable=node,
    )
    assert reused == {**first, "status": "reused"}
    assert _assert_svg(reused, api_output) == api_svg
    assert sorted(path.name for path in api_output.iterdir()) == [first["svg"]]
    argv = [
        "render", "--analysis", str(analysis_path), "--output", str(cli_output),
        "--node", node, "--json",
    ]
    if explicit:
        argv.extend(["--mark", mark])
    assert cli.main(argv) == 0
    cli_first = json.loads(capsys.readouterr().out)
    assert cli_first["status"] == "created"
    assert _assert_svg(cli_first, cli_output) == api_svg
    assert cli_first["artifact_id"] == first["artifact_id"]
    assert cli.main(argv) == 0
    cli_second = json.loads(capsys.readouterr().out)
    assert cli_second == {**cli_first, "status": "reused"}
    assert _assert_svg(cli_second, cli_output) == api_svg
    assert sorted(path.name for path in cli_output.iterdir()) == [cli_first["svg"]]
    assert analysis_path.read_bytes() == document and source.read_bytes() == original
    assert spec_path.read_bytes() == original_spec


@pytest.mark.parametrize("analysis_id", ANALYSES)
@requires_renderer_node
def test_real_mcp_advanced_analysis_handle_renders_the_same_public_result(
    analysis_id: str, tmp_path: Path,
) -> None:
    from patent_analysis import api
    from patent_analysis.analysis_registry import get_analysis_definition
    from patent_analysis.canonical_v2 import canonical_json_bytes
    from patent_analysis_mcp.roots import ApprovedRoot, RootRegistry
    from patent_analysis_mcp.tool_handlers import ToolHandlers

    input_root, source, spec_path = _input(tmp_path, analysis_id)
    original_source = source.read_bytes()
    original_spec = spec_path.read_bytes()
    output_root = tmp_path / "output"
    output_root.mkdir()
    direct_output = tmp_path / "direct-output"
    direct_output.mkdir()
    node = _exact_renderer_node()
    assert node is not None
    definition = get_analysis_definition(analysis_id)
    assert definition.mcp_public and definition.compatible_render_marks
    mark = definition.compatible_render_marks[0]
    spec = json.loads(spec_path.read_bytes())
    handlers = ToolHandlers(roots=RootRegistry(
        input_roots=(ApprovedRoot("input", input_root),),
        output_roots=(ApprovedRoot("output", output_root),),
    ), node_executable=node)
    analyzed = handlers.call("patent_analysis.analyze", {
        "input_root_id": "input", "path": source.name, "spec": spec,
    })
    assert analyzed["ok"] is True, analyzed
    handle = analyzed["content"]["render_handle"]
    direct = api.run_analysis_csv(source.name, spec_path.read_bytes(), allowed_root=input_root)
    expected_data = ToolHandlers._without_linkable_provenance(direct["data"])
    assert analyzed["content"]["data"] == expected_data
    rendered = handlers.call("patent_analysis.render", {
        "output_root_id": "output", "output_path": "session",
        "analysis_handle": handle, "mark": mark,
    })
    assert rendered["ok"] is True, rendered
    via_mcp = rendered["content"]
    assert via_mcp["status"] == "created" and via_mcp["mark"] == mark
    via_api = api.render_analysis_svg(canonical_json_bytes(direct), mark=mark,
                                      output_directory=direct_output, node_executable=node)
    assert _assert_svg(via_mcp, output_root / "session") == _assert_svg(via_api, direct_output)
    assert via_mcp["artifact_id"] == via_api["artifact_id"]
    mcp_reused = handlers.call("patent_analysis.render", {
        "output_root_id": "output", "output_path": "session",
        "analysis_handle": handle, "mark": mark,
    })
    assert mcp_reused["ok"] is True, mcp_reused
    assert mcp_reused["content"] == {**via_mcp, "status": "reused"}
    assert _assert_svg(mcp_reused["content"], output_root / "session") == _assert_svg(
        via_api, direct_output,
    )
    assert sorted(path.name for path in (output_root / "session").iterdir()) == [via_mcp["svg"]]
    assert source.read_bytes() == original_source and spec_path.read_bytes() == original_spec
    assert "receipt" not in analyzed["content"]
    assert str(input_root) not in repr(analyzed) and str(output_root) not in repr(rendered)
