"""Pinned advanced-family resources, sharing the existing verified file reader."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from patent_analysis._render_canonical import canonical_json_bytes, sha256_bytes
from patent_analysis.advanced_bundle import decode_advanced_bundle
from patent_analysis.advanced_presentation import ADVANCED_RENDER_PROFILE_ID
from patent_analysis.advanced_renderer_build import ADVANCED_BUILD
from patent_analysis.renderer_resources import (
    MAX_RENDERER_BOOTSTRAP_BYTES,
    MAX_RENDERER_BUILD_MANIFEST_BYTES,
    MAX_RENDERER_BUNDLE_BYTES,
    MAX_RENDERER_SCHEMA_BYTES,
    RendererProtocolError,
    RendererResources,
    RendererRuntimeBinding,
    _parse_manifest,
    _read_verified_resource,
    _renderer_resource_root,
)


def load_verified_advanced_renderer_resources() -> RendererResources:
    """Fail closed for unbuilt, replaced, oversized or incompatible resources."""
    pins = ADVANCED_BUILD
    if pins is None:
        raise RendererProtocolError()
    root = _renderer_resource_root()
    try:
        manifest_bytes = _read_verified_resource(
            root / "advanced-renderer-build-manifest.json", MAX_RENDERER_BUILD_MANIFEST_BYTES
        )
        bootstrap = _read_verified_resource(
            root / "advanced-bootstrap.js", MAX_RENDERER_BOOTSTRAP_BYTES
        )
        archive = _read_verified_resource(
            root / "advanced-renderer.bundle.js.gz", MAX_RENDERER_BUNDLE_BYTES
        )
        if any(
            sha256_bytes(raw) != pins[key]
            for raw, key in (
                (manifest_bytes, "manifest_sha256"),
                (bootstrap, "bootstrap_sha256"),
                (archive, "archive_sha256"),
            )
        ):
            raise ValueError("advanced resource digest")
        bundle = decode_advanced_bundle(archive, pins["bundle_sha256"])
        manifest = _parse_manifest(manifest_bytes)
        if (
            manifest.build_tool_version != "1.0.0"
            or manifest.bootstrap_sha256 != pins["bootstrap_sha256"]
            or manifest.renderer_bundle_sha256 != pins["bundle_sha256"]
        ):
            raise ValueError("advanced manifest binding")
        import json

        digest = sha256_bytes(canonical_json_bytes(json.loads(manifest_bytes)))
        if digest != pins["build_digest"]:
            raise ValueError("advanced build digest")
        for name in (
            "advanced-chart-model-v1.schema.json",
            "advanced-render-spec-v1.schema.json",
            "advanced-renderer-response.schema.json",
        ):
            path = Path(str(files("patent_analysis").joinpath("schemas", name)))
            raw = _read_verified_resource(path, MAX_RENDERER_SCHEMA_BYTES)
            if sha256_bytes(raw) != pins[name]:
                raise ValueError("advanced schema binding")
        runtime = RendererRuntimeBinding(
            node_version="24.22.1",
            echarts_version="6.1.0",
            renderer_build_digest=digest,
            render_profile_id=ADVANCED_RENDER_PROFILE_ID,
        )
        return RendererResources(
            manifest=manifest,
            manifest_bytes=manifest_bytes,
            bootstrap_bytes=bootstrap,
            bundle_bytes=bundle,
            renderer_build_digest=digest,
            runtime=runtime,
        )
    except (OSError, KeyError, TypeError, ValueError, RecursionError):
        raise RendererProtocolError() from None
