from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from advanced_inventory import MCP_IDS

from patent_analysis.canonical_v2 import canonical_json_bytes

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "mcp"
RANKING_SPEC = json.loads((FIXTURE_ROOT / "ranking-spec.json").read_text(encoding="utf-8"))


def _registry(tmp_path: Path):
    from patent_analysis_mcp.roots import ApprovedRoot, RootRegistry

    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    input_root.mkdir()
    output_root.mkdir()
    (input_root / "input.csv").write_bytes((FIXTURE_ROOT / "input.csv").read_bytes())
    return (
        RootRegistry(
            input_roots=(ApprovedRoot("input", input_root),),
            output_roots=(ApprovedRoot("output", output_root),),
        ),
        input_root,
        output_root,
    )


def test_six_tools_use_the_shared_core_and_inspect_stays_metadata_only(tmp_path: Path) -> None:
    from patent_analysis_mcp.tool_handlers import ToolHandlers

    roots, _input_root, _output_root = _registry(tmp_path)
    handlers = ToolHandlers(roots=roots)

    assert handlers.tool_names() == (
        "patent_analysis.capabilities",
        "patent_analysis.schema",
        "patent_analysis.inspect",
        "patent_analysis.validate_spec",
        "patent_analysis.analyze",
        "patent_analysis.render",
    )
    capabilities = handlers.call("patent_analysis.capabilities", {})
    schema = handlers.call(
        "patent_analysis.schema",
        {"schema_name": "analysis-spec.schema.json"},
    )
    inspection = handlers.call(
        "patent_analysis.inspect",
        {"input_root_id": "input", "path": "input.csv"},
    )
    validation = handlers.call(
        "patent_analysis.validate_spec",
        {"spec": RANKING_SPEC},
    )
    analysis = handlers.call(
        "patent_analysis.analyze",
        {"input_root_id": "input", "path": "input.csv", "spec": RANKING_SPEC},
    )

    assert [item["analysis_id"] for item in capabilities["content"]["analyses"]] == list(MCP_IDS)
    assert schema["content"]["schema_name"] == "analysis-spec.schema.json"
    assert inspection["ok"] is True
    serialized_inspection = canonical_json_bytes(inspection)
    assert b'"rows"' not in serialized_inspection
    assert b'"samples"' not in serialized_inspection
    assert validation["content"] == {
        "valid": True,
        "analysis_id": "ranking.v1",
        "spec_variant": "versionless-ranking",
    }
    assert [
        (row["label"], row["value"], row["count"])
        for row in analysis["content"]["result"]["rows"]
    ] == [("A社", 2, 2), ("B社", 1, 1)]
    assert "receipt" not in analysis["content"]
    assert "sha256" not in repr(analysis["content"]).casefold()
    assert isinstance(analysis["content"]["render_handle"], str)
    assert len(analysis["content"]["render_handle"]) >= 32


@pytest.mark.parametrize("rejected_path", ["../outside.csv", "C:/outside.csv", "/outside.csv"])
def test_input_escape_is_rejected_without_path_disclosure(
    tmp_path: Path,
    rejected_path: str,
) -> None:
    from patent_analysis_mcp.tool_handlers import ToolHandlers

    roots, _input_root, _output_root = _registry(tmp_path)
    result = ToolHandlers(roots=roots).call(
        "patent_analysis.analyze",
        {"input_root_id": "input", "path": rejected_path, "spec": RANKING_SPEC},
    )

    assert result == {
        "ok": False,
        "error": {"code": "input.invalid", "message": "Tool input is invalid"},
    }
    assert "outside.csv" not in repr(result)


def test_symlink_escape_is_rejected_before_the_core_reads_it(tmp_path: Path) -> None:
    from patent_analysis_mcp.roots import RootError
    from patent_analysis_mcp.tool_handlers import ToolHandlers

    roots, input_root, _output_root = _registry(tmp_path)
    outside = tmp_path / "outside.csv"
    outside.write_text("secret\nvalue\n", encoding="utf-8")
    try:
        os.symlink(outside, input_root / "link.csv")
    except OSError:
        pytest.skip("symlink creation is unavailable")

    result = ToolHandlers(roots=roots).call(
        "patent_analysis.inspect",
        {"input_root_id": "input", "path": "link.csv"},
    )
    assert result["error"]["code"] == "input.invalid"
    assert "outside" not in repr(result)
    with pytest.raises(RootError):
        roots.resolve_input("input", "link.csv")


def test_private_analysis_is_rejected_before_execution(tmp_path: Path) -> None:
    from patent_analysis_mcp.tool_handlers import ToolHandlers

    roots, _input_root, _output_root = _registry(tmp_path)
    calls: list[str] = []
    fake_api = SimpleNamespace(
        get_public_schema=lambda _name: {},
        inspect_dataset=lambda *_args, **_kwargs: {},
        validate_analysis_spec_bytes=lambda _raw: {
            "valid": True,
            "analysis_id": "future-analysis.v1",
            "spec_variant": "analysis-spec-v2",
        },
        run_analysis_csv=lambda *_args, **_kwargs: calls.append("analyze") or {},
        render_analysis_svg=lambda *_args, **_kwargs: {},
    )

    result = ToolHandlers(roots=roots, api=fake_api).call(
        "patent_analysis.analyze",
        {"input_root_id": "input", "path": "input.csv", "spec": RANKING_SPEC},
    )

    assert result["error"]["code"] == "analysis.unknown"
    assert calls == []


def test_render_uses_only_the_approved_output_and_server_owned_node(tmp_path: Path) -> None:
    from patent_analysis_mcp.tool_handlers import ToolHandlers

    roots, _input_root, output_root = _registry(tmp_path)
    captured: dict[str, object] = {}

    def render(analysis_document: bytes, **kwargs: object) -> dict[str, object]:
        captured.update(analysis_document=analysis_document, **kwargs)
        return {
            "render_contract_version": "1.0.0",
            "ok": True,
            "status": "created",
            "artifact_id": "a" * 64,
            "svg": "ranking-svg-a.svg",
            "svg_sha256": "b" * 64,
            "renderer_build_digest": "c" * 64,
        }

    full_analysis_document = {
        "analysis_contract_version": "1.0.0",
        "ok": True,
        "result": {"analysis_type": "ranking", "rows": []},
        "receipt": {
            "algorithm_id": "ranking.v1",
            "package_version": "0.2.0",
            "input_sha256": "1" * 64,
            "spec_sha256": "2" * 64,
            "result_sha256": "3" * 64,
        },
    }
    fake_api = SimpleNamespace(
        validate_analysis_spec_bytes=lambda _raw: {
            "valid": True,
            "analysis_id": "ranking.v1",
            "spec_variant": "versionless-ranking",
        },
        run_analysis_csv=lambda *_args, **_kwargs: full_analysis_document,
        render_analysis_svg=render,
    )
    handlers = ToolHandlers(
        roots=roots,
        api=fake_api,
        node_executable="C:/trusted/node.exe",
    )
    analyzed = handlers.call(
        "patent_analysis.analyze",
        {"input_root_id": "input", "path": "input.csv", "spec": RANKING_SPEC},
    )
    render_handle = analyzed["content"]["render_handle"]

    result = handlers.call(
        "patent_analysis.render",
        {
            "output_root_id": "output",
            "output_path": "session-1",
            "analysis_handle": render_handle,
            "mark": "ranking-svg.v1",
        },
    )

    assert result["ok"] is True
    assert captured["analysis_document"] == canonical_json_bytes(full_analysis_document)
    assert captured["mark"] == "ranking-svg.v1"
    assert captured["output_directory"] == (output_root / "session-1").resolve()
    assert captured["node_executable"] == "C:/trusted/node.exe"


def test_render_handles_are_process_local_bounded_and_not_caller_forgeable(
    tmp_path: Path,
) -> None:
    from patent_analysis_mcp.tool_handlers import ToolHandlers

    roots, _input_root, _output_root = _registry(tmp_path)
    fake_api = SimpleNamespace(
        validate_analysis_spec_bytes=lambda _raw: {
            "valid": True,
            "analysis_id": "ranking.v1",
            "spec_variant": "versionless-ranking",
        },
        run_analysis_csv=lambda *_args, **_kwargs: {
            "analysis_contract_version": "1.0.0",
            "ok": True,
            "result": {"analysis_type": "ranking", "rows": []},
            "receipt": {"private": True},
        },
        render_analysis_svg=lambda *_args, **_kwargs: {"ok": True},
    )
    handlers = ToolHandlers(roots=roots, api=fake_api)
    handles = [
        handlers.call(
            "patent_analysis.analyze",
            {"input_root_id": "input", "path": "input.csv", "spec": RANKING_SPEC},
        )["content"]["render_handle"]
        for _ in range(5)
    ]

    evicted = handlers.call(
        "patent_analysis.render",
        {
            "output_root_id": "output",
            "output_path": "session-1",
            "analysis_handle": handles[0],
            "mark": "ranking-svg.v1",
        },
    )
    forged = handlers.call(
        "patent_analysis.render",
        {
            "output_root_id": "output",
            "output_path": "session-2",
            "analysis_handle": "caller-chosen",
            "mark": "ranking-svg.v1",
        },
    )

    assert evicted["error"]["code"] == "analysis.unknown"
    assert forged["error"]["code"] == "analysis.unknown"


def test_oversized_or_unsafe_results_fail_closed_and_cancellation_propagates(
    tmp_path: Path,
) -> None:
    from patent_analysis_mcp.tool_handlers import ToolHandlers

    roots, _input_root, _output_root = _registry(tmp_path)
    calls: list[str] = []
    handlers = ToolHandlers(roots=roots, argument_maximum_bytes=128)
    oversized = handlers.call(
        "patent_analysis.analyze",
        {"input_root_id": "input", "path": "x" * 256, "spec": RANKING_SPEC},
    )
    assert oversized["error"]["code"] == "input.too_large"

    large_result_api = SimpleNamespace(
        validate_analysis_spec_bytes=lambda _raw: {
            "valid": True,
            "analysis_id": "ranking.v1",
            "spec_variant": "versionless-ranking",
        },
        run_analysis_csv=lambda *_args, **_kwargs: {"summary": "x" * 512},
    )
    response_limited = ToolHandlers(
        roots=roots,
        api=large_result_api,
        response_maximum_bytes=128,
    ).call(
        "patent_analysis.analyze",
        {"input_root_id": "input", "path": "input.csv", "spec": RANKING_SPEC},
    )
    assert response_limited["error"]["code"] == "response.too_large"

    secret_api = SimpleNamespace(
        inspect_dataset=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("token=secret C:/customer.csv")
        ),
        validate_analysis_spec_bytes=lambda _raw: {
            "valid": True,
            "analysis_id": "ranking.v1",
            "spec_variant": "versionless-ranking",
        },
        run_analysis_csv=lambda *_args, **_kwargs: calls.append("analyze")
        or {"raw_rows": [{"secret": "value"}]},
        render_analysis_svg=lambda *_args, **_kwargs: {},
        get_public_schema=lambda _name: {},
    )
    unsafe = ToolHandlers(roots=roots, api=secret_api)
    inspection = unsafe.call(
        "patent_analysis.inspect",
        {"input_root_id": "input", "path": "input.csv"},
    )
    analysis = unsafe.call(
        "patent_analysis.analyze",
        {"input_root_id": "input", "path": "input.csv", "spec": RANKING_SPEC},
    )
    assert inspection["error"] == {
        "code": "internal.failed",
        "message": "Internal MCP adapter failure",
    }
    assert "secret" not in repr(inspection)
    assert analysis["error"]["code"] == "internal.failed"
    assert "value" not in repr(analysis)

    cancelling_api = SimpleNamespace(
        inspect_dataset=lambda *_args, **_kwargs: (_ for _ in ()).throw(KeyboardInterrupt()),
    )
    with pytest.raises(KeyboardInterrupt):
        ToolHandlers(roots=roots, api=cancelling_api).call(
            "patent_analysis.inspect",
            {"input_root_id": "input", "path": "input.csv"},
        )


@pytest.mark.parametrize("replace_parent", [False, True])
def test_replaced_output_root_is_rejected_before_creating_outside_directories(
    tmp_path: Path, replace_parent: bool,
) -> None:
    from patent_analysis_mcp.roots import ApprovedRoot, RootError, RootRegistry

    input_root = tmp_path / "input"
    parent = tmp_path / "approved"
    output_root = parent / "output"
    outside = tmp_path / "outside"
    input_root.mkdir()
    output_root.mkdir(parents=True)
    outside.mkdir()
    roots = RootRegistry(input_roots=(ApprovedRoot("in", input_root),),
                         output_roots=(ApprovedRoot("out", output_root),))
    swapped = parent if replace_parent else output_root
    if replace_parent:
        (outside / "output").mkdir()
    swapped.rename(tmp_path / "original")
    try:
        swapped.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlink creation is unavailable")
    before = sorted(str(p.relative_to(outside)) for p in outside.rglob("*"))
    with pytest.raises(RootError):
        roots.resolve_output_directory("out", "session/nested")
    assert sorted(str(p.relative_to(outside)) for p in outside.rglob("*")) == before


def test_render_value_labels_is_an_optional_closed_choice(tmp_path: Path) -> None:
    from patent_analysis_mcp.tool_handlers import ToolHandlers

    roots, _input_root, _output_root = _registry(tmp_path)
    calls: list[dict[str, object]] = []

    def render(_document: bytes, **kwargs: object) -> dict[str, object]:
        calls.append(kwargs)
        return {"render_contract_version": "1.0.0", "ok": True, "status": "created"}

    analysis = {
        "analysis_contract_version": "1.0.0",
        "ok": True,
        "result": {"analysis_type": "ranking", "rows": []},
        "receipt": {"algorithm_id": "ranking.v1"},
    }
    handlers = ToolHandlers(
        roots=roots,
        api=SimpleNamespace(
            validate_analysis_spec_bytes=lambda _raw: {
                "valid": True,
                "analysis_id": "ranking.v1",
                "spec_variant": "versionless-ranking",
            },
            run_analysis_csv=lambda *_a, **_k: analysis,
            render_analysis_svg=render,
        ),
    )
    handle = handlers.call(
        "patent_analysis.analyze",
        {"input_root_id": "input", "path": "input.csv", "spec": RANKING_SPEC},
    )["content"]["render_handle"]
    base = {
        "output_root_id": "output",
        "output_path": "session-1",
        "analysis_handle": handle,
        "mark": "ranking-svg.v1",
    }

    assert handlers.call("patent_analysis.render", base)["ok"] is True
    assert handlers.call("patent_analysis.render", {**base, "value_labels": "shown"})["ok"] is True
    assert (
        handlers.call("patent_analysis.render", {**base, "palette": "colorblind"})["ok"] is True
    )
    assert "value_labels" not in calls[0] and "palette" not in calls[0]
    assert calls[1]["value_labels"] == "shown"
    assert calls[2]["palette"] == "colorblind"
    bad_options = (
        {"value_labels": "loud"},
        {"value_labels": 1},
        {"palette": "neon"},
        {"palette": None},
        {"theme": "dark"},
    )
    for bad in bad_options:
        result = handlers.call("patent_analysis.render", {**base, **bad})
        assert result["ok"] is False
        assert result["error"]["code"] == "input.invalid"
    assert len(calls) == 3
