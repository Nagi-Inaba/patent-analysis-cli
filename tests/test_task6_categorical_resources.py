from __future__ import annotations

import hashlib
import json

import pytest


def test_categorical_renderer_resources_are_pinned_and_separate() -> None:
    from patent_analysis.renderer_resources import (
        PINNED_CATEGORICAL_RENDERER_BOOTSTRAP_SHA256,
        PINNED_CATEGORICAL_RENDERER_BUILD_DIGEST,
        PINNED_CATEGORICAL_RENDERER_BUILD_MANIFEST_SHA256,
        PINNED_CATEGORICAL_RENDERER_BUNDLE_SHA256,
        load_verified_categorical_renderer_resources,
        load_verified_matrix_renderer_resources,
        load_verified_renderer_resources,
    )

    categorical = load_verified_categorical_renderer_resources()
    matrix = load_verified_matrix_renderer_resources()
    ranking = load_verified_renderer_resources()

    assert hashlib.sha256(categorical.bootstrap_bytes).hexdigest() == (
        PINNED_CATEGORICAL_RENDERER_BOOTSTRAP_SHA256
    )
    assert hashlib.sha256(categorical.bundle_bytes).hexdigest() == (
        PINNED_CATEGORICAL_RENDERER_BUNDLE_SHA256
    )
    assert hashlib.sha256(categorical.manifest_bytes).hexdigest() == (
        PINNED_CATEGORICAL_RENDERER_BUILD_MANIFEST_SHA256
    )
    assert categorical.runtime.renderer_build_digest == (
        PINNED_CATEGORICAL_RENDERER_BUILD_DIGEST
    )
    assert categorical.runtime.render_profile_id == (
        "categorical-svg-ja-jp-node22-echarts6.v1"
    )
    assert categorical.runtime.renderer_build_digest not in {
        ranking.runtime.renderer_build_digest,
        matrix.runtime.renderer_build_digest,
    }
    assert categorical.bootstrap_bytes not in {
        ranking.bootstrap_bytes,
        matrix.bootstrap_bytes,
    }
    assert categorical.bundle_bytes not in {
        ranking.bundle_bytes,
        matrix.bundle_bytes,
    }


def test_categorical_response_schema_is_digest_pinned() -> None:
    from patent_analysis.renderer_resources import (
        PINNED_CATEGORICAL_RENDERER_RESPONSE_SCHEMA_SHA256,
        _load_verified_renderer_schema_bytes,
    )

    raw = _load_verified_renderer_schema_bytes(
        "categorical-renderer-response.schema.json"
    )
    assert hashlib.sha256(raw).hexdigest() == (
        PINNED_CATEGORICAL_RENDERER_RESPONSE_SCHEMA_SHA256
    )
    value = json.loads(raw)
    profile = value["$defs"]["runtime"]["properties"]["render_profile_id"]
    assert profile == {"const": "categorical-svg-ja-jp-node22-echarts6.v1"}


def test_renderer_protocol_selects_categorical_response_contract() -> None:
    from patent_analysis.renderer_protocol import (
        RendererDeclaredError,
        decode_renderer_response,
    )
    from patent_analysis.renderer_resources import (
        load_verified_categorical_renderer_resources,
    )

    runtime = load_verified_categorical_renderer_resources().runtime
    raw = json.dumps(
        {
            "protocol_version": "1.0.0",
            "ok": False,
            "runtime": {
                "node_version": runtime.node_version,
                "echarts_version": runtime.echarts_version,
                "renderer_build_digest": runtime.renderer_build_digest,
                "render_profile_id": runtime.render_profile_id,
            },
            "error": {"code": "render.failed", "message": "Renderer failed"},
        },
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii") + b"\n"

    with pytest.raises(RendererDeclaredError) as caught:
        decode_renderer_response(raw, runtime)

    assert caught.value.code == "render.failed"
    assert caught.value.safe_message == "Renderer failed"
