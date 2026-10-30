"""Execute native inventor acceptance with a non-editable wheel's Python -I.

Synthetic examples are copied outside the checkout. Expected numeric results
come from the installed API, independently compared with console and MCP stdio;
finite schema, population and statistic-count assertions are not registry-derived.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as metadata
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.etree import ElementTree

# -I deliberately excludes the checkout and script directory from sys.path.
# Load only the adjacent verification helper, never add repository src to sys.path.
_HELPER = importlib.util.spec_from_file_location(
    "release_verification_helpers", Path(__file__).with_name("verify_installed_release.py")
)
assert _HELPER is not None and _HELPER.loader is not None
release = importlib.util.module_from_spec(_HELPER)
_HELPER.loader.exec_module(release)
INVENTOR_IDS = release.INVENTOR_IDS
INVENTOR_MARKS = (
    "inventor-network-svg.v1",
    "inventor-ego-network-svg.v1",
    "inventor-technology-svg.v1",
    "inventor-activity-svg.v1",
    "inventor-cluster-flow-svg.v1",
    "inventor-similarity-svg.v1",
    "inventor-impact-svg.v1",
    "inventor-mobility-svg.v1",
    "inventor-mobility-flow-svg.v1",
)
STATISTIC_COUNTS = {
    "inventor-network.v1": {"nodes": 4, "edges": 2, "communities": 2},
    "inventor-ego-network.v1": {"nodes": 3, "edges": 2, "partners": 2},
    "inventor-technology.v1": {"profiles": 4, "cells": 4, "classifications": 2},
    "inventor-activity.v1": {"people": 4, "calendar": 2, "observations": 5},
    "inventor-cluster-flow.v1": {"nodes": 5, "links": 4, "unplottable": 1},
    "inventor-similarity.v1": {"features": 4, "similarities": 10, "classifications": 2},
    "inventor-impact.v1": {"people": 4, "units": 4, "unplottable": 4},
    "inventor-mobility.v1": {"associations": 7, "episodes": 6, "candidates": 2},
    "inventor-mobility-flow.v1": {"associations": 7, "candidates": 2, "flows": 2},
    "inventor-mobility-evidence.v1": {"associations": 7, "episodes": 6, "candidates": 2},
}
SOURCE = "inventor-analysis/patents.json"


def canonical(document: dict) -> bytes:
    from patent_analysis.canonical_v2 import canonical_json_bytes

    return canonical_json_bytes(document)


def check_result(result: dict, aid: str) -> None:
    from jsonschema import Draft202012Validator

    from patent_analysis import api

    assert result["analysis_id"] == aid
    assert result["population"] == {"input_rows": 4, "analyzed_rows": 4, "excluded_rows": 0}
    data = result["data"]
    assert data["schema_version"] == data["algorithm_version"] == "1.0.0"
    schema_name = aid.removesuffix(".v1") + "-result-v1.schema.json"
    Draft202012Validator(api.get_public_schema(schema_name)).validate(data)
    assert data["provenance"]["sidecar_state"] == "input_not_provided"
    assert data["provenance"]["sidecars"] == []
    assert data["family_basis"] == {"family_mode": "records", "unit": "records"}
    assert data["input_coverage"]["missing_date"] == 1
    assert len(data["identity_evidence"]) == 4
    for table, count in STATISTIC_COUNTS[aid].items():
        assert len(data["statistics"][table]) == count, (aid, table)
    assert result["warnings"], "employment caveat must remain visible"


def console_bytes(*args: str) -> bytes:
    done = subprocess.run(
        [release.console("patent-analysis"), *args],
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert done.returncode == 0 and not done.stderr, (args, done.stdout, done.stderr)
    return done.stdout


def exact_renderer_node() -> str:
    from patent_analysis.local_renderer import require_supported_platform

    require_supported_platform()
    node = shutil.which("node")
    assert node is not None, "Node is required for installed SVG acceptance"
    probe = subprocess.run(
        [node, "-p", "process.versions.node + '/' + process.arch"],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    assert probe.stdout.strip() in (
        {"24.22.1/x64", "24.22.1/arm64"} if sys.platform == "darwin" else {"24.22.1/x64"}
    )
    return node


def check_svg(receipt: dict, output: Path) -> bytes:
    assert receipt["ok"] is True
    name = receipt["svg"]
    assert name == Path(name).name and name.endswith(".svg")
    path = release.fixture(output, name)
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == receipt["svg_sha256"]
    release.verify_svg_accessibility(path)
    root = ElementTree.fromstring(raw)
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    for element in root.iter():
        assert element.tag.rsplit("}", 1)[-1] not in {"script", "foreignObject", "iframe", "image"}
        for key, value in element.attrib.items():
            local = key.rsplit("}", 1)[-1].casefold()
            assert not local.startswith("on")
            if local == "href":
                assert value.startswith("#")
    assert sorted(p.name for p in output.iterdir()) == [name]
    return raw


def verify_native_svg(result: dict, mark: str, input_root: Path, output_root: Path) -> dict:
    from patent_analysis import api

    node = exact_renderer_node()
    document = canonical(result)
    analysis_path = input_root / "verification-result.json"
    analysis_path.write_bytes(document)
    api_output = output_root / "api"
    api_output.mkdir(parents=True)
    first = api.render_analysis_svg(
        document, mark=mark, output_directory=api_output, node_executable=node
    )
    svg = check_svg(first, api_output)
    assert first["status"] == "created" and first["mark"] == mark
    again = api.render_analysis_svg(
        document, mark=mark, output_directory=api_output, node_executable=node
    )
    assert again == {**first, "status": "reused"}
    assert check_svg(again, api_output) == svg
    for explicit in (False, True):
        output = output_root / ("cli-explicit" if explicit else "cli-default")
        output.mkdir()
        args = [
            "render",
            "--analysis",
            analysis_path.name,
            "--output",
            str(output),
            "--node",
            node,
            "--json",
        ]
        if explicit:
            args.extend(["--mark", mark])
        created = json.loads(console_bytes(*args))
        assert canonical(created) == canonical(first)
        assert check_svg(created, output) == svg
        reused = json.loads(console_bytes(*args))
        assert canonical(reused) == canonical(again)
        assert check_svg(reused, output) == svg
    assert analysis_path.read_bytes() == document
    return {
        "receipt": again,
        "svg_sha256": first["svg_sha256"],
        "svg_path": str(api_output / first["svg"]),
        "api_cli_receipts_equal": True,
        "reused": True,
        "cli_modes": ["default", "explicit"],
        "accessibility": "passed",
    }


def verify_native(input_root: Path, output_root: Path, *, render_svg: bool) -> dict:
    from patent_analysis import api

    caps = api.describe_capabilities()
    release.verify_capability_inventory(caps, [{"analysis_id": a} for a in release.CATALOG_IDS])
    native_caps = {
        c["analysis_id"]: c for c in caps["analyses"] if c["analysis_id"] in INVENTOR_IDS
    }
    for index, aid in enumerate(INVENTOR_IDS):
        assert native_caps[aid]["render_marks"] == (
            [INVENTOR_MARKS[index]] if index < len(INVENTOR_MARKS) else []
        )
    results, rendered = {}, {}
    for aid in INVENTOR_IDS:
        spec_path = f"inventor-analysis/{aid}.json"
        spec_bytes = release.fixture(input_root, spec_path).read_bytes()
        assert api.validate_analysis_spec_bytes(spec_bytes)["analysis_id"] == aid
        result = api.run_analysis(SOURCE, spec_bytes, allowed_root=input_root)
        check_result(result, aid)
        cli = json.loads(console_bytes("analyze", SOURCE, "--spec", spec_path, "--json"))
        assert canonical(result) == canonical(cli), aid
        table = console_bytes("analyze", SOURCE, "--spec", spec_path, "--format", "csv")
        api_table = api.run_analysis_table(SOURCE, spec_bytes, allowed_root=input_root)
        assert table == api_table.encode("utf-8"), aid
        assert table.startswith(b"analysis_id,table,") and aid.encode() in table
        text = console_bytes("analyze", SOURCE, "--spec", spec_path, "--format", "text")
        assert text == api.run_analysis_table(
            SOURCE, spec_bytes, allowed_root=input_root, table_format="text"
        ).encode("utf-8"), aid
        results[aid] = {
            "api_cli_canonical_equal": True,
            "result_sha256": hashlib.sha256(canonical(result)).hexdigest(),
            "table_equal": True,
            "csv_sha256": hashlib.sha256(table).hexdigest(),
            "text_sha256": hashlib.sha256(text).hexdigest(),
            "population": result["population"],
            "statistic_counts": STATISTIC_COUNTS[aid],
        }
        if render_svg and aid != "inventor-mobility-evidence.v1":
            mark = INVENTOR_MARKS[INVENTOR_IDS.index(aid)]
            rendered[aid] = verify_native_svg(result, mark, input_root, output_root / aid)
    return {
        "analysis_ids": list(INVENTOR_IDS),
        "results": results,
        "svg": rendered,
        "svg_platform_supported": sys.platform in {"win32", "darwin"},
    }


def verify_review_roundtrip(input_root: Path) -> dict:
    """Re-input an actual M10 candidate key; user assertion is not confirmed employment."""
    import csv
    from io import StringIO

    from jsonschema import Draft202012Validator

    from patent_analysis import api

    aid = "inventor-mobility-evidence.v1"
    spec = json.loads(release.fixture(input_root, f"inventor-analysis/{aid}.json").read_bytes())
    baseline = api.run_analysis(SOURCE, canonical(spec), allowed_root=input_root)
    candidate = baseline["data"]["statistics"]["candidates"][0]
    assert candidate["canonical_inventor_id"] == "SAMPLE-B"
    cid, rid = candidate["candidate_id"], "installed-synthetic-review"
    tables = {
        name: []
        for name in (
            "sources",
            "identities",
            "entities",
            "entity_aliases",
            "groups",
            "events",
            "personal_evidence",
            "reviews",
            "citations",
        )
    }
    tables["sources"] = [
        {
            "source_id": "installed-synthetic-source",
            "kind": "local_document",
            "citation": "Synthetic installed-release acceptance only",
            "checked_date": "2025-01-01",
            "url": None,
        }
    ]
    tables["entities"] = [
        {"entity_id": entity, "display_name": entity, "source_ids": ["installed-synthetic-source"]}
        for entity in ("SAMPLE-ORG-1", "SAMPLE-ORG-2")
    ]
    tables["reviews"] = [
        {
            "review_id": rid,
            "inventor_id": "SAMPLE-B",
            "claim": "employment_move",
            "status": "accepted",
            "reason": "Synthetic user assessment, not employment evidence",
            "reviewed_date": "2025-01-01",
            "evidence_ids": [],
            "event_ids": [],
            "record_ids": [],
            "source_ids": ["installed-synthetic-source"],
            "supersedes_review_id": None,
        }
    ]
    sidecar = {"version": "1.0.0", "tables": tables}
    Draft202012Validator(api.get_public_schema("inventor-sidecar-v1.schema.json")).validate(sidecar)
    (input_root / "verification-review.json").write_bytes(canonical(sidecar))
    spec["parameters"] = {
        "auxiliary": {"format": "json", "path": "verification-review.json"},
        "review_bindings": {cid: [rid]},
    }
    spec_path = input_root / "verification-reviewed-spec.json"
    spec_path.write_bytes(canonical(spec))
    actual = api.run_analysis(SOURCE, canonical(spec), allowed_root=input_root)
    Draft202012Validator(
        api.get_public_schema("inventor-mobility-evidence-result-v1.schema.json")
    ).validate(actual["data"])
    reviewed = next(
        c for c in actual["data"]["statistics"]["candidates"] if c["candidate_id"] == cid
    )
    assert reviewed["employment_status"] == "user_asserted"
    assert reviewed["corporate_status"] == "unknown"
    assert reviewed["reviews"][0]["review_id"] == rid and reviewed["reviews"][0]["active"]
    cli = json.loads(console_bytes("analyze", SOURCE, "--spec", spec_path.name, "--json"))
    assert canonical(cli) == canonical(actual)
    raw = console_bytes("analyze", SOURCE, "--spec", spec_path.name, "--format", "csv")
    assert raw == api.run_analysis_table(SOURCE, canonical(spec), allowed_root=input_root).encode()
    rows = [r for r in csv.DictReader(StringIO(raw.decode())) if r["table"] == "candidates"]
    row = next(r for r in rows if r["candidate_id"] == cid)
    assert row["employment_status"] == "user_asserted"
    assert json.loads(row["reviews"])[0]["review_id"] == rid
    return {
        "candidate_id": cid,
        "review_id": rid,
        "employment_status": "user_asserted",
        "api_cli_canonical_equal": True,
        "table_contains_review": True,
        "result_sha256": hashlib.sha256(canonical(actual)).hexdigest(),
    }


def assert_installed_imports() -> dict:
    paths = {}
    for name, module in tuple(sys.modules.items()):
        if name == "patent_analysis" or name.startswith(
            ("patent_analysis.", "patent_analysis_mcp")
        ):
            path = getattr(module, "__file__", None)
            if path:
                resolved = Path(path).resolve()
                assert resolved.is_relative_to(Path(sys.prefix).resolve()), (name, path)
                paths[name] = str(resolved)
    return paths


def public_document(value):
    """Independent expectation for the documented public MCP privacy boundary."""
    if isinstance(value, dict):
        return {
            k: public_document(v)
            for k, v in value.items()
            if k != "receipt" and not k.casefold().endswith("sha256")
        }
    if isinstance(value, list):
        return [public_document(item) for item in value]
    return value


async def verify_native_mcp_svg(
    session, content: dict, direct: dict, aid: str, output_root: Path
) -> dict:
    from patent_analysis import api

    node = exact_renderer_node()
    mark = INVENTOR_MARKS[INVENTOR_IDS.index(aid)]
    output_path = f"mcp/{aid}"
    output = output_root / output_path
    output.mkdir(parents=True)
    request = {
        "output_root_id": "output",
        "output_path": output_path,
        "analysis_handle": content["render_handle"],
        "mark": mark,
    }
    reply = await session.call_tool("patent_analysis.render", request)
    assert not reply.is_error, reply
    created = reply.structured_content["content"]
    assert created["status"] == "created"
    svg = check_svg(created, output)
    api_output = output_root / "mcp-api-reference" / aid
    api_output.mkdir(parents=True)
    api_created = api.render_analysis_svg(
        canonical(direct), mark=mark, output_directory=api_output, node_executable=node
    )
    assert canonical(created) == canonical(api_created), aid
    assert check_svg(api_created, api_output) == svg
    reply = await session.call_tool("patent_analysis.render", request)
    assert not reply.is_error, reply
    reused = reply.structured_content["content"]
    assert reused == {**created, "status": "reused"}
    assert check_svg(reused, output) == svg
    api_reused = api.render_analysis_svg(
        canonical(direct), mark=mark, output_directory=api_output, node_executable=node
    )
    assert canonical(reused) == canonical(api_reused), aid
    assert check_svg(api_reused, api_output) == svg
    return {
        "receipt": reused,
        "svg_sha256": created["svg_sha256"],
        "svg_path": str(output / created["svg"]),
        "mcp_api_receipts_equal": True,
        "reused": True,
        "accessibility": "passed",
    }


async def verify_native_mcp(input_root: Path, output_root: Path, render_svg: bool) -> dict:
    import anyio
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    from patent_analysis import api

    params = StdioServerParameters(
        command=release.console("patent-analysis-mcp"),
        args=["--input-root", f"input={input_root}", "--output-root", f"output={output_root}"],
        cwd=Path.cwd(),
        env={key: os.environ[key] for key in ("TMPDIR", "TEMP", "TMP") if key in os.environ},
    )
    rendered, results = {}, {}
    with anyio.fail_after(240):
        async with stdio_client(params) as streams:
            async with ClientSession(*streams, read_timeout_seconds=45) as session:
                await session.initialize()
                assert {t.name for t in (await session.list_tools()).tools} == release.MCP_TOOLS
                caps = await session.call_tool("patent_analysis.capabilities", {})
                assert not caps.is_error
                release.verify_capability_inventory(
                    caps.structured_content["content"],
                    [{"analysis_id": aid} for aid in release.CATALOG_IDS],
                )
                m10 = next(
                    c
                    for c in caps.structured_content["content"]["analyses"]
                    if c["analysis_id"] == "inventor-mobility-evidence.v1"
                )
                assert m10["render_marks"] == []
                for aid in INVENTOR_IDS:
                    spec = json.loads(
                        release.fixture(input_root, f"inventor-analysis/{aid}.json").read_bytes()
                    )
                    validation = await session.call_tool(
                        "patent_analysis.validate_spec", {"spec": spec}
                    )
                    assert not validation.is_error
                    assert validation.structured_content["content"]["analysis_id"] == aid
                    schema_name = aid.removesuffix(".v1") + "-result-v1.schema.json"
                    schema = await session.call_tool(
                        "patent_analysis.schema", {"schema_name": schema_name}
                    )
                    assert not schema.is_error, (aid, schema)
                    assert schema.structured_content["content"]["schema"] == api.get_public_schema(
                        schema_name
                    )
                    direct = api.run_analysis(SOURCE, canonical(spec), allowed_root=input_root)
                    check_result(direct, aid)
                    reply = await session.call_tool(
                        "patent_analysis.analyze",
                        {
                            "input_root_id": "input",
                            "path": SOURCE,
                            "spec": spec,
                        },
                    )
                    assert not reply.is_error, reply
                    content = reply.structured_content["content"]
                    projected = {k: v for k, v in content.items() if k != "render_handle"}
                    assert canonical(projected) == canonical(public_document(direct)), aid
                    assert str(input_root) not in repr(content) and "receipt" not in content
                    results[aid] = hashlib.sha256(canonical(direct)).hexdigest()
                    if aid == "inventor-mobility-evidence.v1":
                        assert "render_handle" not in content
                    else:
                        assert isinstance(content["render_handle"], str)
                        if render_svg:
                            rendered[aid] = await verify_native_mcp_svg(
                                session, content, direct, aid, output_root
                            )
                reviewed_spec = input_root / "verification-reviewed-spec.json"
                if reviewed_spec.is_file():
                    spec = json.loads(reviewed_spec.read_bytes())
                    direct = api.run_analysis(SOURCE, canonical(spec), allowed_root=input_root)
                    reply = await session.call_tool(
                        "patent_analysis.analyze",
                        {
                            "input_root_id": "input",
                            "path": SOURCE,
                            "spec": spec,
                        },
                    )
                    assert not reply.is_error, reply
                    assert canonical(reply.structured_content["content"]) == canonical(
                        public_document(direct)
                    )
    return {
        "transport": "stdio",
        "console_executable": params.command,
        "analysis_ids": list(INVENTOR_IDS),
        "svg": rendered,
        "public_api_equal": True,
        "m10_has_no_render_handle": True,
        "result_sha256": results,
        "mcp_version": metadata.version("mcp"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--examples", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path)
    parser.add_argument("--mcp", action="store_true")
    args = parser.parse_args()
    if not sys.flags.isolated:
        parser.error("use the clean installed venv's python -I")
    report = {
        "mode": "inventor-mcp" if args.mcp else "inventor",
        "python": sys.version,
        **release.installed_package(),
    }
    assert metadata.version("networkx") == "3.6.1"
    assert metadata.version("numpy") == "2.4.3"
    if not args.mcp:
        assert importlib.util.find_spec("mcp") is None
    with tempfile.TemporaryDirectory(prefix="inventor-installed-release-") as work:
        work = Path(work).resolve()
        input_root = work / "input"
        output_root = args.artifacts.resolve() if args.artifacts else work / "output"
        shutil.copytree(
            args.examples.resolve(strict=True) / "inventor-analysis",
            input_root / "inventor-analysis",
        )
        output_root.mkdir(parents=True)
        before = {
            p.relative_to(input_root).as_posix(): release.digest(p)
            for p in input_root.rglob("*")
            if p.is_file()
        }
        old_cwd = Path.cwd()
        try:
            os.chdir(work)
            os.environ.pop("PYTHONPATH", None)
            os.environ.pop("PYTHONHOME", None)
            os.environ["PATENT_ANALYSIS_ALLOWED_ROOT"] = str(input_root)
            report.update(
                verify_native(
                    input_root, output_root, render_svg=sys.platform in {"win32", "darwin"}
                )
            )
            report["review_roundtrip"] = verify_review_roundtrip(input_root)
            if args.mcp:
                import anyio

                report["mcp"] = anyio.run(
                    verify_native_mcp, input_root, output_root, sys.platform in {"win32", "darwin"}
                )
            assert all(release.digest(input_root / p) == value for p, value in before.items())
            report["installed_module_paths"] = assert_installed_imports()
        finally:
            os.chdir(old_cwd)
    report["fixture_sha256"] = before
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "mode": report["mode"],
                "analyses": len(report["analysis_ids"]),
                "svg_reuse_checks": len(report["svg"]),
                "mcp_svg_reuse_checks": len(report.get("mcp", {}).get("svg", {})),
                "input_unchanged": True,
            }
        )
    )


if __name__ == "__main__":
    main()
