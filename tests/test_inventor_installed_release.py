"""Regression coverage for finite installed-release acceptance, not registry-derived IDs."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import sysconfig
from pathlib import Path

import pytest

from patent_analysis import api

ROOT = Path(__file__).resolve().parents[1]


def verifier(name="verify_installed_release"):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("platform", "interpreter_dir", "scripts_dir"),
    (("win32", ".", "Scripts"), ("win32", "Scripts", "Scripts"),
     ("linux", "bin", "bin")),
)
def test_console_resolves_current_interpreter_install_scheme(
    tmp_path, monkeypatch, platform, interpreter_dir, scripts_dir
):
    release = verifier()
    suffix = ".exe" if platform == "win32" else ""
    scripts = tmp_path / scripts_dir
    scripts.mkdir()
    entrypoint = scripts / ("patent-analysis" + suffix)
    entrypoint.write_bytes(b"synthetic entrypoint")
    monkeypatch.setattr(sys, "platform", platform)
    monkeypatch.setattr(sys, "executable", str(tmp_path / interpreter_dir / "python.exe"))
    monkeypatch.setattr(sysconfig, "get_path", lambda name: str(scripts))
    assert release.console("patent-analysis") == str(entrypoint)


def test_legacy_verifier_accepts_native_public_capabilities_without_expanding_golden_cases():
    release = verifier()
    cases = json.loads((ROOT / "examples/analysis-catalog.json").read_text())["cases"]
    check = getattr(release, "verify_capability_inventory", None)
    assert callable(check), "installed verifier needs a finite legacy/native capability check"
    check(api.describe_capabilities(), cases)
    assert len(cases) == 18


def test_sdist_manifest_includes_public_inventor_usage_guide(monkeypatch):
    pytest.importorskip("setuptools")
    from setuptools.command.egg_info import FileList

    monkeypatch.chdir(ROOT)
    manifest = FileList()
    manifest.findall("docs")
    for line in (ROOT / "MANIFEST.in").read_text().splitlines():
        if line.strip():
            manifest.process_template_line(line)
    assert "docs/inventor-analysis.md" in {Path(p).as_posix() for p in manifest.files}


def test_native_installed_verifier_compares_all_ten_real_api_console_results(tmp_path, monkeypatch):
    script = ROOT / "scripts/verify_installed_inventor_release.py"
    assert script.is_file(), "clean native installed-release verifier is missing"
    native = verifier("verify_installed_inventor_release")
    input_root = tmp_path / "input"
    shutil.copytree(ROOT / "examples/inventor-analysis", input_root / "inventor-analysis")
    output_root = tmp_path / "output"
    output_root.mkdir()
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(input_root))
    report = native.verify_native(input_root, output_root, render_svg=False)
    assert report["analysis_ids"] == list(verifier().INVENTOR_IDS)
    assert len(report["results"]) == 10
    assert all(
        r["api_cli_canonical_equal"] and r["table_equal"] for r in report["results"].values()
    )
    assert report["svg"] == {}


@pytest.mark.skipif(sys.platform != "win32", reason="native SVG gate is Windows-only")
def test_native_verifier_requires_nine_api_console_default_explicit_svg_paths(
    tmp_path, monkeypatch
):
    native = verifier("verify_installed_inventor_release")
    input_root = tmp_path / "input"
    shutil.copytree(ROOT / "examples/inventor-analysis", input_root / "inventor-analysis")
    output_root = tmp_path / "output"
    output_root.mkdir()
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(input_root))
    report = native.verify_native(input_root, output_root, render_svg=True)
    assert set(report["svg"]) == set(verifier().INVENTOR_IDS[:-1])
    assert all(r["api_cli_receipts_equal"] and r["reused"] for r in report["svg"].values())
    assert all(Path(r["svg_path"]).is_file() for r in report["svg"].values())


def test_distribution_inventory_includes_untracked_native_sources(tmp_path):
    release = verifier()
    collect = getattr(release, "release_source_files", None)
    assert callable(collect), "wheel acceptance must inventory disk, not git ls-files"
    native = ROOT / "src/patent_analysis/analyses/inventor_network.py"
    assert native in collect(ROOT)
    source = tmp_path / "src/patent_analysis/new_untracked.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n")
    metadata = tmp_path / "src/patent_analysis_cli.egg-info/SOURCES.txt"
    metadata.parent.mkdir()
    metadata.write_text("not a packaged source\n")
    assert collect(tmp_path) == [source]


def test_native_evidence_acceptance_reinputs_candidate_review_via_real_console(
    tmp_path, monkeypatch
):
    native = verifier("verify_installed_inventor_release")
    check = getattr(native, "verify_review_roundtrip", None)
    assert callable(check), "M10 needs a real candidate-key review re-input check"
    shutil.copytree(ROOT / "examples/inventor-analysis", tmp_path / "inventor-analysis")
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))
    report = check(tmp_path)
    assert report["employment_status"] == "user_asserted"
    assert report["review_id"] == "installed-synthetic-review"
    assert report["api_cli_canonical_equal"] and report["table_contains_review"]


def test_native_mcp_acceptance_uses_real_stdio_for_all_ten_analyses(tmp_path, monkeypatch):
    import anyio

    native = verifier("verify_installed_inventor_release")
    check = getattr(native, "verify_native_mcp", None)
    assert callable(check), "native wheel acceptance needs actual MCP stdio"
    input_root = tmp_path / "input"
    shutil.copytree(ROOT / "examples/inventor-analysis", input_root / "inventor-analysis")
    output_root = tmp_path / "output"
    output_root.mkdir()
    monkeypatch.chdir(tmp_path)
    report = anyio.run(check, input_root, output_root, False)
    assert report["transport"] == "stdio"
    assert report["analysis_ids"] == list(verifier().INVENTOR_IDS)
    assert report["public_api_equal"] is True
    assert report["m10_has_no_render_handle"] is True


@pytest.mark.skipif(sys.platform != "win32", reason="native SVG gate is Windows-only")
def test_native_mcp_svg_acceptance_compares_real_stdio_receipts(tmp_path, monkeypatch):
    import anyio
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    native = verifier("verify_installed_inventor_release")
    check = getattr(native, "verify_native_mcp_svg", None)
    assert callable(check), "each of nine actual stdio render handles must match installed API"
    input_root = tmp_path / "input"
    shutil.copytree(ROOT / "examples/inventor-analysis", input_root / "inventor-analysis")
    output_root = tmp_path / "output"
    output_root.mkdir()
    monkeypatch.chdir(tmp_path)

    async def execute():
        params = StdioServerParameters(
            command=native.release.console("patent-analysis-mcp"),
            args=["--input-root", f"input={input_root}", "--output-root", f"output={output_root}"],
            cwd=tmp_path,
        )
        async with stdio_client(params) as streams:
            async with ClientSession(*streams, read_timeout_seconds=45) as session:
                await session.initialize()
                for aid in native.INVENTOR_IDS[:-1]:
                    spec = (input_root / "inventor-analysis" / f"{aid}.json").read_bytes()
                    direct = api.run_analysis(native.SOURCE, spec, allowed_root=input_root)
                    reply = await session.call_tool(
                        "patent_analysis.analyze",
                        {
                            "input_root_id": "input",
                            "path": native.SOURCE,
                            "spec": json.loads(spec),
                        },
                    )
                    assert not reply.is_error
                    report = await check(
                        session, reply.structured_content["content"], direct, aid, output_root
                    )
                    assert report["mcp_api_receipts_equal"] and report["reused"]
                    assert Path(report["svg_path"]).is_file()

    anyio.run(execute)


@pytest.mark.parametrize(
    "name",
    (
        "inventor-network",
        "inventor-ego-network",
        "inventor-technology",
        "inventor-activity",
        "inventor-similarity",
        "inventor-impact",
        "inventor-mobility-flow",
    ),
)
def test_mcp_public_schema_preserves_large_finite_bound_without_relaxing_results(tmp_path, name):
    from patent_analysis_mcp.contracts import McpContractError, success_envelope
    from patent_analysis_mcp.roots import ApprovedRoot, RootRegistry
    from patent_analysis_mcp.tool_handlers import ToolHandlers

    schema_name = f"{name}-result-v1.schema.json"
    expected = api.get_public_schema(schema_name)
    maximum = expected["$defs"]["exact"]["properties"]["value"]["maximum"]
    assert maximum > 9007199254740991
    (tmp_path / "input").mkdir()
    (tmp_path / "output").mkdir()
    handlers = ToolHandlers(
        roots=RootRegistry(
            input_roots=(ApprovedRoot("input", tmp_path / "input"),),
            output_roots=(ApprovedRoot("output", tmp_path / "output"),),
        )
    )
    reply = handlers.call("patent_analysis.schema", {"schema_name": schema_name})
    assert reply["ok"] is True, reply
    assert reply["content"]["schema"] == expected
    with pytest.raises(McpContractError):
        success_envelope({"ordinary_analysis_value": maximum})


@pytest.mark.parametrize(
    "schema",
    (
        {"maximum": float("nan")},
        {"maximum": float("inf")},
        {"maximum": float("-inf")},
        {"properties": {"secrets": {"type": "string"}}},
        {"description": "\ud800"},
    ),
)
def test_schema_response_exception_retains_finite_and_private_key_guards(schema):
    from patent_analysis_mcp.contracts import McpContractError, schema_success_envelope

    with pytest.raises(McpContractError) as caught:
        schema_success_envelope({"schema_name": "test.schema.json", "schema": schema})
    assert caught.value.code == "internal.failed"


def test_schema_response_exception_retains_closed_size_depth_and_cycle_guards():
    from patent_analysis_mcp.contracts import McpContractError, schema_success_envelope

    payload = {"schema_name": "test.schema.json", "schema": {"maximum": 3.402823669209385e38}}
    with pytest.raises(McpContractError) as caught:
        schema_success_envelope(payload, maximum_bytes=10)
    assert caught.value.code == "response.too_large"
    with pytest.raises(McpContractError):
        schema_success_envelope({**payload, "extra": True})
    nested = {}
    cursor = nested
    for _ in range(70):
        cursor["nested"] = {}
        cursor = cursor["nested"]
    with pytest.raises(McpContractError):
        schema_success_envelope({"schema_name": "test.schema.json", "schema": nested})
    cyclic = {}
    cyclic["self"] = cyclic
    with pytest.raises(McpContractError):
        schema_success_envelope({"schema_name": "test.schema.json", "schema": cyclic})
