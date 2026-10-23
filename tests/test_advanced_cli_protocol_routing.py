"""CLI dispatch doubles and real closed-response decoding; not Windows SVG E2E."""
from __future__ import annotations

import base64
import json

import pytest

from patent_analysis import api, cli
from patent_analysis.advanced_presentation import (
    ADVANCED_PRESENTATIONS,
    ADVANCED_RENDER_PROFILE_ID,
)
from patent_analysis.render_errors import RenderError
from patent_analysis.renderer_protocol import RendererDeclaredError, decode_renderer_response
from patent_analysis.renderer_resources import RendererProtocolError, RendererRuntimeBinding

PRESENTATIONS = tuple(ADVANCED_PRESENTATIONS.values())
ARGS = ["render", "--analysis", "input.json", "--output", "output", "--json"]
SVG = b'<svg xmlns="http://www.w3.org/2000/svg"></svg>'


@pytest.mark.parametrize("presentation", PRESENTATIONS, ids=lambda p: p.analysis_id)
def test_unavailable_advanced_marks_are_not_advertised_or_read(monkeypatch, capsys, presentation):
    monkeypatch.setattr(cli, "advanced_marks_for", lambda analysis_id: ())
    parser = cli._build_parser()
    subparsers = next(action for action in parser._actions if hasattr(action, "choices")
                     and isinstance(action.choices, dict) and "render" in action.choices)
    render_parser = subparsers.choices["render"]
    mark_action = next(action for action in render_parser._actions if action.dest == "render_mark")
    assert presentation.mark not in mark_action.choices
    def must_not_read(*args, **kwargs):
        pytest.fail("An unavailable mark must be rejected before reading input")

    monkeypatch.setattr(cli, "_read_render_source", must_not_read)
    code = cli.main([*ARGS, "--mark", presentation.mark])
    assert code == cli.EXIT_USAGE_ERROR
    assert json.loads(capsys.readouterr().out)["error"]["code"] == "usage.invalid"


@pytest.mark.parametrize("variant", [[], {}, ["network"]])
def test_malformed_variant_returns_safe_error(monkeypatch, capsys, tmp_path, variant):
    raw = json.dumps({"result_variant": variant}).encode()
    analysis = tmp_path / "input.json"
    analysis.write_bytes(raw)
    output = tmp_path / "must-not-be-created"
    with pytest.raises(RenderError) as rejected:
        api.render_analysis_svg(raw, output_directory=output)
    assert rejected.value.code == "render.invalid"
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))
    assert cli.main([
        "render", "--analysis", analysis.name, "--output", str(output), "--json",
    ]) == cli.EXIT_INVALID_OPERATION_PLAN
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out)["error"] == rejected.value.as_dict()
    assert analysis.read_bytes() == raw and not output.exists()


def _runtime():
    return RendererRuntimeBinding(
        node_version="24.22.1", echarts_version="6.1.0",
        renderer_build_digest="a" * 64, render_profile_id=ADVANCED_RENDER_PROFILE_ID,
    )


def _response(*, error=None):
    runtime = _runtime()
    response = {"protocol_version": "1.0.0", "ok": error is None, "runtime": {
        "node_version": runtime.node_version, "echarts_version": runtime.echarts_version,
        "renderer_build_digest": runtime.renderer_build_digest,
        "render_profile_id": runtime.render_profile_id,
    }}
    if error is None:
        response["svg_b64"] = base64.b64encode(SVG).decode("ascii")
    else:
        response["error"] = error
    return response


def _wire(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii") + b"\n"


def test_advanced_response_uses_pinned_schema_and_decodes_svg():
    assert decode_renderer_response(_wire(_response()), _runtime()) == SVG


def test_advanced_declared_error_preserves_fixed_safe_pair():
    value = _response(error={"code": "schema.invalid", "message": "Renderer input was rejected"})
    with pytest.raises(RendererDeclaredError) as raised:
        decode_renderer_response(_wire(value), _runtime())
    assert raised.value.code == "schema.invalid"
    assert raised.value.safe_message == "Renderer input was rejected"


@pytest.mark.parametrize(("field", "value"), [
    ("node_version", "22.20.0"), ("echarts_version", "6.0.0"),
    ("renderer_build_digest", "b" * 64),
    ("render_profile_id", "points-svg-ja-jp-node24-echarts6.v1"),
])
def test_advanced_runtime_binding_is_still_strict(field, value):
    response = _response()
    response["runtime"][field] = value
    with pytest.raises(RendererProtocolError):
        decode_renderer_response(_wire(response), _runtime())


@pytest.mark.parametrize(
    "mutation", ["no-newline", "crlf", "spaces", "duplicate", "base64", "extra"],
)
def test_advanced_wire_guards_are_not_relaxed(mutation):
    response = _response()
    raw = _wire(response)
    if mutation == "no-newline":
        raw = raw[:-1]
    elif mutation == "crlf":
        raw = raw[:-1] + b"\r\n"
    elif mutation == "spaces":
        raw = raw.replace(b'"ok":true', b'"ok": true', 1)
    elif mutation == "duplicate":
        raw = raw.replace(b'"ok":true', b'"ok":true,"ok":true', 1)
    elif mutation == "base64":
        response["svg_b64"] = "not-base64"
        raw = _wire(response)
    else:
        response["extra"] = True
        raw = _wire(response)
    with pytest.raises(RendererProtocolError):
        decode_renderer_response(raw, _runtime())


def test_advanced_declared_error_cannot_leak_arbitrary_message():
    response = _response(error={"code": "schema.invalid", "message": "private input path"})
    with pytest.raises(RendererProtocolError):
        decode_renderer_response(_wire(response), _runtime())
