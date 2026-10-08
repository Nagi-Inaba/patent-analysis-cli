from __future__ import annotations

import base64
import hashlib
from collections.abc import Callable
from typing import Any, NoReturn

from patent_analysis.renderer_protocol import (
    MAX_RENDERER_STDOUT_BYTES,
    RendererDeclaredError,
    decode_renderer_response,
    encode_renderer_frame,
)
from patent_analysis.renderer_resources import (
    RendererProtocolError,
    RendererResources,
    RendererRuntimeBinding,
)

MAX_RENDERER_STDERR_BYTES = 64 * 1024
MAX_RENDERER_MODEL_BYTES = 2 * 1024 * 1024
MAX_RENDERER_SPEC_BYTES = 16 * 1024


class RendererRuntimeError(RuntimeError):
    """Fixed safe internal failure for renderer process execution."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        del args, kwargs
        super().__init__("Trusted renderer is unavailable")
        self.code = "renderer.unavailable"
        self.safe_message = "Trusted renderer is unavailable"
        self.__suppress_context__ = True


def _raise_runtime_error() -> NoReturn:
    raise RendererRuntimeError() from None


def build_renderer_request(
    model_bytes: bytes,
    spec_bytes: bytes,
    resources: RendererResources,
) -> bytes:
    if (
        type(model_bytes) is not bytes
        or type(spec_bytes) is not bytes
        or not isinstance(resources, RendererResources)
        or len(model_bytes) > MAX_RENDERER_MODEL_BYTES
        or len(spec_bytes) > MAX_RENDERER_SPEC_BYTES
    ):
        raise RendererProtocolError() from None
    request: dict[str, object] = {
        "protocol_version": "1.0.0",
        "chart_model_b64": base64.b64encode(model_bytes).decode("ascii"),
        "chart_model_sha256": hashlib.sha256(model_bytes).hexdigest(),
        "render_spec_b64": base64.b64encode(spec_bytes).decode("ascii"),
        "render_spec_sha256": hashlib.sha256(spec_bytes).hexdigest(),
    }
    return encode_renderer_frame(resources.bundle_bytes, request)


def run_bound_renderer(
    launcher: Callable[[bytes], Any],
    frame: bytes,
    binding: RendererRuntimeBinding,
    *,
    accessibility_model: bytes | None = None,
) -> bytes:
    if not callable(launcher) or type(frame) is not bytes or not isinstance(
        binding, RendererRuntimeBinding
    ):
        raise RendererProtocolError() from None

    result: Any | None = None
    launch_failed = False
    try:
        result = launcher(frame)
    except Exception:
        launch_failed = True
    if launch_failed or result is None:
        _raise_runtime_error()

    result_invalid = False
    returncode: int | None = None
    stdout: bytes | None = None
    stderr: bytes | None = None
    try:
        returncode = result.returncode
        stdout = result.stdout
        stderr = result.stderr
        result_invalid = (
            isinstance(returncode, bool)
            or not isinstance(returncode, int)
            or type(stdout) is not bytes
            or type(stderr) is not bytes
        )
    except Exception:
        result_invalid = True
    if (
        result_invalid
        or returncode is None
        or stdout is None
        or stderr is None
        or returncode != 0
        or len(stdout) > MAX_RENDERER_STDOUT_BYTES
        or len(stderr) > MAX_RENDERER_STDERR_BYTES
    ):
        _raise_runtime_error()

    svg: bytes | None = None
    declared_error: RendererDeclaredError | None = None
    protocol_failed = False
    try:
        svg = decode_renderer_response(stdout, binding)
    except RendererDeclaredError as error:
        declared_error = error
    except RendererProtocolError:
        protocol_failed = True
    except Exception:
        protocol_failed = True
    if declared_error is not None:
        raise declared_error from None
    if protocol_failed or svg is None:
        raise RendererProtocolError() from None
    if accessibility_model is not None:
        from patent_analysis.svg_accessibility import add_svg_accessibility

        metadata_failed = False
        try:
            svg = add_svg_accessibility(svg, accessibility_model)
        except Exception:
            metadata_failed = True
        if metadata_failed:
            _raise_runtime_error()
    return svg
