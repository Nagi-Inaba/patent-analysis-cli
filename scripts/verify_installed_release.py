"""Verify the built distribution outside the checkout; do not rerun pytest.

Run with a fresh venv's Python -I. Examples are synthetic, copied to a separate
input root; the runtime imports must resolve inside that venv, never src/.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata as metadata
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from io import StringIO
from pathlib import Path
from xml.etree import ElementTree

SVG_CASES = frozenset({
    "ranking.v1", "matrix.v1", "timeline.v1", "composition.v1", "collaboration-network.v1",
    "inventor-tracking.v1",
})
MCP_SVG_CASES = frozenset({
    "ranking.v1", "matrix.v1", "timeline.v1", "composition.v1", "collaboration-network.v1",
    "inventor-tracking.v1",
})
MCP_TOOLS = {
    "patent_analysis.capabilities",
    "patent_analysis.schema",
    "patent_analysis.inspect",
    "patent_analysis.validate_spec",
    "patent_analysis.analyze",
    "patent_analysis.render",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(root: Path, relative: str) -> Path:
    path = (root / relative).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("example path must stay inside its input root")
    return path


def console(name: str) -> str:
    suffix = ".exe" if sys.platform == "win32" else ""
    path = Path(sys.executable).parent / (name + suffix)
    if not path.is_file():
        raise RuntimeError(f"installed console script missing: {name}")
    return str(path)


def run_json(*args: str, expected_code: int = 0) -> dict:
    done = subprocess.run(
        [console("patent-analysis"), *args],
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert done.returncode == expected_code, (args, done.stdout, done.stderr)
    return json.loads(done.stdout)


def installed_package() -> dict:
    import patent_analysis

    assert sys.prefix != sys.base_prefix, "Use a fresh venv, not the development interpreter"
    assert Path(patent_analysis.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
    distribution = metadata.distribution("patent-analysis-cli")
    direct_url = distribution.read_text("direct_url.json")
    assert direct_url and not json.loads(direct_url).get("dir_info", {}).get("editable")
    assert distribution.metadata["Description-Content-Type"] == "text/markdown"
    assert (
        distribution.metadata["License-Expression"]
        == "Apache-2.0 AND MIT AND BSD-3-Clause AND 0BSD"
    )
    assert "Private :: Do Not Upload" not in distribution.metadata.get_all("Classifier", [])
    license_files = {
        str(path).replace("\\", "/"): path
        for path in distribution.files or ()
        if ".dist-info/licenses/" in str(path).replace("\\", "/")
    }
    project_license = next(
        path for name, path in license_files.items() if name.endswith("/licenses/LICENSE")
    )
    third_party_notices = next(
        path
        for name, path in license_files.items()
        if name.endswith("/licenses/src/patent_analysis/renderer/THIRD_PARTY_NOTICES.txt")
    )
    assert "Apache License" in Path(
        distribution.locate_file(project_license)
    ).read_text(encoding="utf-8")
    assert "THIRD-PARTY NOTICES" in Path(
        distribution.locate_file(third_party_notices)
    ).read_text(encoding="utf-8")
    requires_python = distribution.metadata["Requires-Python"]
    assert requires_python and {part.strip() for part in requires_python.split(",")} == {
        ">=3.14", "<3.15"
    }, "Package Python range must match the fixed Unicode runtime"
    assert "mcp" in distribution.metadata.get_all("Provides-Extra", [])
    forbidden = {"patent-analysis-workbench", "bubble-matrix-map", "matrix-map-desktop"}
    requirements = distribution.requires or []
    assert not any(name in req.lower() for name in forbidden for req in requirements)
    paths = [str(path).replace("\\", "/") for path in distribution.files or []]
    assert "patent_analysis/normalization/family.py" in paths
    assert "patent_analysis_mcp/server.py" in paths
    assert not any(
        path.startswith(("tests/", "node_modules/")) for path in paths
    )
    resources = {
        path: digest(Path(distribution.locate_file(path)))
        for path in paths
        if path.startswith(("patent_analysis/schemas/", "patent_analysis/renderer/"))
        and path.endswith((".json", ".js", ".gz", ".txt"))
    }
    assert "patent_analysis/renderer/advanced-renderer.bundle.js.gz" in resources
    assert "patent_analysis/renderer/THIRD_PARTY_NOTICES.txt" in resources
    return {
        "package_version": distribution.version,
        "requires_python": requires_python,
        "requires_dist": requirements,
        "resources_sha256": resources,
    }


def render_cli(result: dict, mark: str, output: Path, input_root: Path) -> dict:
    document = input_root / "verification-result.json"
    document.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    args = (
        "render",
        "--analysis",
        document.name,
        "--mark",
        mark,
        "--output",
        str(output),
        "--json",
    )
    first = run_json(*args)
    svg = fixture(output, first["svg"])
    verify_svg_accessibility(svg)
    before = digest(svg)
    second = run_json(*args)
    assert first["status"] == "created" and second["status"] == "reused"
    assert first["svg"] == second["svg"] and digest(svg) == before
    return {"mark": mark, "svg_sha256": before, "receipt": second}


def verify_svg_accessibility(path: Path) -> None:
    root = ElementTree.fromstring(path.read_bytes())
    assert root.attrib["role"] == "img"
    for attribute, tag in (("aria-labelledby", "title"), ("aria-describedby", "desc")):
        node = root.find(f"{{http://www.w3.org/2000/svg}}{tag}")
        assert node is not None and node.text and node.attrib["id"] == root.attrib[attribute]


def verify_core(cases: list[dict], expected: dict, input_root: Path, output_root: Path) -> dict:
    assert importlib.util.find_spec("mcp") is None, "Core install unexpectedly includes MCP"
    caps = run_json("capabilities", "--json")
    assert {a["analysis_id"] for a in caps["analyses"]} == {c["analysis_id"] for c in cases}
    inspection = run_json("inspect", cases[0]["csv"], "--json")
    assert inspection.get("ok") is not False
    validation = run_json("validate-spec", "basic/ranking.json", "--json")
    assert validation["analysis_id"] == "ranking.v1" and validation["valid"]
    assert run_json("schema", "analysis-spec.schema.json", "--json")["schema"]["type"] == "object"
    table = subprocess.run(
        [console("patent-analysis"), "analyze", cases[0]["csv"], "--spec", "basic/ranking.json",
         "--format", "csv"],
        env={**os.environ, "PYTHONUTF8": "0"}, capture_output=True, check=True, timeout=30,
    )
    assert not table.stderr
    table_rows = list(csv.DictReader(StringIO(table.stdout.decode("utf-8"))))
    assert [row["label"] for row in table_rows] == [
        row["label"] for row in expected["ranking.v1"]["rows"]
    ]
    context = subprocess.run(
        [console("patent-analysis"), "analyze", cases[0]["csv"], "--spec", "basic/ranking.json",
         "--format", "csv", "--include-context"],
        env={**os.environ, "PYTHONUTF8": "0"}, capture_output=True, check=True, timeout=30,
    )
    assert not context.stderr
    pointers = {json.loads(row["context_path"]): json.loads(row["context_value"])
                for row in csv.DictReader(StringIO(context.stdout.decode("utf-8")))
                if row["table"] == "context"}
    assert "/analysis/receipt" in pointers and "/spec" in pointers
    rendered = {}
    for case in cases:
        aid = case["analysis_id"]
        result = run_json("analyze", case["csv"], "--spec", case["spec"], "--json")
        aggregate = result["result" if aid == "ranking.v1" else "data"]
        assert aggregate == expected[aid], f"aggregate mismatch: {aid}"
        if sys.platform == "win32" and aid in SVG_CASES:
            target = output_root / aid
            target.mkdir()
            rendered[aid] = render_cli(result, case["mark"], target, input_root)
    family = run_json(
        "analyze", "family/patents.csv", "--spec", "family/composition.json", "--json"
    )
    assert family["family_selection"]["representative_rows"] == 4
    assert family["family_selection"]["collapsed_rows"] == 1
    assert importlib.util.find_spec("mcp") is None
    return {
        "analysis_ids": [c["analysis_id"] for c in cases],
        "family_example": "passed",
        "svg": rendered,
        "svg_platform_supported": sys.platform == "win32",
    }


async def verify_mcp(
    cases: list[dict], expected: dict, input_root: Path, output_root: Path
) -> dict:
    import anyio
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    args = ["--input-root", f"input={input_root}", "--output-root", f"output={output_root}"]
    params = StdioServerParameters(
        command=console("patent-analysis-mcp"), args=args, cwd=Path.cwd()
    )
    public = {c["analysis_id"] for c in cases if c["mcp"]}
    rendered = {}
    with anyio.fail_after(120):
        async with stdio_client(params) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                assert {t.name for t in (await session.list_tools()).tools} == MCP_TOOLS
                caps = await session.call_tool("patent_analysis.capabilities", {})
                assert not caps.is_error
                assert {
                    a["analysis_id"] for a in caps.structured_content["content"]["analyses"]
                } == public
                unknown = await session.call_tool(
                    "patent_analysis.validate_spec",
                    {"spec": {"analysis_contract_version": "2.0.0", "analysis_id": "future.v1"}},
                )
                assert unknown.is_error
                for case in cases:
                    aid = case["analysis_id"]
                    spec = json.loads(fixture(input_root, case["spec"]).read_text(encoding="utf-8"))
                    reply = await session.call_tool(
                        "patent_analysis.analyze",
                        {
                            "input_root_id": "input",
                            "path": case["csv"],
                            "spec": spec,
                        },
                    )
                    assert aid in public
                    assert not reply.is_error, reply
                    content = reply.structured_content["content"]
                    assert content["result" if aid == "ranking.v1" else "data"] == expected[aid], (
                        aid
                    )
                    assert str(input_root) not in repr(content) and "receipt" not in content
                    if sys.platform == "win32" and aid in MCP_SVG_CASES:
                        (output_root / aid).mkdir()
                        request = {
                            "output_root_id": "output",
                            "output_path": aid,
                            "analysis_handle": content["render_handle"],
                            "mark": case["mark"],
                        }
                        first = await session.call_tool("patent_analysis.render", request)
                        assert not first.is_error, first
                        receipt = first.structured_content["content"]
                        svg = fixture(output_root / aid, receipt["svg"])
                        verify_svg_accessibility(svg)
                        before = digest(svg)
                        second = await session.call_tool("patent_analysis.render", request)
                        assert not second.is_error, second
                        again = second.structured_content["content"]
                        assert receipt["status"] == "created" and again["status"] == "reused"
                        assert receipt["svg"] == again["svg"] and digest(svg) == before
                        rendered[aid] = {"svg_sha256": before, "receipt": again}
    return {
        "analysis_ids": sorted(public),
        "svg": rendered,
        "svg_platform_supported": sys.platform == "win32",
        "mcp_version": metadata.version("mcp"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--examples", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--mcp", action="store_true")
    args = parser.parse_args()
    if not sys.flags.isolated:
        parser.error("run this script using the fresh venv's python -I")
    report = {"mode": "mcp" if args.mcp else "core", "python": sys.version, **installed_package()}
    source_examples = args.examples.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="patent-release-") as work:
        work = Path(work).resolve()
        input_root, output_root = work / "input", work / "output"
        shutil.copytree(source_examples, input_root)
        output_root.mkdir()
        cases = json.loads((input_root / "analysis-catalog.json").read_text(encoding="utf-8"))[
            "cases"
        ]
        expected = json.loads((input_root / "expected-aggregates.json").read_text(encoding="utf-8"))
        assert {c["analysis_id"] for c in cases} == set(expected) and len(cases) == len(expected)
        before = {
            str(p.relative_to(input_root)): digest(p) for p in input_root.rglob("*") if p.is_file()
        }
        for case in cases:
            for kind in ("csv", "spec"):
                assert digest(fixture(input_root, case[kind])) == case[f"{kind}_sha256"]
        old_cwd = Path.cwd()
        try:
            os.chdir(work)
            os.environ.pop("PYTHONPATH", None)
            os.environ.pop("PYTHONHOME", None)
            os.environ["PATENT_ANALYSIS_ALLOWED_ROOT"] = str(input_root)
            if args.mcp:
                import anyio

                report.update(anyio.run(verify_mcp, cases, expected, input_root, output_root))
            else:
                report.update(verify_core(cases, expected, input_root, output_root))
            assert all(digest(input_root / p) == value for p, value in before.items())
        finally:
            os.chdir(old_cwd)
    report["fixture_sha256"] = before
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "mode": report["mode"],
                "analyses": len(report["analysis_ids"]),
                "svg_reuse_checks": len(report["svg"]),
                "input_unchanged": True,
            }
        )
    )


if __name__ == "__main__":
    main()
