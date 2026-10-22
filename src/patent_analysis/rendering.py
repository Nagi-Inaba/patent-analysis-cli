from __future__ import annotations

import json
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn

from patent_analysis._json_preflight import (
    JsonPreflightError as _InputJsonViolation,
)
from patent_analysis._json_preflight import (
    preflight_json_bytes as _preflight_json_bytes,
)
from patent_analysis._render_canonical import (
    CanonicalJsonError,
    canonical_json_bytes,
    sha256_bytes,
    strict_b64decode,
)
from patent_analysis._render_contracts import RenderContractError
from patent_analysis.chart_model import (
    build_ranking_chart_model,
    build_ranking_render_spec,
)
from patent_analysis.chart_models.composition import (
    COMPOSITION_RENDER_MARKS,
    build_composition_chart_model,
    build_composition_render_spec,
)
from patent_analysis.chart_models.points import (
    POINTS_RENDER_MARKS,
    build_points_chart_model,
    build_points_render_spec,
)
from patent_analysis.chart_models.series import (
    SERIES_RENDER_MARKS,
    build_series_chart_model,
    build_series_render_spec,
)
from patent_analysis.local_renderer import (
    LocalRendererError,
    launch_trusted_node,
    require_supported_platform,
    resolve_node_executable,
    validate_local_directory,
)
from patent_analysis.matrix_chart_model import (
    build_matrix_chart_model,
    build_matrix_render_spec,
)
from patent_analysis.render_errors import RenderError, _make_render_error
from patent_analysis.renderer_protocol import RendererDeclaredError
from patent_analysis.renderer_resources import (
    RendererProtocolError,
    load_verified_categorical_renderer_resources,
    load_verified_matrix_renderer_resources,
    load_verified_points_renderer_resources,
    load_verified_renderer_resources,
)
from patent_analysis.renderer_runtime import (
    RendererRuntimeError,
    build_renderer_request,
    run_bound_renderer,
)

RENDER_CONTRACT_VERSION = "1.0.0"
MAX_ANALYSIS_DOCUMENT_BYTES = 16 * 1024 * 1024
MAX_OVERLAY_DOCUMENT_BYTES = 4 * 1024 * 1024
MAX_PUBLISHED_SVG_BYTES = 8 * 1024 * 1024


class _PublicationViolation(ValueError):
    pass


@dataclass(frozen=True)
class _PreparedRender:
    model_sha256: str
    spec_sha256: str
    model_bytes: bytes
    spec_bytes: bytes


def _raise(code: str) -> NoReturn:
    raise _make_render_error(code) from None


def _closed_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def _reject_constant(_value: str) -> NoReturn:
    raise ValueError


def _parse_json_object(raw: bytes) -> object:
    return json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_closed_object,
        parse_constant=_reject_constant,
    )


def _parse_document(raw: bytes, limit: int) -> dict[str, Any]:
    if type(raw) is not bytes or len(raw) > limit:
        _raise("input.invalid")
    failed = False
    value: Any = None
    try:
        _preflight_json_bytes(raw)
        value = _parse_json_object(raw)
    except (
        _InputJsonViolation,
        UnicodeDecodeError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
        RecursionError,
    ):
        failed = True
    if failed or not isinstance(value, dict):
        _raise("input.invalid")
    return value


def _prepare_render(
    analysis: dict[str, Any],
    overlay: dict[str, Any] | None,
    palette: str | None = None,
) -> _PreparedRender:
    model, receipt = build_ranking_chart_model(analysis, overlay=overlay)
    model_bytes = strict_b64decode(
        receipt["chart_model_bytes"],
        max_decoded_bytes=2 * 1024 * 1024,
    )
    model_sha256 = receipt["chart_model_sha256"]
    if not isinstance(model_sha256, str) or sha256_bytes(model_bytes) != model_sha256:
        raise RenderContractError() from None
    spec = build_ranking_render_spec(row_count=len(model["rows"]), palette=palette)
    spec_bytes = canonical_json_bytes(spec)
    spec_sha256 = sha256_bytes(spec_bytes)
    return _PreparedRender(
        model_sha256=model_sha256,
        spec_sha256=spec_sha256,
        model_bytes=model_bytes,
        spec_bytes=spec_bytes,
    )


def _render_svg(
    prepared: _PreparedRender,
    node_executable: str | os.PathLike[str] | None,
) -> tuple[str, str, str, bytes]:
    node = resolve_node_executable(node_executable)
    resources = load_verified_renderer_resources()
    frame = build_renderer_request(prepared.model_bytes, prepared.spec_bytes, resources)
    svg = run_bound_renderer(
        lambda request: launch_trusted_node(node, resources.bootstrap_bytes, request),
        frame,
        resources.runtime,
        accessibility_model=prepared.model_bytes,
    )
    return (
        prepared.model_sha256,
        prepared.spec_sha256,
        resources.renderer_build_digest,
        svg,
    )


def _probe_final(path: Path, expected: bytes) -> str:
    try:
        before = path.lstat()
    except FileNotFoundError:
        return "missing"
    attributes = getattr(before, "st_file_attributes", 0)
    if (
        not stat.S_ISREG(before.st_mode)
        or stat.S_ISLNK(before.st_mode)
        or bool(attributes & 0x0400)
    ):
        raise _PublicationViolation
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or not os.path.samestat(before, opened):
            raise _PublicationViolation
        actual = stream.read(MAX_PUBLISHED_SVG_BYTES + 1)
        after = path.lstat()
        after_attributes = getattr(after, "st_file_attributes", 0)
        if (
            not stat.S_ISREG(after.st_mode)
            or stat.S_ISLNK(after.st_mode)
            or bool(after_attributes & 0x0400)
            or not os.path.samestat(opened, after)
        ):
            raise _PublicationViolation
    return "equal" if actual == expected else "different"


def _read_existing(path: Path, expected: bytes) -> bool:
    return _probe_final(path, expected) == "equal"


def _publish_svg_impl(output_directory: Path, filename: str, svg: bytes) -> str:
    final = output_directory / filename
    initial_state = _probe_final(final, svg)
    if initial_state == "equal":
        return "reused"
    if initial_state != "missing":
        raise _PublicationViolation

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{filename}.",
            suffix=".tmp",
            dir=output_directory,
            delete=False,
        ) as stream:
            temp_path = Path(stream.name)
            stream.write(svg)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            if os.name == "nt":
                os.rename(temp_path, final)
            else:
                # POSIX rename replaces an existing destination. A same-directory
                # hard link publishes complete bytes atomically without clobbering
                # a concurrent winner; finally removes only our temporary name.
                os.link(temp_path, final, follow_symlinks=False)
        except FileExistsError:
            winner_state = _probe_final(final, svg)
            if winner_state == "equal":
                return "reused"
            raise _PublicationViolation from None
        if os.name == "nt":
            temp_path = None
        return "created"
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass


def _publish_svg(output_directory: Path, filename: str, svg: bytes) -> str:
    result: str | None = None
    failed = False
    try:
        result = _publish_svg_impl(output_directory, filename, svg)
    except (OSError, TypeError, ValueError, OverflowError):
        failed = True
    if failed or result is None:
        _raise("output.conflict")
    return result


def render_ranking_svg(
    analysis_document: bytes,
    *,
    overlay_document: bytes | None = None,
    output_directory: str | Path,
    node_executable: str | Path | None = None,
    palette: str | None = None,
) -> dict[str, object]:
    if (
        type(analysis_document) is not bytes
        or len(analysis_document) > MAX_ANALYSIS_DOCUMENT_BYTES
        or (
            overlay_document is not None
            and (
                type(overlay_document) is not bytes
                or len(overlay_document) > MAX_OVERLAY_DOCUMENT_BYTES
            )
        )
    ):
        _raise("input.invalid")
    analysis = _parse_document(analysis_document, MAX_ANALYSIS_DOCUMENT_BYTES)
    overlay = (
        None
        if overlay_document is None
        else _parse_document(overlay_document, MAX_OVERLAY_DOCUMENT_BYTES)
    )
    prepared: _PreparedRender | None = None
    prepare_failed = False
    try:
        prepared = _prepare_render(analysis, overlay, palette)
    except (
        RenderContractError,
        CanonicalJsonError,
        TypeError,
        ValueError,
        RecursionError,
    ):
        prepare_failed = True
    if prepare_failed or prepared is None:
        _raise("render.invalid")

    platform_failed = False
    try:
        require_supported_platform()
    except LocalRendererError:
        platform_failed = True
    if platform_failed:
        _raise("renderer.unavailable")
    output_failed = False
    output: Path | None = None
    try:
        output = validate_local_directory(output_directory)
    except LocalRendererError:
        output_failed = True
    if output_failed or output is None:
        _raise("output.conflict")

    failure_code: str | None = None
    render_result: tuple[str, str, str, bytes] | None = None
    try:
        render_result = _render_svg(
            prepared,
            node_executable,
        )
    except RenderError:
        raise
    except RenderContractError:
        failure_code = "render.invalid"
    except RendererDeclaredError as error:
        failure_code = (
            "render.invalid" if error.code == "schema.invalid" else "renderer.unavailable"
        )
    except (
        CanonicalJsonError,
        RendererProtocolError,
        RendererRuntimeError,
        LocalRendererError,
    ):
        failure_code = "renderer.unavailable"
    except Exception:
        failure_code = "renderer.unavailable"
    if failure_code is not None or render_result is None:
        _raise(failure_code or "renderer.unavailable")
    model_hash, spec_hash, build_digest, svg = render_result

    if type(svg) is not bytes or len(svg) > MAX_PUBLISHED_SVG_BYTES:
        _raise("renderer.unavailable")
    svg_hash = sha256_bytes(svg)
    artifact_id = sha256_bytes(
        canonical_json_bytes(
            {
                "chart_model_sha256": model_hash,
                "render_spec_sha256": spec_hash,
                "renderer_build_digest": build_digest,
                "svg_sha256": svg_hash,
            }
        )
    )
    filename = f"ranking-svg-{artifact_id}.svg"
    status = _publish_svg(output, filename, svg)
    return {
        "render_contract_version": RENDER_CONTRACT_VERSION,
        "ok": True,
        "status": status,
        "artifact_id": artifact_id,
        "svg": filename,
        "svg_sha256": svg_hash,
        "renderer_build_digest": build_digest,
    }


def _prepare_matrix_render(
    analysis: dict[str, Any],
    *,
    mark: str,
    value_labels: str | None = None,
    palette: str | None = None,
) -> _PreparedRender:
    model, receipt = build_matrix_chart_model(analysis, mark=mark)
    model_bytes = canonical_json_bytes(model)
    model_sha256 = receipt["chart_model_sha256"]
    if not isinstance(model_sha256, str) or sha256_bytes(model_bytes) != model_sha256:
        _raise("render.invalid")
    spec = build_matrix_render_spec(
        mark=mark,
        x_count=len(model["x_axis"]["categories"]),
        y_count=len(model["y_axis"]["categories"]),
        value_labels=value_labels,
        palette=palette,
    )
    spec_bytes = canonical_json_bytes(spec)
    return _PreparedRender(
        model_sha256=model_sha256,
        spec_sha256=sha256_bytes(spec_bytes),
        model_bytes=model_bytes,
        spec_bytes=spec_bytes,
    )


def _render_matrix_payload(
    prepared: _PreparedRender,
    node_executable: str | os.PathLike[str] | None,
) -> tuple[str, str, str, bytes]:
    node = resolve_node_executable(node_executable)
    resources = load_verified_matrix_renderer_resources()
    frame = build_renderer_request(prepared.model_bytes, prepared.spec_bytes, resources)
    svg = run_bound_renderer(
        lambda request: launch_trusted_node(node, resources.bootstrap_bytes, request),
        frame,
        resources.runtime,
        accessibility_model=prepared.model_bytes,
    )
    return (
        prepared.model_sha256,
        prepared.spec_sha256,
        resources.renderer_build_digest,
        svg,
    )


def render_matrix_svg(
    analysis_document: bytes,
    *,
    mark: str,
    output_directory: str | Path,
    node_executable: str | Path | None = None,
    value_labels: str | None = None,
    palette: str | None = None,
) -> dict[str, object]:
    if mark not in {"matrix-bubble-svg.v1", "matrix-heatmap-svg.v1"}:
        raise ValueError("unknown matrix renderer mark")
    if type(analysis_document) is not bytes or len(analysis_document) > MAX_ANALYSIS_DOCUMENT_BYTES:
        _raise("input.invalid")
    analysis = _parse_document(analysis_document, MAX_ANALYSIS_DOCUMENT_BYTES)
    try:
        prepared = _prepare_matrix_render(
            analysis, mark=mark, value_labels=value_labels, palette=palette
        )
    except RenderError:
        raise
    except (RenderContractError, CanonicalJsonError, TypeError, ValueError, RecursionError):
        _raise("render.invalid")

    try:
        require_supported_platform()
    except LocalRendererError:
        _raise("renderer.unavailable")
    try:
        output = validate_local_directory(output_directory)
    except LocalRendererError:
        _raise("output.conflict")

    failure_code: str | None = None
    render_result: tuple[str, str, str, bytes] | None = None
    try:
        render_result = _render_matrix_payload(prepared, node_executable)
    except RenderError:
        raise
    except RenderContractError:
        failure_code = "render.invalid"
    except RendererDeclaredError as error:
        failure_code = (
            "render.invalid" if error.code == "schema.invalid" else "renderer.unavailable"
        )
    except (
        CanonicalJsonError,
        RendererProtocolError,
        RendererRuntimeError,
        LocalRendererError,
    ):
        failure_code = "renderer.unavailable"
    except Exception:
        failure_code = "renderer.unavailable"
    if failure_code is not None or render_result is None:
        _raise(failure_code or "renderer.unavailable")

    model_hash, spec_hash, build_digest, svg = render_result
    if type(svg) is not bytes or len(svg) > MAX_PUBLISHED_SVG_BYTES:
        _raise("renderer.unavailable")
    svg_hash = sha256_bytes(svg)
    artifact_id = sha256_bytes(
        canonical_json_bytes(
            {
                "chart_model_sha256": model_hash,
                "render_spec_sha256": spec_hash,
                "renderer_build_digest": build_digest,
                "svg_sha256": svg_hash,
            }
        )
    )
    prefix = mark.removesuffix(".v1")
    filename = f"{prefix}-{artifact_id}.svg"
    status = _publish_svg(output, filename, svg)
    return {
        "render_contract_version": RENDER_CONTRACT_VERSION,
        "ok": True,
        "status": status,
        "mark": mark,
        "artifact_id": artifact_id,
        "svg": filename,
        "svg_sha256": svg_hash,
        "renderer_build_digest": build_digest,
    }


def _prepare_categorical_render(
    analysis: dict[str, Any],
    *,
    mark: str,
    palette: str | None = None,
) -> _PreparedRender:
    if mark in SERIES_RENDER_MARKS:
        model, receipt = build_series_chart_model(analysis, mark=mark)
        x = model.get("x")
        series = model.get("series")
        if not isinstance(x, list) or not isinstance(series, list):
            raise ValueError("series chart model is invalid")
        spec = build_series_render_spec(
            mark=mark,
            x_count=len(x),
            series_count=len(series),
            palette=palette,
        )
    elif mark in COMPOSITION_RENDER_MARKS:
        model, receipt = build_composition_chart_model(analysis, mark=mark)
        items = model.get("items")
        if not isinstance(items, list):
            raise ValueError("composition chart model is invalid")
        spec = build_composition_render_spec(
            mark=mark,
            item_count=len(items),
            palette=palette,
        )
    else:
        raise ValueError("unknown categorical renderer mark")

    model_bytes = canonical_json_bytes(model)
    model_sha256 = receipt.get("chart_model_sha256")
    if (
        not isinstance(model_sha256, str)
        or sha256_bytes(model_bytes) != model_sha256
    ):
        raise RenderContractError() from None
    spec_bytes = canonical_json_bytes(spec)
    return _PreparedRender(
        model_sha256=model_sha256,
        spec_sha256=sha256_bytes(spec_bytes),
        model_bytes=model_bytes,
        spec_bytes=spec_bytes,
    )


def _render_categorical_payload(
    prepared: _PreparedRender,
    node_executable: str | os.PathLike[str] | None,
) -> tuple[str, str, str, bytes]:
    node = resolve_node_executable(node_executable)
    resources = load_verified_categorical_renderer_resources()
    frame = build_renderer_request(
        prepared.model_bytes,
        prepared.spec_bytes,
        resources,
    )
    svg = run_bound_renderer(
        lambda request: launch_trusted_node(
            node,
            resources.bootstrap_bytes,
            request,
        ),
        frame,
        resources.runtime,
        accessibility_model=prepared.model_bytes,
    )
    return (
        prepared.model_sha256,
        prepared.spec_sha256,
        resources.renderer_build_digest,
        svg,
    )


def render_categorical_svg(
    analysis_document: bytes,
    *,
    mark: str,
    output_directory: str | Path,
    node_executable: str | Path | None = None,
    palette: str | None = None,
) -> dict[str, object]:
    if mark not in {*SERIES_RENDER_MARKS, *COMPOSITION_RENDER_MARKS}:
        raise ValueError("unknown categorical renderer mark")
    if (
        type(analysis_document) is not bytes
        or len(analysis_document) > MAX_ANALYSIS_DOCUMENT_BYTES
    ):
        _raise("input.invalid")
    analysis = _parse_document(
        analysis_document,
        MAX_ANALYSIS_DOCUMENT_BYTES,
    )
    try:
        prepared = _prepare_categorical_render(analysis, mark=mark, palette=palette)
    except RenderError:
        raise
    except (
        RenderContractError,
        CanonicalJsonError,
        TypeError,
        ValueError,
        RecursionError,
    ):
        _raise("render.invalid")

    try:
        require_supported_platform()
    except LocalRendererError:
        _raise("renderer.unavailable")
    try:
        output = validate_local_directory(output_directory)
    except LocalRendererError:
        _raise("output.conflict")

    failure_code: str | None = None
    render_result: tuple[str, str, str, bytes] | None = None
    try:
        render_result = _render_categorical_payload(
            prepared,
            node_executable,
        )
    except RenderError:
        raise
    except RenderContractError:
        failure_code = "render.invalid"
    except RendererDeclaredError as error:
        failure_code = (
            "render.invalid"
            if error.code == "schema.invalid"
            else "renderer.unavailable"
        )
    except (
        CanonicalJsonError,
        RendererProtocolError,
        RendererRuntimeError,
        LocalRendererError,
    ):
        failure_code = "renderer.unavailable"
    except Exception:
        failure_code = "renderer.unavailable"
    if failure_code is not None or render_result is None:
        _raise(failure_code or "renderer.unavailable")

    model_hash, spec_hash, build_digest, svg = render_result
    if type(svg) is not bytes or len(svg) > MAX_PUBLISHED_SVG_BYTES:
        _raise("renderer.unavailable")
    svg_hash = sha256_bytes(svg)
    artifact_id = sha256_bytes(
        canonical_json_bytes(
            {
                "chart_model_sha256": model_hash,
                "render_spec_sha256": spec_hash,
                "renderer_build_digest": build_digest,
                "svg_sha256": svg_hash,
            }
        )
    )
    prefix = mark.removesuffix(".v1")
    filename = f"{prefix}-{artifact_id}.svg"
    status = _publish_svg(output, filename, svg)
    return {
        "render_contract_version": RENDER_CONTRACT_VERSION,
        "ok": True,
        "status": status,
        "mark": mark,
        "artifact_id": artifact_id,
        "svg": filename,
        "svg_sha256": svg_hash,
        "renderer_build_digest": build_digest,
    }



def _prepare_points_render(
    analysis: dict[str, Any],
    *,
    mark: str,
    palette: str | None = None,
) -> _PreparedRender:
    model, receipt = build_points_chart_model(analysis, mark=mark)
    points = model.get("points")
    if not isinstance(points, list):
        raise ValueError("points chart model is invalid")
    spec = build_points_render_spec(mark=mark, point_count=len(points), palette=palette)
    model_bytes = canonical_json_bytes(model)
    model_sha256 = receipt.get("chart_model_sha256")
    if not isinstance(model_sha256, str) or sha256_bytes(model_bytes) != model_sha256:
        raise RenderContractError() from None
    spec_bytes = canonical_json_bytes(spec)
    return _PreparedRender(
        model_sha256=model_sha256,
        spec_sha256=sha256_bytes(spec_bytes),
        model_bytes=model_bytes,
        spec_bytes=spec_bytes,
    )


def _render_points_payload(
    prepared: _PreparedRender,
    node_executable: str | os.PathLike[str] | None,
) -> tuple[str, str, str, bytes]:
    node = resolve_node_executable(node_executable)
    resources = load_verified_points_renderer_resources()
    frame = build_renderer_request(prepared.model_bytes, prepared.spec_bytes, resources)
    svg = run_bound_renderer(
        lambda request: launch_trusted_node(node, resources.bootstrap_bytes, request),
        frame,
        resources.runtime,
        accessibility_model=prepared.model_bytes,
    )
    return (
        prepared.model_sha256,
        prepared.spec_sha256,
        resources.renderer_build_digest,
        svg,
    )


def render_points_svg(
    analysis_document: bytes,
    *,
    mark: str,
    output_directory: str | Path,
    node_executable: str | Path | None = None,
    palette: str | None = None,
) -> dict[str, object]:
    if mark not in POINTS_RENDER_MARKS:
        raise ValueError("unknown points renderer mark")
    if type(analysis_document) is not bytes or len(analysis_document) > MAX_ANALYSIS_DOCUMENT_BYTES:
        _raise("input.invalid")
    analysis = _parse_document(analysis_document, MAX_ANALYSIS_DOCUMENT_BYTES)
    try:
        prepared = _prepare_points_render(analysis, mark=mark, palette=palette)
    except RenderError:
        raise
    except (
        RenderContractError,
        CanonicalJsonError,
        TypeError,
        ValueError,
        RecursionError,
    ):
        _raise("render.invalid")

    try:
        require_supported_platform()
    except LocalRendererError:
        _raise("renderer.unavailable")
    try:
        output = validate_local_directory(output_directory)
    except LocalRendererError:
        _raise("output.conflict")

    failure_code: str | None = None
    render_result: tuple[str, str, str, bytes] | None = None
    try:
        render_result = _render_points_payload(prepared, node_executable)
    except RenderError:
        raise
    except RenderContractError:
        failure_code = "render.invalid"
    except RendererDeclaredError as error:
        failure_code = (
            "render.invalid" if error.code == "schema.invalid" else "renderer.unavailable"
        )
    except (
        CanonicalJsonError,
        RendererProtocolError,
        RendererRuntimeError,
        LocalRendererError,
    ):
        failure_code = "renderer.unavailable"
    except Exception:
        failure_code = "renderer.unavailable"
    if failure_code is not None or render_result is None:
        _raise(failure_code or "renderer.unavailable")

    model_hash, spec_hash, build_digest, svg = render_result
    if type(svg) is not bytes or len(svg) > MAX_PUBLISHED_SVG_BYTES:
        _raise("renderer.unavailable")
    svg_hash = sha256_bytes(svg)
    artifact_id = sha256_bytes(
        canonical_json_bytes(
            {
                "chart_model_sha256": model_hash,
                "render_spec_sha256": spec_hash,
                "renderer_build_digest": build_digest,
                "svg_sha256": svg_hash,
            }
        )
    )
    filename = f"points-bubble-svg-{artifact_id}.svg"
    status = _publish_svg(output, filename, svg)
    return {
        "render_contract_version": RENDER_CONTRACT_VERSION,
        "ok": True,
        "status": status,
        "mark": mark,
        "artifact_id": artifact_id,
        "svg": filename,
        "svg_sha256": svg_hash,
        "renderer_build_digest": build_digest,
    }

def render_analysis_svg(
    analysis_document: bytes,
    *,
    mark: str | None = None,
    overlay_document: bytes | None = None,
    output_directory: str | Path,
    node_executable: str | Path | None = None,
    value_labels: str | None = None,
    palette: str | None = None,
) -> dict[str, object]:
    if type(analysis_document) is not bytes or len(analysis_document) > MAX_ANALYSIS_DOCUMENT_BYTES:
        _raise("input.invalid")
    analysis = _parse_document(analysis_document, MAX_ANALYSIS_DOCUMENT_BYTES)
    is_matrix = (
        analysis.get("analysis_id") == "matrix.v1" and analysis.get("result_variant") == "matrix"
    )
    if is_matrix:
        if overlay_document is not None:
            _raise("render.invalid")
        return render_matrix_svg(
            analysis_document,
            mark=mark or "matrix-bubble-svg.v1",
            output_directory=output_directory,
            node_executable=node_executable,
            value_labels=value_labels,
            palette=palette,
        )
    if value_labels is not None:
        # Count labels exist only on the matrix bubble mark.
        _raise("render.invalid")
    result_variant = analysis.get("result_variant")
    if result_variant == "points":
        if overlay_document is not None:
            _raise("render.invalid")
        return render_points_svg(
            analysis_document,
            mark=mark or "points-bubble-svg.v1",
            output_directory=output_directory,
            node_executable=node_executable,
            palette=palette,
        )
    if result_variant in ("series", "composition"):
        if overlay_document is not None:
            _raise("render.invalid")
        default_mark = (
            "series-line-svg.v1"
            if result_variant == "series"
            else "composition-bar-svg.v1"
        )
        return render_categorical_svg(
            analysis_document,
            mark=mark or default_mark,
            output_directory=output_directory,
            node_executable=node_executable,
            palette=palette,
        )
    if mark not in {None, "ranking-svg.v1"}:
        _raise("render.invalid")
    return render_ranking_svg(
        analysis_document,
        overlay_document=overlay_document,
        output_directory=output_directory,
        node_executable=node_executable,
        palette=palette,
    )
