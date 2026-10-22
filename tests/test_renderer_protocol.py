from __future__ import annotations

import base64
import hashlib
import importlib
import json
import struct
import traceback
from pathlib import Path

import pytest

_CORPUS = json.loads(
    (Path(__file__).parent / "fixtures" / "renderer-protocol-cases.json").read_text(
        encoding="utf-8"
    )
)


def _protocol_module():
    try:
        return importlib.import_module("patent_analysis.renderer_protocol")
    except ModuleNotFoundError:
        pytest.fail("missing renderer protocol interfaces", pytrace=False)


def _runtime(module):
    return module.RendererRuntimeBinding(
        node_version="22.23.4",
        echarts_version="6.1.0",
        renderer_build_digest="1b6378efd6155f306f74c79199e69ba2613a5f72aa52ee97a1c1514417cdc1a9",
        render_profile_id="ranking-svg-ja-jp-node22-echarts6.v1",
    )


def _request() -> dict[str, object]:
    chart = b'{"chart_model_version":"1.0.0"}'
    spec = b'{"render_spec_version":"1.0.0"}'
    return {
        "protocol_version": "1.0.0",
        "chart_model_b64": base64.b64encode(chart).decode("ascii"),
        "chart_model_sha256": hashlib.sha256(chart).hexdigest(),
        "render_spec_b64": base64.b64encode(spec).decode("ascii"),
        "render_spec_sha256": hashlib.sha256(spec).hexdigest(),
    }


def _response_bytes(runtime, *, svg: bytes = b"<svg/>") -> bytes:
    value = {
        "protocol_version": "1.0.0",
        "ok": True,
        "runtime": {
            "node_version": runtime.node_version,
            "echarts_version": runtime.echarts_version,
            "renderer_build_digest": runtime.renderer_build_digest,
            "render_profile_id": runtime.render_profile_id,
        },
        "svg_b64": base64.b64encode(svg).decode("ascii"),
    }
    return json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii") + b"\n"


def _failure_bytes(runtime, code: str, message: str) -> bytes:
    value = {
        "protocol_version": "1.0.0",
        "ok": False,
        "runtime": {
            "node_version": runtime.node_version,
            "echarts_version": runtime.echarts_version,
            "renderer_build_digest": runtime.renderer_build_digest,
            "render_profile_id": runtime.render_profile_id,
        },
        "error": {"code": code, "message": message},
    }
    return json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii") + b"\n"


def test_renderer_protocol_interfaces_and_exact_constants_exist() -> None:
    module = _protocol_module()

    assert module.RENDERER_FRAME_MAGIC == b"PARSVG01"
    assert module.RENDERER_FRAME_VERSION == 1
    assert module.RENDERER_FRAME_HEADER_BYTES == 20
    assert module.MAX_RENDERER_BUNDLE_BYTES == 4 * 1024 * 1024
    assert module.MAX_RENDERER_REQUEST_JSON_BYTES == 3 * 1024 * 1024
    assert module.MAX_RENDERER_FRAME_BYTES == 7 * 1024 * 1024
    assert module.MAX_RENDERER_STDOUT_BYTES == 12 * 1024 * 1024
    assert module.MAX_RENDERER_SVG_BYTES == 8 * 1024 * 1024


def test_frame_is_exact_big_endian_header_and_canonical_five_field_request() -> None:
    module = _protocol_module()
    bundle = b"verified-bundle"

    frame = module.encode_renderer_frame(bundle, _request())

    assert frame[:20] == struct.pack(
        ">8sIII", b"PARSVG01", 1, len(bundle), len(frame) - 20 - len(bundle)
    )
    assert frame[20 : 20 + len(bundle)] == bundle
    request_bytes = frame[20 + len(bundle) :]
    assert request_bytes == (
        b'{"chart_model_b64":"eyJjaGFydF9tb2RlbF92ZXJzaW9uIjoiMS4wLjAifQ==",'
        b'"chart_model_sha256":"72f326804c6a5b276f6225ba543b4528b68c48ce5e74b5db1430e613eed0b3eb",'
        b'"protocol_version":"1.0.0",'
        b'"render_spec_b64":"eyJyZW5kZXJfc3BlY192ZXJzaW9uIjoiMS4wLjAifQ==",'
        b'"render_spec_sha256":"34a2899f99d9e7ecdf32d4c0f961d30f79ce339c924cb18f07d3d0c8d644aff9"}'
    )


@pytest.mark.parametrize(
    ("bundle_length", "request_length", "accepted"),
    [
        (case["bundle_length"], case["request_length"], case["valid"])
        for case in _CORPUS["frame_boundaries"]
    ],
)
def test_frame_boundary_arithmetic_is_exact(
    bundle_length: int,
    request_length: int,
    accepted: bool,
) -> None:
    module = _protocol_module()

    if accepted:
        frame = module._encode_frame_parts(b"b" * bundle_length, b"r" * request_length)
        assert len(frame) == 20 + bundle_length + request_length
    else:
        with pytest.raises(module.RendererProtocolError):
            module._encode_frame_parts(b"b" * bundle_length, b"r" * request_length)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing-field",
        "extra-field",
        "bool-version",
        "invalid-base64",
        "noncanonical-base64",
        "chart-digest-mismatch",
        "spec-digest-mismatch",
    ],
)
def test_request_mutations_fail_closed_without_retention(mutation: str) -> None:
    module = _protocol_module()
    request = _request()
    secret = "TASK3-REQUEST-SECRET"
    if mutation == "missing-field":
        request.pop("render_spec_sha256")
    elif mutation == "extra-field":
        request["secret"] = secret
    elif mutation == "bool-version":
        request["protocol_version"] = True
    elif mutation == "invalid-base64":
        request["chart_model_b64"] = "!!!!"
    elif mutation == "noncanonical-base64":
        request["chart_model_b64"] = request["chart_model_b64"].rstrip("=")
    elif mutation == "chart-digest-mismatch":
        request["chart_model_sha256"] = "0" * 64
    else:
        request["render_spec_sha256"] = "0" * 64

    with pytest.raises(module.RendererProtocolError) as caught:
        module.encode_renderer_frame(b"bundle", request)

    rendered = "".join(traceback.format_exception(caught.value))
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert secret not in rendered
    assert secret not in repr(caught.value.__dict__)


def test_success_response_returns_immutable_svg_bytes() -> None:
    module = _protocol_module()
    runtime = _runtime(module)

    svg = module.decode_renderer_response(_response_bytes(runtime), runtime)

    assert svg == b"<svg/>"
    assert type(svg) is bytes


def test_success_response_accepts_exact_8_mib_and_rejects_one_over() -> None:
    module = _protocol_module()
    runtime = _runtime(module)
    exact = b"x" * (8 * 1024 * 1024)
    assert module.decode_renderer_response(_response_bytes(runtime, svg=exact), runtime) == exact
    with pytest.raises(module.RendererProtocolError):
        module.decode_renderer_response(_response_bytes(runtime, svg=exact + b"x"), runtime)


def test_stdout_accepts_exact_12_mib_parse_attempt_and_rejects_one_over() -> None:
    module = _protocol_module()
    runtime = _runtime(module)
    valid = _response_bytes(runtime)
    exact = valid[:-1] + b" " * (12 * 1024 * 1024 - len(valid)) + b"\n"
    with pytest.raises(module.RendererProtocolError):
        module.decode_renderer_response(exact, runtime)
    with pytest.raises(module.RendererProtocolError):
        module.decode_renderer_response(exact + b"x", runtime)


def test_runtime_mismatch_is_rejected_before_svg_decode() -> None:
    module = _protocol_module()
    runtime = _runtime(module)
    value = json.loads(_response_bytes(runtime))
    value["runtime"]["node_version"] = "22.19.1"
    value["svg_b64"] = "TASK3-INVALID-BASE64"
    raw = json.dumps(value, separators=(",", ":")).encode("ascii") + b"\n"

    with pytest.raises(module.RendererProtocolError) as caught:
        module.decode_renderer_response(raw, runtime)

    assert caught.value.code == "renderer.protocol_invalid"
    assert "TASK3" not in repr(caught.value)


@pytest.mark.parametrize(
    "payload",
    [
        b"\xff",
        b'{"a":"\x00"}',
        b"[]",
        b'{"a":1,"a":2}',
    ],
)
def test_lexical_preflight_rejects_invalid_bytes_and_nonclosed_object(payload: bytes) -> None:
    module = _protocol_module()
    preflight = getattr(module, "_preflight_renderer_json", None)
    assert callable(preflight), "missing renderer stdout lexical preflight"

    with pytest.raises(module._ProtocolViolation):
        preflight(payload)


def test_lexical_preflight_enforces_exact_depth_budget() -> None:
    module = _protocol_module()
    preflight = getattr(module, "_preflight_renderer_json", None)
    assert callable(preflight), "missing renderer stdout lexical preflight"
    exact_depth, one_over_depth = _CORPUS["lexical_boundaries"]["depth"]
    exact = b'{"a":' + b"[" * (exact_depth - 1) + b"0" + b"]" * (exact_depth - 1) + b"}"
    one_over = (
        b'{"a":'
        + b"[" * (one_over_depth - 1)
        + b"0"
        + b"]" * (one_over_depth - 1)
        + b"}"
    )

    preflight(exact)
    with pytest.raises(module._ProtocolViolation):
        preflight(one_over)


def test_lexical_preflight_enforces_exact_token_budget() -> None:
    module = _protocol_module()
    preflight = getattr(module, "_preflight_renderer_json", None)
    assert callable(preflight), "missing renderer stdout lexical preflight"
    exact_tokens, _one_over_tokens = _CORPUS["lexical_boundaries"]["tokens"]
    exact = b'{"a":[' + b",".join([b"null"] * (exact_tokens - 3)) + b"]}"
    one_over = exact[:-2] + b",null]}"

    preflight(exact)
    with pytest.raises(module._ProtocolViolation):
        preflight(one_over)


def test_lexical_preflight_enforces_exact_numeric_lexeme_budget() -> None:
    module = _protocol_module()
    preflight = getattr(module, "_preflight_renderer_json", None)
    assert callable(preflight), "missing renderer stdout lexical preflight"

    exact_bytes, one_over_bytes = _CORPUS["lexical_boundaries"]["numeric_lexeme_bytes"]
    preflight(b'{"a":1' + b"0" * (exact_bytes - 1) + b"}")
    with pytest.raises(module._ProtocolViolation):
        preflight(b'{"a":1' + b"0" * (one_over_bytes - 1) + b"}")


def test_lexical_preflight_enforces_exact_decoded_string_budget() -> None:
    module = _protocol_module()
    preflight = getattr(module, "_preflight_renderer_json", None)
    assert callable(preflight), "missing renderer stdout lexical preflight"
    exact_points, one_over_points = _CORPUS["lexical_boundaries"][
        "decoded_non_payload_code_points"
    ]
    exact = b'{"a":"' + b"x" * (exact_points - 1) + b'"}'
    one_over = b'{"a":"' + b"x" * (one_over_points - 1) + b'"}'

    preflight(exact)
    with pytest.raises(module._ProtocolViolation):
        preflight(one_over)


def test_truncated_json_with_required_lf_is_rejected_before_json_load(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _protocol_module()
    runtime = _runtime(module)
    monkeypatch.setattr(
        module.json,
        "loads",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("json.loads reached for truncated input")
        ),
    )

    with pytest.raises(module.RendererProtocolError):
        module.decode_renderer_response(_CORPUS["truncated_with_lf"].encode("ascii"), runtime)


@pytest.mark.parametrize(
    "mutation",
    _CORPUS["invalid_response_mutations"],
)
def test_noncanonical_or_multiple_stdout_objects_are_rejected(mutation: str) -> None:
    module = _protocol_module()
    runtime = _runtime(module)
    raw = _response_bytes(runtime)
    text = raw[:-1].decode("ascii")
    mutations = {
        "bom": b"\xef\xbb\xbf" + raw,
        "leading_whitespace": b" " + raw,
        "missing_lf": raw[:-1],
        "crlf": raw[:-1] + b"\r\n",
        "trailing_lf": raw + b"\n",
        "trailing_data": raw + b"x",
        "duplicate_key": (
            text.replace('{"protocol_version":', '{"ok":true,"protocol_version":', 1).encode()
            + b"\n"
        ),
        "nan": text.replace('"svg_b64":"PHN2Zy8+"', '"svg_b64":NaN').encode() + b"\n",
        "infinity": text.replace('"svg_b64":"PHN2Zy8+"', '"svg_b64":Infinity').encode() + b"\n",
        "alternate_order": (
            text.replace(
                '{"protocol_version":"1.0.0","ok":true',
                '{"ok":true,"protocol_version":"1.0.0"',
            ).encode()
            + b"\n"
        ),
        "alternate_spacing": text.replace(":", ": ", 1).encode() + b"\n",
        "alternate_escape": text.replace("1.0.0", "1.0.\\u0030", 1).encode() + b"\n",
        "multiple_objects": raw + raw,
        "unknown_field": (text[:-1] + ',"extra":true}').encode() + b"\n",
    }

    with pytest.raises(module.RendererProtocolError):
        module.decode_renderer_response(mutations[mutation], runtime)


@pytest.mark.parametrize(
    ("code", "message"),
    _CORPUS["failure_pairs"],
)
def test_all_six_declared_failure_pairs_raise_fixed_typed_error(code: str, message: str) -> None:
    module = _protocol_module()
    runtime = _runtime(module)

    with pytest.raises(module.RendererDeclaredError) as caught:
        module.decode_renderer_response(_failure_bytes(runtime, code, message), runtime)

    error = caught.value
    assert error.code == code
    assert error.safe_message == message
    assert error.__cause__ is None
    assert error.__context__ is None
    assert set(error.__dict__) == {"code", "safe_message"}


def test_unapproved_failure_pair_and_strict_base64_are_rejected() -> None:
    module = _protocol_module()
    runtime = _runtime(module)
    with pytest.raises(module.RendererProtocolError):
        module.decode_renderer_response(_failure_bytes(runtime, "render.failed", "secret"), runtime)
    raw = _response_bytes(runtime).replace(b"PHN2Zy8+", b"PHN2Zy8")
    with pytest.raises(module.RendererProtocolError):
        module.decode_renderer_response(raw, runtime)


def test_declared_error_cannot_be_constructed_directly_with_arbitrary_data() -> None:
    module = _protocol_module()
    secret = "TASK3-DECLARED-ERROR-SECRET"

    with pytest.raises(module.RendererProtocolError) as caught:
        module.RendererDeclaredError(secret, secret)

    rendered = "".join(traceback.format_exception(caught.value))
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert secret not in repr(caught.value)
    assert secret not in repr(caught.value.__dict__)
    assert secret not in rendered


@pytest.mark.parametrize(
    ("field", "bad_pad_bits"),
    [
        ("chart_model_b64", _CORPUS["bad_pad_bits"][0]),
        ("render_spec_b64", _CORPUS["bad_pad_bits"][1]),
    ],
)
def test_request_schema_and_runtime_reject_nonzero_base64_pad_bits(
    field: str,
    bad_pad_bits: str,
) -> None:
    module = _protocol_module()
    request = _request()
    request[field] = bad_pad_bits

    with pytest.raises(module._ProtocolViolation):
        module._schema_valid(request, "renderer-request.schema.json")
    with pytest.raises(module.RendererProtocolError):
        module.encode_renderer_frame(b"bundle", request)


def test_response_schema_and_runtime_reject_nonzero_base64_pad_bits() -> None:
    module = _protocol_module()
    runtime = _runtime(module)
    value = json.loads(_response_bytes(runtime))
    value["svg_b64"] = _CORPUS["bad_pad_bits"][2]
    raw = json.dumps(value, separators=(",", ":")).encode("ascii") + b"\n"

    with pytest.raises(module._ProtocolViolation):
        module._schema_valid(value, "renderer-response.schema.json")
    with pytest.raises(module.RendererProtocolError):
        module.decode_renderer_response(raw, runtime)


def test_schema_resources_are_draft_2020_12_and_closed() -> None:
    package = Path(importlib.import_module("patent_analysis").__file__).parent
    expected_ids = {
        "renderer-build-manifest.schema.json": (
            "urn:patent-analysis:renderer-build-manifest:1.0.0"
        ),
        "renderer-request.schema.json": "urn:patent-analysis:renderer-request:1.0.0",
        "renderer-response.schema.json": "urn:patent-analysis:renderer-response:1.0.0",
    }
    for name, expected_id in expected_ids.items():
        schema_path = package / "schemas" / name
        assert schema_path.is_file(), f"missing renderer schema interface: {name}"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["$id"] == expected_id
        assert schema["additionalProperties"] is False
        stack = [schema]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                if current.get("type") == "object":
                    assert current.get("additionalProperties") is False
                stack.extend(current.values())
            elif isinstance(current, list):
                stack.extend(current)
