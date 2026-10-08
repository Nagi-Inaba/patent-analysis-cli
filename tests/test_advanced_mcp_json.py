"""MCP fault-injection and render-handle lifecycle regressions."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from patent_analysis_mcp.contracts import MAX_TOOL_RESPONSE_BYTES
from patent_analysis_mcp.exposure import require_visible_analysis
from patent_analysis_mcp.roots import ApprovedRoot, RootRegistry
from patent_analysis_mcp.tool_handlers import ToolHandlers

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "advanced"
JSON_IDS = (
    "growth-quadrant.v1",
    "entry-exit.v1",
    "citation.v1",
    "matrix-composition.v1",
    "new-entrants.v1",
    "compara.v1",
    "cooccurrence.v1",
    "collaboration-network.v1",
    "uniqueness.v1",
    "shared-involvement.v1",
)


def _spec(analysis_id: str) -> dict[str, object]:
    return json.loads((EXAMPLES / f"{analysis_id[:-3]}.json").read_text(encoding="utf-8"))


def _session(
    tmp_path: Path,
    *,
    api_override: object | None = None,
    response_bytes: int = MAX_TOOL_RESPONSE_BYTES,
):
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    input_root.mkdir()
    output_root.mkdir()
    (input_root / "patents.csv").write_bytes((EXAMPLES / "patents.csv").read_bytes())
    roots = RootRegistry(
        input_roots=(ApprovedRoot("input", input_root),),
        output_roots=(ApprovedRoot("output", output_root),),
    )
    return (
        ToolHandlers(roots=roots, api=api_override, response_maximum_bytes=response_bytes),
        input_root,
        output_root,
    )


def _arguments(analysis_id: str) -> dict[str, object]:
    return {"input_root_id": "input", "path": "patents.csv", "spec": _spec(analysis_id)}


def test_json_requests_do_not_evict_existing_render_handles(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handlers, _, _ = _session(tmp_path)
    growth = _spec("entry-exit.v1")
    growth["analysis_id"] = "growth.v1"
    growth["parameters"] = {
        "date_role": "year",
        "series_role": "group",
        "start_year": 2020,
        "end_year": 2024,
    }
    arguments = {"input_root_id": "input", "path": "patents.csv", "spec": growth}
    for _ in range(4):
        result = handlers.call("patent_analysis.analyze", arguments)
        assert result["ok"] is True, result
        assert isinstance(result["content"]["render_handle"], str)
    saved = dict(handlers._render_documents)
    assert len(saved) == 4

    # Explicitly simulate an unbuilt/JSON-only definition, not the live activated inventory.
    def json_only_definition(analysis_id: str):
        definition = require_visible_analysis(analysis_id)
        return replace(definition, compatible_render_marks=())

    monkeypatch.setattr(
        "patent_analysis_mcp.tool_handlers.require_visible_analysis",
        json_only_definition,
    )

    def no_new_handle(*_args: object, **_kwargs: object) -> str:
        pytest.fail("JSON-only analysis must not allocate a render handle")

    monkeypatch.setattr("patent_analysis_mcp.tool_handlers.secrets.token_urlsafe", no_new_handle)
    for analysis_id in JSON_IDS:
        result = handlers.call("patent_analysis.analyze", _arguments(analysis_id))
        assert result["ok"] is True, result
    assert handlers._render_documents == saved


def test_json_no_artifact_handle_can_be_forged_or_used_for_render(tmp_path: Path) -> None:
    handlers, _, output_root = _session(tmp_path)
    assert handlers.call("patent_analysis.analyze", _arguments("entry-exit.v1"))["ok"] is True
    result = handlers.call(
        "patent_analysis.render",
        {
            "output_root_id": "output",
            "output_path": "unused",
            "analysis_handle": "forged-json-handle",
            "mark": "entry-exit-svg.v1",
        },
    )
    assert result["ok"] is False
    assert result["error"]["code"] == "analysis.unknown"
    assert list(output_root.iterdir()) == []


@pytest.mark.parametrize("key", ["raw_rows", "source_fields", "absolute_path"])
def test_injected_unsafe_core_response_still_fails_closed(tmp_path: Path, key: str) -> None:
    # This is deliberately a facade fault-injection test, not calculation validation.
    fake = SimpleNamespace(
        validate_analysis_spec_bytes=lambda _raw: {"valid": True, "analysis_id": "entry-exit.v1"},
        run_analysis_csv=lambda *_a, **_kw: {"data": {key: "PRIVATE_TEST_MARKER"}},
    )
    handlers, _, _ = _session(tmp_path, api_override=fake)
    result = handlers.call("patent_analysis.analyze", _arguments("entry-exit.v1"))
    assert result["ok"] is False
    assert result["error"]["code"] == "internal.failed"
    assert "PRIVATE_TEST_MARKER" not in repr(result)
    assert handlers._render_documents == {}


def test_injected_oversized_json_response_does_not_use_render_storage(tmp_path: Path) -> None:
    fake = SimpleNamespace(
        validate_analysis_spec_bytes=lambda _raw: {"valid": True, "analysis_id": "entry-exit.v1"},
        run_analysis_csv=lambda *_a, **_kw: {"data": {"label": "x" * 1024}},
    )
    handlers, _, _ = _session(tmp_path, api_override=fake, response_bytes=128)
    result = handlers.call("patent_analysis.analyze", _arguments("entry-exit.v1"))
    assert result["ok"] is False
    assert result["error"]["code"] == "response.too_large"
    assert handlers._render_documents == {}


def test_json_core_provenance_is_removed_without_mutating_the_document(tmp_path: Path) -> None:
    document = {
        "data": {"points": [{"label": "A", "value": 2, "input_sha256": "a" * 64}]},
        "receipt": {"private": True},
        "dataset_sha256": "b" * 64,
    }
    before = deepcopy(document)
    fake = SimpleNamespace(
        validate_analysis_spec_bytes=lambda _raw: {"valid": True, "analysis_id": "entry-exit.v1"},
        run_analysis_csv=lambda *_a, **_kw: document,
    )
    handlers, _, _ = _session(tmp_path, api_override=fake)
    result = handlers.call("patent_analysis.analyze", _arguments("entry-exit.v1"))
    assert result["ok"] is True
    handle = result["content"].pop("render_handle")
    assert handle in handlers._render_documents
    assert result == {"ok": True, "content": {"data": {"points": [{"label": "A", "value": 2}]}}}
    assert document == before


def test_committed_entry_exit_session_uses_real_handlers(tmp_path: Path) -> None:
    handlers, _, _ = _session(tmp_path)
    session = json.loads(
        (EXAMPLES.parent / "mcp" / "entry-exit-json-session.json").read_text(encoding="utf-8")
    )
    for request in session["requests"]:
        response = handlers.call(request["name"], request["arguments"])
        assert response["ok"] is True, response
    assert response["content"]["analysis_id"] == "entry-exit.v1"
    assert response["content"]["render_handle"] in handlers._render_documents


@pytest.mark.parametrize("fault", ["unsafe", "oversized"])
def test_rejected_renderable_response_restores_all_four_handles(tmp_path: Path, fault: str):
    handlers, input_root, output_root = _session(tmp_path)
    for _ in range(4):
        response = handlers.call("patent_analysis.analyze", _arguments("entry-exit.v1"))
        assert response["ok"] is True, response
    before = dict(handlers._render_documents)
    source = (input_root / "patents.csv").read_bytes()
    document = (
        {"data": {"raw_rows": "PRIVATE_TEST_MARKER"}}
        if fault == "unsafe"
        else {
            "data": {"label": "x" * 1024},
        }
    )
    handlers.api = SimpleNamespace(
        validate_analysis_spec_bytes=lambda _raw: {"valid": True, "analysis_id": "entry-exit.v1"},
        run_analysis_csv=lambda *_args, **_kwargs: document,
    )
    if fault == "oversized":
        handlers.response_maximum_bytes = 128
    result = handlers.call("patent_analysis.analyze", _arguments("entry-exit.v1"))
    assert result["ok"] is False
    assert result["error"]["code"] == (
        "internal.failed" if fault == "unsafe" else "response.too_large"
    )
    assert "PRIVATE_TEST_MARKER" not in repr(result)
    assert list(handlers._render_documents.items()) == list(before.items())
    assert (input_root / "patents.csv").read_bytes() == source
    assert list(output_root.iterdir()) == []


def test_successful_advanced_analyses_keep_exact_four_handle_fifo(tmp_path: Path):
    handlers, _, output_root = _session(tmp_path)
    issued = []
    for analysis_id in JSON_IDS:
        result = handlers.call("patent_analysis.analyze", _arguments(analysis_id))
        assert result["ok"] is True, result
        issued.append(result["content"]["render_handle"])
        assert list(handlers._render_documents) == issued[-4:]
    assert len(set(issued)) == len(issued)
    assert list(output_root.iterdir()) == []
