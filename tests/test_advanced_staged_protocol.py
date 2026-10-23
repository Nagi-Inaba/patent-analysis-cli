"""Real staged bootstrap/bundle integration, not Windows public-adapter acceptance.

These build-workspace tests never change the checked-in activation record or the
Windows launcher guard. The child receives only the verified self-contained
bundle and framed request, from an otherwise empty working directory.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from patent_analysis import api
from patent_analysis._render_canonical import canonical_json_bytes
from patent_analysis.advanced_bundle import decode_advanced_bundle
from patent_analysis.advanced_presentation import ADVANCED_RENDER_PROFILE_ID
from patent_analysis.chart_models.advanced import (
    build_advanced_chart_model,
    build_advanced_render_spec,
)
from patent_analysis.renderer_protocol import RendererDeclaredError, encode_renderer_frame
from patent_analysis.renderer_resources import RendererRuntimeBinding
from patent_analysis.renderer_runtime import run_bound_renderer

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "src" / "patent_analysis" / "renderer"
EXAMPLES = ROOT / "examples" / "advanced"


@pytest.fixture(scope="module")
def staged_runtime():
    candidate = RESOURCES / "advanced-renderer-candidate-pins.json"
    if not candidate.is_file():
        pytest.skip("requires explicit advanced --stage-only build")
    node = shutil.which("node")
    if node is None:
        pytest.skip("requires Node 24.22.1 x64 in the build workspace")
    probe = subprocess.run(
        [node, "-p", "process.versions.node + '/' + process.arch"],
        capture_output=True, text=True, timeout=10, check=True,
    )
    if probe.stdout.strip() not in (
        {"24.22.1/x64", "24.22.1/arm64"} if sys.platform == "darwin" else {"24.22.1/x64"}
    ):
        pytest.skip("requires exact Node 24.22.1 x64")
    pins = json.loads(candidate.read_bytes())
    bootstrap = (RESOURCES / "advanced-bootstrap.js").read_bytes()
    archive = (RESOURCES / "advanced-renderer.bundle.js.gz").read_bytes()
    manifest = (RESOURCES / "advanced-renderer-build-manifest.json").read_bytes()
    for value, key in (
        (bootstrap, "bootstrap_sha256"), (archive, "archive_sha256"),
        (manifest, "manifest_sha256"),
    ):
        assert hashlib.sha256(value).hexdigest() == pins[key]
    assert hashlib.sha256(canonical_json_bytes(json.loads(manifest))).hexdigest() == pins[
        "build_digest"
    ]
    bundle = decode_advanced_bundle(archive, pins["bundle_sha256"])
    binding = RendererRuntimeBinding(
        node_version="24.22.1", echarts_version="6.1.0",
        renderer_build_digest=pins["build_digest"], render_profile_id=ADVANCED_RENDER_PROFILE_ID,
    )
    return node, bootstrap.decode("utf-8"), bundle, binding


def _request(analysis_id: str):
    spec = (EXAMPLES / f"{analysis_id.removesuffix('.v1')}.json").read_bytes()
    result = api.run_analysis_csv("patents.csv", spec, allowed_root=EXAMPLES)
    model, _ = build_advanced_chart_model(result, analysis_id=analysis_id)
    model_bytes = canonical_json_bytes(model)
    render_spec = canonical_json_bytes(build_advanced_render_spec())
    return {
        "protocol_version": "1.0.0",
        "chart_model_b64": base64.b64encode(model_bytes).decode("ascii"),
        "chart_model_sha256": hashlib.sha256(model_bytes).hexdigest(),
        "render_spec_b64": base64.b64encode(render_spec).decode("ascii"),
        "render_spec_sha256": hashlib.sha256(render_spec).hexdigest(),
    }


def _run(staged_runtime, frame: bytes, directory: Path):
    node, bootstrap, _, binding = staged_runtime
    # No NODE_OPTIONS, NODE_PATH or caller-supplied module paths are inherited.
    environment = {
        key: os.environ[key]
        for key in ("SystemRoot", "WINDIR", "TEMP", "TMP") if key in os.environ
    }
    return run_bound_renderer(
        lambda request: subprocess.run(
            [node, "--permission", "--max-old-space-size=192", "--disable-proto=throw",
             "--eval", bootstrap],
            input=request, capture_output=True, timeout=10, check=False,
            cwd=directory, env=environment,
        ),
        frame, binding,
    )


def test_staged_bootstrap_rejects_invalid_frame(staged_runtime, tmp_path):
    with pytest.raises(RendererDeclaredError) as error:
        _run(staged_runtime, b"not-a-frame", tmp_path)
    assert error.value.code == "protocol.invalid"
    assert list(tmp_path.iterdir()) == []


def test_staged_bootstrap_rejects_changed_bundle(staged_runtime, tmp_path):
    frame = bytearray(encode_renderer_frame(staged_runtime[2], _request("citation.v1")))
    frame[20] ^= 1  # Valid framing, but the bundle no longer matches its fixed pin.
    with pytest.raises(RendererDeclaredError) as error:
        _run(staged_runtime, bytes(frame), tmp_path)
    assert error.value.code == "digest.mismatch"
    assert list(tmp_path.iterdir()) == []


def test_staged_renderer_rejects_incompatible_profile(staged_runtime, tmp_path):
    request = _request("citation.v1")
    spec = json.loads(base64.b64decode(request["render_spec_b64"]))
    spec["render_profile_id"] = "points-svg-ja-jp-node24-echarts6.v1"
    raw = canonical_json_bytes(spec)
    request["render_spec_b64"] = base64.b64encode(raw).decode("ascii")
    request["render_spec_sha256"] = hashlib.sha256(raw).hexdigest()
    frame = encode_renderer_frame(staged_runtime[2], request)
    with pytest.raises(RendererDeclaredError) as error:
        _run(staged_runtime, frame, tmp_path)
    assert error.value.code == "schema.invalid"
    assert list(tmp_path.iterdir()) == []
