"""Opt-in MCP checks retain the six-tool, metadata-only local boundary."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator

from patent_analysis.canonical_v2 import canonical_json_bytes
from patent_analysis_mcp.exposure import describe_mcp_capabilities
from patent_analysis_mcp.roots import ApprovedRoot, RootRegistry
from patent_analysis_mcp.server import _INPUT_SCHEMAS
from patent_analysis_mcp.tool_handlers import ToolHandlers

FIXTURES = Path(__file__).parent / "fixtures" / "mcp"
RANKING_SPEC = json.loads((FIXTURES / "ranking-spec.json").read_text(encoding="utf-8"))
VALIDATION = {"valid": True, "analysis_id": "ranking.v1", "spec_variant": "versionless-ranking"}
INVALID = {"ok": False, "error": {"code": "input.invalid", "message": "Tool input is invalid"}}


def _roots(tmp_path: Path) -> tuple[RootRegistry, Path]:
    source = tmp_path / "private-input"
    output = tmp_path / "private-output"
    source.mkdir()
    output.mkdir()
    (source / "input.csv").write_bytes((FIXTURES / "input.csv").read_bytes())
    return RootRegistry(
        input_roots=(ApprovedRoot("input", source),),
        output_roots=(ApprovedRoot("output", output),),
    ), source


def test_capabilities_default_and_explicit_false_do_not_probe(tmp_path: Path) -> None:
    roots, _ = _roots(tmp_path)
    calls = []
    handlers = ToolHandlers(
        roots=roots, api=SimpleNamespace(diagnose_renderer=lambda **_: calls.append("probe")),
    )
    default = handlers.call("patent_analysis.capabilities", {})
    disabled = handlers.call("patent_analysis.capabilities", {"check_runtime": False})
    assert default == disabled == {"ok": True, "content": describe_mcp_capabilities()}
    assert calls == [] and len(handlers.tool_names()) == 6


def test_capabilities_opt_in_uses_only_server_selected_node(tmp_path: Path) -> None:
    roots, _ = _roots(tmp_path)
    captured = {}
    report = {"available": False, "checks": [{"code": "node.version_mismatch"}]}

    def diagnose(**kwargs):
        captured.update(kwargs)
        return report

    handlers = ToolHandlers(
        roots=roots, api=SimpleNamespace(diagnose_renderer=diagnose),
        node_executable="C:/PRIVATE_NODE_PATH/node.exe",
    )
    result = handlers.call("patent_analysis.capabilities", {"check_runtime": True})
    assert result == {"ok": True, "content": {
        **describe_mcp_capabilities(), "renderer_runtime": report,
    }}
    assert captured == {"node_executable": "C:/PRIVATE_NODE_PATH/node.exe"}
    assert "PRIVATE_NODE_PATH" not in repr(result)


@pytest.mark.parametrize("value", [None, 1, 0, "true", [], {}])
def test_capabilities_runtime_flag_rejects_non_boolean(tmp_path: Path, value: object) -> None:
    roots, _ = _roots(tmp_path)
    assert ToolHandlers(roots=roots).call(
        "patent_analysis.capabilities", {"check_runtime": value},
    ) == INVALID


def test_spec_only_validation_keeps_legacy_response(tmp_path: Path) -> None:
    roots, _ = _roots(tmp_path)
    calls = []

    def validate(raw):
        calls.append(raw)
        return VALIDATION

    handlers = ToolHandlers(roots=roots, api=SimpleNamespace(validate_analysis_spec_bytes=validate))
    result = handlers.call("patent_analysis.validate_spec", {"spec": RANKING_SPEC})
    assert result == {"ok": True, "content": VALIDATION}
    assert calls == [canonical_json_bytes(RANKING_SPEC)]


def test_preflight_runs_after_visible_spec_validation_with_approved_relative_input(
    tmp_path: Path,
) -> None:
    roots, source = _roots(tmp_path)
    events = []
    report = {"checks_passed": False, "roles": [{"role": "dimension", "bound": False}]}

    def validate(raw):
        events.append(("validate", raw))
        return VALIDATION

    def preflight(path, raw, **kwargs):
        events.append(("preflight", path, raw, kwargs))
        return report

    handlers = ToolHandlers(roots=roots, api=SimpleNamespace(
        validate_analysis_spec_bytes=validate, preflight_analysis=preflight,
    ))
    result = handlers.call("patent_analysis.validate_spec", {
        "spec": RANKING_SPEC, "input_root_id": "input", "path": "input.csv",
    })
    assert result == {"ok": True, "content": report}
    raw = canonical_json_bytes(RANKING_SPEC)
    assert events == [("validate", raw), ("preflight", "input.csv", raw, {
        "allowed_root": source.resolve(),
    })]
    assert "render_handle" not in result["content"]


@pytest.mark.parametrize("extra", [
    {"input_root_id": "input"}, {"path": "input.csv"},
    {"input_root_id": None, "path": "input.csv"},
    {"input_root_id": 1, "path": "input.csv"},
    {"input_root_id": "", "path": "input.csv"},
    {"input_root_id": "input", "path": None},
    {"input_root_id": "input", "path": []},
    {"input_root_id": "input", "path": ""},
    {"input_root_id": "input", "input_path": "input.csv"},
])
def test_preflight_requires_the_complete_typed_input_pair(tmp_path: Path, extra: dict) -> None:
    roots, _ = _roots(tmp_path)
    calls = []
    handlers = ToolHandlers(roots=roots, api=SimpleNamespace(
        validate_analysis_spec_bytes=lambda _: VALIDATION,
        preflight_analysis=lambda *_a, **_kw: calls.append("preflight") or {},
    ))
    result = handlers.call("patent_analysis.validate_spec", {"spec": RANKING_SPEC, **extra})
    assert result == INVALID and calls == []


@pytest.mark.parametrize("root_id, path", [
    ("PRIVATE_UNKNOWN_ROOT", "input.csv"), ("input", "../PRIVATE_OUTSIDE.csv"),
    ("input", "C:/PRIVATE_OUTSIDE.csv"), ("input", "/PRIVATE_OUTSIDE.csv"),
])
def test_preflight_keeps_input_root_boundary_private(
    tmp_path: Path, root_id: str, path: str,
) -> None:
    roots, _ = _roots(tmp_path)
    calls = []
    handlers = ToolHandlers(roots=roots, api=SimpleNamespace(
        validate_analysis_spec_bytes=lambda _: VALIDATION,
        preflight_analysis=lambda *_a, **_kw: calls.append("preflight") or {},
    ))
    result = handlers.call("patent_analysis.validate_spec", {
        "spec": RANKING_SPEC, "input_root_id": root_id, "path": path,
    })
    assert result == INVALID and calls == []
    assert "PRIVATE" not in repr(result) and str(tmp_path) not in repr(result)


def test_hidden_analysis_is_rejected_before_input_access_or_preflight(tmp_path: Path) -> None:
    roots, _ = _roots(tmp_path)
    calls = []
    handlers = ToolHandlers(roots=roots, api=SimpleNamespace(
        validate_analysis_spec_bytes=lambda _: {**VALIDATION, "analysis_id": "PRIVATE_ANALYSIS"},
        preflight_analysis=lambda *_a, **_kw: calls.append("preflight") or {},
    ))
    result = handlers.call("patent_analysis.validate_spec", {
        "spec": RANKING_SPEC, "input_root_id": "PRIVATE_ROOT", "path": "PRIVATE_CELL.csv",
    })
    assert result == {"ok": False, "error": {
        "code": "analysis.unknown", "message": "Analysis is unavailable",
    }}
    assert calls == [] and "PRIVATE" not in repr(result)


@pytest.mark.parametrize("mode", ["preflight", "diagnostics"])
@pytest.mark.parametrize("kind", ["exception", "forbidden-key"])
def test_new_checks_use_existing_error_and_response_sanitizers(
    tmp_path: Path, mode: str, kind: str,
) -> None:
    roots, _ = _roots(tmp_path)

    def unsafe(*_args, **_kwargs):
        if kind == "exception":
            raise RuntimeError("PRIVATE_CELL PRIVATE_ROOT PRIVATE_STDERR")
        return {"stderr": "PRIVATE_CELL PRIVATE_ROOT PRIVATE_STDERR"}

    handlers = ToolHandlers(roots=roots, api=SimpleNamespace(
        validate_analysis_spec_bytes=lambda _: VALIDATION,
        preflight_analysis=unsafe, diagnose_renderer=unsafe,
    ))
    if mode == "preflight":
        result = handlers.call("patent_analysis.validate_spec", {
            "spec": RANKING_SPEC, "input_root_id": "input", "path": "input.csv",
        })
    else:
        result = handlers.call("patent_analysis.capabilities", {"check_runtime": True})
    assert result["ok"] is False and "PRIVATE" not in repr(result)


def test_real_preflight_returns_counts_without_cells_paths_or_source_changes(
    tmp_path: Path,
) -> None:
    roots, source = _roots(tmp_path)
    path = source / "input.csv"
    raw = b"group,year,family,filed\nPRIVATE_A,2020,F,2020-01-01\n" \
          b"PRIVATE_B,2020,F,2020-02-01\nPRIVATE_C,garbage,G,\n"
    path.write_bytes(raw)
    spec = {
        "analysis_contract_version": "2.0.0", "analysis_id": "composition.v1",
        "resolution": {"bindings": {"group": "group", "year": "year",
                                    "family": "family", "filed": "filed"}},
        "normalization": {"profiles": []},
        "population": {
            "filters": [{"role": "year", "effect": "include", "match": "year", "value": 2020}],
            "selection_sets": [], "family_mode": "earliest", "family_role": "family",
            "date_role": "filed",
        },
        "parameters": {"role": "group"},
    }
    result = ToolHandlers(roots=roots).call("patent_analysis.validate_spec", {
        "spec": spec, "input_root_id": "input", "path": "input.csv",
    })
    assert result["ok"] is True
    assert result["content"]["checks_passed"] is True
    assert result["content"]["population"] == {
        "input_rows": 3, "matched_rows": 2, "selected_rows": 1,
        "filtered_rows": 1, "collapsed_rows": 1,
    }
    serialized = json.dumps(result)
    assert "PRIVATE" not in serialized and str(source) not in serialized
    assert "raw_rows" not in serialized and "sha256" not in serialized
    assert path.read_bytes() == raw


def test_advertised_schemas_expose_optional_flags_and_pair_dependencies() -> None:
    capabilities = Draft202012Validator(_INPUT_SCHEMAS["patent_analysis.capabilities"])
    validation = Draft202012Validator(_INPUT_SCHEMAS["patent_analysis.validate_spec"])
    assert capabilities.is_valid({}) and capabilities.is_valid({"check_runtime": True})
    assert capabilities.is_valid({"check_runtime": False})
    assert not capabilities.is_valid({"check_runtime": 1})
    assert validation.is_valid({"spec": RANKING_SPEC})
    assert validation.is_valid({
        "spec": RANKING_SPEC, "input_root_id": "input", "path": "input.csv",
    })
    assert not validation.is_valid({"spec": RANKING_SPEC, "input_root_id": "input"})
    assert not validation.is_valid({"spec": RANKING_SPEC, "path": "input.csv"})
