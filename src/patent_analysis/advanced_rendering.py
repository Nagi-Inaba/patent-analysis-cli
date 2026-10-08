"""Shared trusted-local SVG entrypoint for the ten closed advanced marks.

Analysis is not recalculated here. The legacy frame, launcher, SVG validation,
publication and error contracts are reused; unsupported hosts remain unsupported.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from patent_analysis._render_canonical import canonical_json_bytes, sha256_bytes
from patent_analysis.advanced_presentation import get_advanced_presentation
from patent_analysis.advanced_renderer_resources import load_verified_advanced_renderer_resources
from patent_analysis.chart_models.advanced import (
    build_advanced_chart_model,
    build_advanced_render_spec,
)
from patent_analysis.local_renderer import (
    LocalRendererError,
    launch_trusted_node,
    require_windows_x64,
    resolve_node_executable,
    validate_local_directory,
)
from patent_analysis.render_errors import RenderError, _make_render_error
from patent_analysis.renderer_protocol import RendererDeclaredError
from patent_analysis.renderer_runtime import build_renderer_request, run_bound_renderer


def render_advanced_svg(
    analysis_document: bytes,
    *,
    analysis_id: str,
    mark: str | None = None,
    overlay_document: bytes | None = None,
    output_directory: str | Path,
    node_executable: str | Path | None = None,
) -> dict[str, Any]:
    # Lazy import preserves the existing public facade/import graph.
    from patent_analysis.rendering import (
        MAX_ANALYSIS_DOCUMENT_BYTES,
        MAX_PUBLISHED_SVG_BYTES,
        _parse_document,
        _publish_svg,
    )

    if overlay_document is not None:
        raise _make_render_error("render.invalid")
    if type(analysis_document) is not bytes or len(analysis_document) > MAX_ANALYSIS_DOCUMENT_BYTES:
        raise _make_render_error("input.invalid")
    document = _parse_document(analysis_document, MAX_ANALYSIS_DOCUMENT_BYTES)
    try:
        definition = get_advanced_presentation(analysis_id, mark)
        model, receipt = build_advanced_chart_model(
            document, analysis_id=analysis_id, mark=definition.mark
        )
        spec = build_advanced_render_spec()
        model_bytes, spec_bytes = canonical_json_bytes(model), canonical_json_bytes(spec)
        if sha256_bytes(model_bytes) != receipt["chart_model_sha256"]:
            raise ValueError("model binding")
    except (TypeError, ValueError, RecursionError):
        raise _make_render_error("render.invalid") from None
    try:
        require_windows_x64()
    except LocalRendererError:
        raise _make_render_error("renderer.unavailable") from None
    try:
        output = validate_local_directory(output_directory)
    except LocalRendererError:
        raise _make_render_error("output.conflict") from None
    try:
        node = resolve_node_executable(node_executable)
        resources = load_verified_advanced_renderer_resources()
        frame = build_renderer_request(model_bytes, spec_bytes, resources)
        svg = run_bound_renderer(
            lambda request: launch_trusted_node(node, resources.bootstrap_bytes, request),
            frame,
            resources.runtime,
            accessibility_model=model_bytes,
        )
    except RendererDeclaredError as error:
        code = "render.invalid" if error.code == "schema.invalid" else "renderer.unavailable"
        raise _make_render_error(code) from None
    except RenderError:
        raise
    except Exception:
        raise _make_render_error("renderer.unavailable") from None
    if type(svg) is not bytes or not svg or len(svg) > MAX_PUBLISHED_SVG_BYTES:
        raise _make_render_error("renderer.unavailable")
    svg_hash = sha256_bytes(svg)
    artifact_id = sha256_bytes(
        canonical_json_bytes(
            {
                "chart_model_sha256": sha256_bytes(model_bytes),
                "render_spec_sha256": sha256_bytes(spec_bytes),
                "renderer_build_digest": resources.renderer_build_digest,
                "svg_sha256": svg_hash,
            }
        )
    )
    filename = f"{definition.mark.removesuffix('.v1')}-{artifact_id}.svg"
    status = _publish_svg(output, filename, svg)
    return {
        "render_contract_version": "1.0.0",
        "ok": True,
        "status": status,
        "mark": definition.mark,
        "artifact_id": artifact_id,
        "svg": filename,
        "svg_sha256": svg_hash,
        "renderer_build_digest": resources.renderer_build_digest,
    }
