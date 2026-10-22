from __future__ import annotations

import base64
import hashlib
import importlib
import json
import struct
import traceback
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

import patent_analysis
from patent_analysis._render_canonical import CanonicalJsonError, parse_canonical_json_bytes
from patent_analysis._render_contracts import RenderContractError, validate_chart_model
from patent_analysis._render_text import grapheme_count, truncate_title_dimension
from patent_analysis.renderer_protocol import (
    MAX_RENDERER_STDOUT_BYTES,
    RendererDeclaredError,
)
from patent_analysis.renderer_resources import (
    RendererBuildManifest,
    RendererResources,
    RendererRuntimeBinding,
)

_VISUAL_CORPUS = json.loads(
    (Path(__file__).parent / "fixtures" / "renderer-visual-cases.json").read_text(
        encoding="utf-8"
    )
)


def _load_runtime_module() -> tuple[bool, Any | None]:
    try:
        return True, importlib.import_module("patent_analysis.renderer_runtime")
    except ModuleNotFoundError:
        return False, None


def _resources() -> RendererResources:
    manifest = RendererBuildManifest(
        renderer_build_manifest_version="1.0.0",
        bootstrap_sha256="b" * 64,
        renderer_bundle_sha256="c" * 64,
        renderer_protocol_version="1.0.0",
        echarts_version="6.1.0",
        build_tool_id="patent-analysis.renderer-bundler",
        build_tool_version="1.0.0",
    )
    runtime = RendererRuntimeBinding(
        node_version="22.23.4",
        echarts_version="6.1.0",
        renderer_build_digest="d" * 64,
        render_profile_id="ranking-svg-ja-jp-node22-echarts6.v1",
    )
    return RendererResources(
        manifest=manifest,
        manifest_bytes=b"manifest",
        bootstrap_bytes=b"bootstrap",
        bundle_bytes=b"immutable-bundle",
        renderer_build_digest=runtime.renderer_build_digest,
        runtime=runtime,
    )


def _semantic_chart_model() -> dict[str, Any]:
    return {
        "chart_model_contract_version": "1.0.0",
        "chart_type": "ranking.horizontal_bar",
        "analysis_result_sha256": "a" * 64,
        "label_overlay_sha256": None,
        "title": "出願人のランキング",
        "dimension": {
            "source_label": "applicant",
            "display_label": "出願人",
            "description": None,
        },
        "measure": {"mode": "count", "column": None},
        "population": {"input_rows": 1, "analyzed_rows": 1},
        "rows": [
            {
                "index": 0,
                "row_kind": "dimension_value",
                "source_label": "甲社",
                "display_label": "甲社",
                "description": None,
                "semantic_label": "データ中の分類値",
                "value": 1,
                "count": 1,
                "share": 1,
            }
        ],
        "warnings": [],
    }


def _semantic_display_texts(model: dict[str, Any]) -> list[str]:
    dimension = model["dimension"]
    texts = [model["title"], dimension["source_label"], dimension["display_label"]]
    if dimension["description"] is not None:
        texts.append(dimension["description"])
    if model["measure"]["column"] is not None:
        texts.append(model["measure"]["column"])
    for row in model["rows"]:
        texts.extend([row["source_label"], row["display_label"], row["semantic_label"]])
        if row["description"] is not None:
            texts.append(row["description"])
    texts.extend(model["warnings"])
    return texts


def _fill_display_budget(model: dict[str, Any], target: int) -> None:
    base = sum(grapheme_count(text) for text in _semantic_display_texts(model))
    remaining = target - base
    if remaining < 0:
        raise AssertionError("semantic fixture exceeds target before filler")
    warnings: list[str] = []
    while remaining:
        size = min(4096, remaining)
        warnings.append("w" * size)
        remaining -= size
    model["warnings"] = warnings


def _apply_semantic_operation(operation: str) -> dict[str, Any]:
    model = deepcopy(_semantic_chart_model())
    if operation == "none":
        return model
    if operation == "unicode_graphemes":
        model["dimension"]["display_label"] = "👩‍🔬é"
        model["title"] = truncate_title_dimension(model["dimension"]["display_label"])
        model["rows"][0]["display_label"] = "👩‍🔬é"
    elif operation == "nfd_dimension_title":
        model["dimension"]["display_label"] = "e\u0301"
        model["title"] = truncate_title_dimension(model["dimension"]["display_label"])
    elif operation == "nfd_row":
        model["rows"][0]["display_label"] = "e\u0301"
    elif operation == "nfd_warning":
        model["warnings"] = ["e\u0301"]
    elif operation == "two_other":
        model["population"] = {"input_rows": 2, "analyzed_rows": 2}
        model["rows"] = [
            {
                **model["rows"][0],
                "source_label": "その他",
                "display_label": "その他",
                "value": 1.0,
                "share": 0.5,
            },
            {
                **model["rows"][0],
                "index": 1,
                "row_kind": "remainder",
                "source_label": "その他",
                "display_label": "その他",
                "semantic_label": "上位表示外の合計",
                "value": -1,
                "share": 0.5,
            },
        ]
    elif operation in {"title_250", "title_251"}:
        size = 250 if operation == "title_250" else 251
        model["dimension"]["display_label"] = "あ" * size
        model["title"] = truncate_title_dimension(model["dimension"]["display_label"])
    elif operation in {"description_256", "dimension_description_257"}:
        size = 256 if operation == "description_256" else 257
        model["dimension"]["description"] = "説" * size
    elif operation in {"measure_column_256", "measure_column_257"}:
        size = 256 if operation == "measure_column_256" else 257
        model["measure"] = {"mode": "sum", "column": "列" * size}
    elif operation == "display_budget_20000":
        _fill_display_budget(model, 20_000)
    elif operation == "display_budget_20001":
        _fill_display_budget(model, 20_001)
    elif operation == "title_mismatch":
        model["title"] = "wrong title"
    elif operation == "unsafe_newline":
        model["rows"][0]["display_label"] = "unsafe\nlabel"
    elif operation == "unsafe_c1":
        model["warnings"] = ["a\u0080"]
    elif operation == "unsafe_bidi":
        model["warnings"] = ["a\u202e"]
    elif operation == "unsafe_noncharacter":
        model["warnings"] = ["a\ufdd0"]
    elif operation == "unsafe_plane_noncharacter":
        model["warnings"] = ["a" + chr(0x1FFFF)]
    elif operation == "dimension_source_257":
        model["dimension"]["source_label"] = "源" * 257
    elif operation == "row_display_257":
        model["rows"][0]["display_label"] = "行" * 257
    elif operation == "row_description_257":
        model["rows"][0]["description"] = "説" * 257
    else:
        raise AssertionError(f"unknown semantic fixture operation: {operation}")
    return model


def _frame_request(frame: bytes) -> tuple[bytes, dict[str, object]]:
    magic, version, bundle_length, request_length = struct.unpack(">8sIII", frame[:20])
    assert magic == b"PARSVG01"
    assert version == 1
    assert len(frame) == 20 + bundle_length + request_length
    bundle = frame[20 : 20 + bundle_length]
    request = json.loads(frame[20 + bundle_length :].decode("utf-8"))
    assert isinstance(request, dict)
    return bundle, request


@dataclass(frozen=True)
class _ProcessResult:
    returncode: int
    stdout: bytes
    stderr: bytes


def _runtime_object(binding: RendererRuntimeBinding) -> dict[str, str]:
    return {
        "node_version": binding.node_version,
        "echarts_version": binding.echarts_version,
        "renderer_build_digest": binding.renderer_build_digest,
        "render_profile_id": binding.render_profile_id,
    }


def _success_response(binding: RendererRuntimeBinding, svg: bytes = b"<svg/>\n") -> bytes:
    return (
        json.dumps(
            {
                "protocol_version": "1.0.0",
                "ok": True,
                "runtime": _runtime_object(binding),
                "svg_b64": base64.b64encode(svg).decode("ascii"),
            },
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode("ascii")
        + b"\n"
    )


def _failure_response(binding: RendererRuntimeBinding, code: str, message: str) -> bytes:
    return (
        json.dumps(
            {
                "protocol_version": "1.0.0",
                "ok": False,
                "runtime": _runtime_object(binding),
                "error": {"code": code, "message": message},
            },
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode("ascii")
        + b"\n"
    )


def test_internal_renderer_runtime_interfaces_build_the_exact_task3_frame() -> None:
    loaded, module = _load_runtime_module()

    assert loaded is True
    assert module is not None
    assert callable(module.build_renderer_request)
    assert callable(module.run_bound_renderer)

    resources = _resources()
    model_bytes = b'{"chart_model_contract_version":"1.0.0"}'
    spec_bytes = b'{"render_spec_contract_version":"1.0.0"}'
    frame = module.build_renderer_request(model_bytes, spec_bytes, resources)
    bundle, request = _frame_request(frame)

    assert bundle == resources.bundle_bytes
    assert set(request) == {
        "protocol_version",
        "chart_model_b64",
        "chart_model_sha256",
        "render_spec_b64",
        "render_spec_sha256",
    }
    assert request == {
        "protocol_version": "1.0.0",
        "chart_model_b64": base64.b64encode(model_bytes).decode("ascii"),
        "chart_model_sha256": hashlib.sha256(model_bytes).hexdigest(),
        "render_spec_b64": base64.b64encode(spec_bytes).decode("ascii"),
        "render_spec_sha256": hashlib.sha256(spec_bytes).hexdigest(),
    }
    assert base64.b64decode(request["chart_model_b64"], validate=True) is not model_bytes
    assert base64.b64decode(request["chart_model_b64"], validate=True) == model_bytes
    assert base64.b64decode(request["render_spec_b64"], validate=True) == spec_bytes


def test_renderer_request_preallocation_limits_accept_exact_boundaries() -> None:
    loaded, module = _load_runtime_module()
    assert loaded is True and module is not None
    resources = _resources()

    model_frame = module.build_renderer_request(
        b"m" * (2 * 1024 * 1024), b"{}", resources
    )
    _, model_request = _frame_request(model_frame)
    assert len(base64.b64decode(model_request["chart_model_b64"], validate=True)) == (
        2 * 1024 * 1024
    )

    spec_frame = module.build_renderer_request(b"{}", b"s" * (16 * 1024), resources)
    _, spec_request = _frame_request(spec_frame)
    assert len(base64.b64decode(spec_request["render_spec_b64"], validate=True)) == (
        16 * 1024
    )


@pytest.mark.parametrize(
    ("model_bytes", "spec_bytes"),
    [
        (b"m" * (2 * 1024 * 1024 + 1), b"{}"),
        (b"{}", b"s" * (16 * 1024 + 1)),
    ],
    ids=["model-limit-plus-one", "spec-limit-plus-one"],
)
def test_renderer_request_rejects_oversize_before_encoding_hashing_or_request_allocation(
    monkeypatch: pytest.MonkeyPatch,
    model_bytes: bytes,
    spec_bytes: bytes,
) -> None:
    loaded, module = _load_runtime_module()
    assert loaded is True and module is not None
    calls: list[str] = []

    def unexpected(name: str):
        def fail(*_args: object, **_kwargs: object) -> None:
            calls.append(name)
            raise AssertionError(f"oversize path called {name}")

        return fail

    monkeypatch.setattr(module.base64, "b64encode", unexpected("base64"))
    monkeypatch.setattr(module.hashlib, "sha256", unexpected("sha256"))
    monkeypatch.setattr(module, "encode_renderer_frame", unexpected("frame"))

    with pytest.raises(module.RendererProtocolError) as captured:
        module.build_renderer_request(model_bytes, spec_bytes, _resources())

    assert calls == []
    error = captured.value
    assert error.__cause__ is None
    assert error.__context__ is None
    assert "model" not in str(error).lower()
    assert "spec" not in str(error).lower()


def test_renderer_runtime_stays_internal_and_never_imports_subprocess() -> None:
    loaded, module = _load_runtime_module()

    assert loaded is True
    assert module is not None
    assert "subprocess" not in module.__dict__
    assert not hasattr(patent_analysis, "build_renderer_request")
    assert not hasattr(patent_analysis, "run_bound_renderer")


@pytest.mark.parametrize(
    "case",
    _VISUAL_CORPUS["semantic_cases"],
    ids=lambda case: case["id"],
)
def test_shared_semantic_corpus_is_classified_by_authoritative_python(case: dict[str, Any]) -> None:
    model = _apply_semantic_operation(case["operation"])

    if case["python_valid"]:
        assert validate_chart_model(model) == model
    else:
        with pytest.raises(RenderContractError):
            validate_chart_model(model)


@pytest.mark.parametrize(
    "case",
    _VISUAL_CORPUS["numeric_cases"],
    ids=lambda case: case["id"],
)
def test_shared_numeric_lexemes_are_classified_by_authoritative_python(
    case: dict[str, Any],
) -> None:
    raw = f'{{"value":{case["lexeme"]}}}'.encode("ascii")

    if case["python_accepts"]:
        assert parse_canonical_json_bytes(raw, max_bytes=8192)["value"] is not None
    else:
        with pytest.raises(CanonicalJsonError):
            parse_canonical_json_bytes(raw, max_bytes=8192)


def test_bound_runner_calls_the_injected_launcher_once_and_decodes_through_task3() -> None:
    loaded, module = _load_runtime_module()
    assert loaded is True and module is not None
    resources = _resources()
    frame = b"exact-frame"
    calls: list[bytes] = []

    def launcher(received: bytes) -> _ProcessResult:
        calls.append(received)
        return _ProcessResult(
            returncode=0,
            stdout=_success_response(resources.runtime, "<svg>正</svg>\n".encode()),
            stderr=b"",
        )

    assert module.run_bound_renderer(
        launcher, frame, resources.runtime
    ) == "<svg>正</svg>\n".encode()
    assert calls == [frame]
    assert calls[0] is frame


@pytest.mark.parametrize(
    ("result", "secret"),
    [
        (_ProcessResult(7, b"", b"secret-label C:\\private\\case.csv"), "secret-label"),
        (_ProcessResult(0, b"x" * (MAX_RENDERER_STDOUT_BYTES + 1), b""), "x" * 32),
        (_ProcessResult(0, b"{}\n", b"e" * (64 * 1024 + 1)), "e" * 32),
    ],
)
def test_process_failures_and_pipe_limits_raise_only_the_fixed_safe_runtime_error(
    result: _ProcessResult,
    secret: str,
) -> None:
    loaded, module = _load_runtime_module()
    assert loaded is True and module is not None
    calls = 0

    def launcher(_frame: bytes) -> _ProcessResult:
        nonlocal calls
        calls += 1
        return result

    frame = b"raw-" + b"model-spec"
    with pytest.raises(module.RendererRuntimeError) as captured:
        module.run_bound_renderer(launcher, frame, _resources().runtime)

    assert calls == 1
    error = captured.value
    assert error.code == "renderer.unavailable"
    assert error.safe_message == "Trusted renderer is unavailable"
    assert error.__cause__ is None
    assert error.__context__ is None
    surfaces = "\n".join(
        [str(error), repr(error), "".join(traceback.format_exception(error)), repr(vars(error))]
    )
    assert secret not in surfaces
    assert "raw-model-spec" not in surfaces
    # Tracebacks may legitimately contain a checkout named "*-private".
    # Reject the actual untrusted input path, not a word in the source path.
    input_path = "C:\\private\\case.csv"
    assert input_path not in surfaces
    assert repr(input_path)[1:-1] not in surfaces


def test_launcher_exception_and_invalid_stdout_do_not_retain_payload_or_exception_context() -> None:
    loaded, module = _load_runtime_module()
    assert loaded is True and module is not None

    def exploding(_frame: bytes) -> _ProcessResult:
        raise ValueError("sensitive label and C:\\private\\input.json")

    frame = b"raw-" + b"model"
    with pytest.raises(module.RendererRuntimeError) as launcher_error:
        module.run_bound_renderer(exploding, frame, _resources().runtime)
    assert launcher_error.value.__cause__ is None
    assert launcher_error.value.__context__ is None
    assert "sensitive" not in "".join(traceback.format_exception(launcher_error.value))

    invalid_stdout = b'{"' + b'private-payload-canary":"payload"}\n'

    def invalid_response(_frame: bytes) -> _ProcessResult:
        return _ProcessResult(0, invalid_stdout, b"")

    with pytest.raises(Exception) as protocol_error:
        module.run_bound_renderer(invalid_response, frame, _resources().runtime)
    assert type(protocol_error.value).__name__ == "RendererProtocolError"
    assert protocol_error.value.__cause__ is None
    assert protocol_error.value.__context__ is None
    assert "private-payload-canary" not in "\n".join(
        [
            str(protocol_error.value),
            repr(protocol_error.value),
            "".join(traceback.format_exception(protocol_error.value)),
            repr(vars(protocol_error.value)),
        ]
    )


@pytest.mark.parametrize(
    ("code", "message"),
    [
        ("protocol.invalid", "Renderer protocol is invalid"),
        ("payload.too_large", "Renderer payload is too large"),
        ("digest.mismatch", "Renderer payload digest does not match"),
        ("schema.invalid", "Renderer input was rejected"),
        ("runtime.mismatch", "Renderer runtime does not match"),
        ("render.failed", "Renderer failed"),
    ],
)
def test_all_declared_failures_remain_fixed_safe_task3_errors(code: str, message: str) -> None:
    loaded, module = _load_runtime_module()
    assert loaded is True and module is not None
    binding = _resources().runtime

    with pytest.raises(RendererDeclaredError) as captured:
        module.run_bound_renderer(
            lambda _frame: _ProcessResult(
                0,
                _failure_response(binding, code, message),
                b"untrusted stderr",
            ),
            b"frame",
            binding,
        )

    error = captured.value
    assert (error.code, error.safe_message) == (code, message)
    assert error.__cause__ is None
    assert error.__context__ is None
    assert "stderr" not in "\n".join(
        [str(error), repr(error), "".join(traceback.format_exception(error)), repr(vars(error))]
    )
