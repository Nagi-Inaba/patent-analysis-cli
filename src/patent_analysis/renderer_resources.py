from __future__ import annotations

import json
import os
import re
import stat
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, NoReturn

from patent_analysis._render_canonical import canonical_sha256, sha256_bytes

MAX_RENDERER_BUILD_MANIFEST_BYTES = 16 * 1024
MAX_RENDERER_BOOTSTRAP_BYTES = 64 * 1024
MAX_RENDERER_BUNDLE_BYTES = 4 * 1024 * 1024
MAX_RENDERER_SCHEMA_BYTES = 16 * 1024

PINNED_RENDERER_BUILD_MANIFEST_SHA256 = (
    "7b5fc7a60986031616fc4ae0ed07253e5a2249720a9f43ef250f97fc4db40dd5"
)
PINNED_RENDERER_BUILD_DIGEST = "49ef33df4ffa9e61e1507f2f8bb8db98ac27ba52b3b88d26f5eee5217bcbebb7"
PINNED_RENDERER_BOOTSTRAP_SHA256 = (
    "8d2907e4fa4c097abecc2dfcfe5b28768d0174670062f91b0da14ef1b5f66622"
)
PINNED_RENDERER_BUNDLE_SHA256 = "f086c7b2fbf248085512845d77443c9693237057acefd15921336efd6e56829c"
PINNED_MATRIX_RENDERER_BUILD_MANIFEST_SHA256 = (
    "9a710bc74ee463416dd5a11d5c70d2cecabbcb33556cf2d714ca07a713292bdc"
)
PINNED_MATRIX_RENDERER_BUILD_DIGEST = (
    "474ca14ad828ab741d736dd2a66f25ed5a98d4e47e70bd3021b01c22935de602"
)
PINNED_MATRIX_RENDERER_BOOTSTRAP_SHA256 = (
    "2bde3bb8a25e2f565c234d1307880b13c92ff89260a3f1fc1e6d491593c7b7e2"
)
PINNED_MATRIX_RENDERER_BUNDLE_SHA256 = (
    "afba640e7e821639249bf15d24f663d468370d3bb0bfff80a4561830d93a60ad"
)
PINNED_CATEGORICAL_RENDERER_BUILD_MANIFEST_SHA256 = (
    "1c34d53aa1c70d09fa5f758493763154f4907ea02bb163cc700d14058637732f"
)
PINNED_CATEGORICAL_RENDERER_BUILD_DIGEST = (
    "f0d603c08a4ee7b108162f72ade66defd3dabf08d0daaf1857a258f3cc2c3665"
)
PINNED_CATEGORICAL_RENDERER_BOOTSTRAP_SHA256 = (
    "72c3ba94be83d64640f8b3da546e02d133c986b3997e27cdfc3c79dc3bbf8889"
)
PINNED_CATEGORICAL_RENDERER_BUNDLE_SHA256 = (
    "e3ea3b0abec49516faf771022f8fe07c6a28e4932d830fdeb8f9dfe7278e3b45"
)
PINNED_POINTS_RENDERER_BUILD_MANIFEST_SHA256 = (
    "d8c72edf794f3a95b0b4a761160569fa0f306f56c405db801396537982bb354a"
)
PINNED_POINTS_RENDERER_BUILD_DIGEST = (
    "a014f9baad268fece94dbc104603523c45def2ba4c662fda585dd11a5c2e4daa"
)
PINNED_POINTS_RENDERER_BOOTSTRAP_SHA256 = (
    "408957501e767dc44d1760bc425f89115852428709683b4c7126b2b3a3ce8fb7"
)
PINNED_POINTS_RENDERER_BUNDLE_SHA256 = (
    "5d5788c31de774b5363e42fc4fb48d0b527d2ad1f783170fa2d89a09c4d64af0"
)
RENDERER_BUILD_MANIFEST_SCHEMA_SHA256 = (
    "c9c0cf2581b5467fe5941672093ab26ebacf9f5d33d4c218c9ee0e61077f8b2b"
)
RENDERER_REQUEST_SCHEMA_SHA256 = "cefcb2c0e7bfb295d99b9a284078917e2aa7234fd881ba725b69eef19a8ba0cd"
RENDERER_RESPONSE_SCHEMA_SHA256 = "ce39d618d39ca29b0451a58fa6fda2c5da1c3de874b7a6da99f71c6df075e72b"
MATRIX_RENDERER_RESPONSE_SCHEMA_SHA256 = (
    "5304fb063e8974bac76b7cdffd2ff4b0ab981bec86caa48eb9aa88bea57e9a30"
)
PINNED_CATEGORICAL_RENDERER_RESPONSE_SCHEMA_SHA256 = (
    "3fd635d3b42fef23fcc9f52006439566a4340eef629dac25ce7527847d469d43"
)
PINNED_POINTS_RENDERER_RESPONSE_SCHEMA_SHA256 = (
    "cfc140058855b1f03a2a785cf4a01dc3db0f53a6a84c1b7427fec7b6d141308d"
)

_RENDER_PROFILE_IDS = frozenset(
    {
        "ranking-svg-ja-jp-node22-echarts6.v1",
        "matrix-svg-ja-jp-node22-echarts6.v1",
        "categorical-svg-ja-jp-node22-echarts6.v1",
        "points-svg-ja-jp-node22-echarts6.v1",
        "advanced-svg-ja-jp-node22-echarts6.v1",
    }
)

_FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
_LOWER_SHA256 = re.compile(r"^[0-9a-f]{64}$", re.ASCII)
_SEMVER = re.compile(
    r"^(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:-(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$",
    re.ASCII,
)


class RendererProtocolError(ValueError):
    """Fixed safe internal failure for renderer resources or wire data."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        del args, kwargs
        super().__init__("Renderer protocol is invalid")
        self.code = "renderer.protocol_invalid"
        self.safe_message = "Renderer protocol is invalid"
        self.__suppress_context__ = True


@dataclass(frozen=True)
class RendererBuildManifest:
    renderer_build_manifest_version: str
    bootstrap_sha256: str
    renderer_bundle_sha256: str
    renderer_protocol_version: str
    echarts_version: str
    build_tool_id: str
    build_tool_version: str


@dataclass(frozen=True)
class RendererRuntimeBinding:
    node_version: str
    echarts_version: str
    renderer_build_digest: str
    render_profile_id: str

    def __post_init__(self) -> None:
        if (
            self.node_version != "22.19.0"
            or self.echarts_version != "6.1.0"
            or _LOWER_SHA256.fullmatch(self.renderer_build_digest) is None
            or self.render_profile_id not in _RENDER_PROFILE_IDS
        ):
            raise ValueError("renderer runtime binding is invalid")


@dataclass(frozen=True)
class RendererResources:
    manifest: RendererBuildManifest
    manifest_bytes: bytes
    bootstrap_bytes: bytes
    bundle_bytes: bytes
    renderer_build_digest: str
    runtime: RendererRuntimeBinding


class _ResourceViolation(ValueError):
    pass


def _raise_duplicate_key(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _ResourceViolation
        result[key] = value
    return result


def _reject_constant(_value: str) -> NoReturn:
    raise _ResourceViolation


def _renderer_resource_root() -> Path:
    return Path(os.fspath(files("patent_analysis").joinpath("renderer")))


def _schema_resource_root() -> Path:
    return Path(os.fspath(files("patent_analysis").joinpath("schemas")))


def _is_reparse_or_not_regular(result: os.stat_result) -> bool:
    attributes = getattr(result, "st_file_attributes", 0)
    return (
        not stat.S_ISREG(result.st_mode)
        or stat.S_ISLNK(result.st_mode)
        or bool(attributes & _FILE_ATTRIBUTE_REPARSE_POINT)
    )


def _read_verified_resource_impl(path: Path, limit: int) -> bytes:
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        raise _ResourceViolation
    before = path.lstat()
    if _is_reparse_or_not_regular(before):
        raise _ResourceViolation
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if _is_reparse_or_not_regular(opened) or not os.path.samestat(before, opened):
            raise _ResourceViolation
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise _ResourceViolation
    return bytes(raw)


def _read_verified_resource(path: Path, limit: int) -> bytes:
    result: bytes | None = None
    failed = False
    try:
        result = _read_verified_resource_impl(path, limit)
    except (_ResourceViolation, OSError, TypeError, ValueError, OverflowError):
        failed = True
    if failed or result is None:
        raise RendererProtocolError() from None
    return result


_SCHEMA_DIGESTS = {
    "advanced-renderer-response.schema.json": (
        "c457d43440f01c861f876ae921ac830d31b113a1183c17b6a184506f86a8d3a8"
    ),
    "renderer-build-manifest.schema.json": RENDERER_BUILD_MANIFEST_SCHEMA_SHA256,
    "renderer-request.schema.json": RENDERER_REQUEST_SCHEMA_SHA256,
    "renderer-response.schema.json": RENDERER_RESPONSE_SCHEMA_SHA256,
    "matrix-renderer-response.schema.json": MATRIX_RENDERER_RESPONSE_SCHEMA_SHA256,
    "categorical-renderer-response.schema.json": (
        PINNED_CATEGORICAL_RENDERER_RESPONSE_SCHEMA_SHA256
    ),
    "points-renderer-response.schema.json": (PINNED_POINTS_RENDERER_RESPONSE_SCHEMA_SHA256),
}


def _load_verified_renderer_schema_bytes(name: str) -> bytes:
    raw: bytes | None = None
    failed = False
    try:
        expected_digest = _SCHEMA_DIGESTS.get(name)
        if expected_digest is None:
            raise _ResourceViolation
        raw = _read_verified_resource_impl(
            _schema_resource_root() / name, MAX_RENDERER_SCHEMA_BYTES
        )
        if sha256_bytes(raw) != expected_digest:
            raise _ResourceViolation
    except (_ResourceViolation, OSError, TypeError, ValueError, OverflowError):
        failed = True
    if failed or raw is None:
        raise RendererProtocolError() from None
    return raw


def _parse_manifest(raw: bytes) -> RendererBuildManifest:
    try:
        parsed = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_raise_duplicate_key,
            parse_constant=_reject_constant,
        )
    except (_ResourceViolation, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        raise _ResourceViolation from None
    expected = {
        "renderer_build_manifest_version",
        "bootstrap_sha256",
        "renderer_bundle_sha256",
        "renderer_protocol_version",
        "echarts_version",
        "build_tool_id",
        "build_tool_version",
    }
    if not isinstance(parsed, dict) or set(parsed) != expected:
        raise _ResourceViolation
    if any(not isinstance(parsed[key], str) for key in expected):
        raise _ResourceViolation
    if (
        parsed["renderer_build_manifest_version"] != "1.0.0"
        or parsed["renderer_protocol_version"] != "1.0.0"
        or parsed["echarts_version"] != "6.1.0"
        or parsed["build_tool_id"] != "patent-analysis.renderer-bundler"
        or _LOWER_SHA256.fullmatch(parsed["bootstrap_sha256"]) is None
        or _LOWER_SHA256.fullmatch(parsed["renderer_bundle_sha256"]) is None
        or not 1 <= len(parsed["build_tool_version"]) <= 64
        or not parsed["build_tool_version"].isascii()
        or _SEMVER.fullmatch(parsed["build_tool_version"]) is None
    ):
        raise _ResourceViolation
    return RendererBuildManifest(**parsed)


def _load_verified_renderer_resources_impl() -> RendererResources:
    root = _renderer_resource_root()
    manifest_bytes = _read_verified_resource_impl(
        root / "renderer-build-manifest.json", MAX_RENDERER_BUILD_MANIFEST_BYTES
    )
    if sha256_bytes(manifest_bytes) != PINNED_RENDERER_BUILD_MANIFEST_SHA256:
        raise _ResourceViolation
    manifest_schema_bytes = _load_verified_renderer_schema_bytes(
        "renderer-build-manifest.schema.json"
    )
    try:
        manifest_schema = json.loads(manifest_schema_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        raise _ResourceViolation from None
    if not isinstance(manifest_schema, dict):
        raise _ResourceViolation
    from patent_analysis.analysis_contracts import StrictDraft202012Validator

    manifest = _parse_manifest(manifest_bytes)
    manifest_value = {
        "renderer_build_manifest_version": manifest.renderer_build_manifest_version,
        "bootstrap_sha256": manifest.bootstrap_sha256,
        "renderer_bundle_sha256": manifest.renderer_bundle_sha256,
        "renderer_protocol_version": manifest.renderer_protocol_version,
        "echarts_version": manifest.echarts_version,
        "build_tool_id": manifest.build_tool_id,
        "build_tool_version": manifest.build_tool_version,
    }
    if next(StrictDraft202012Validator(manifest_schema).iter_errors(manifest_value), None):
        raise _ResourceViolation
    if (
        manifest.build_tool_version != "1.0.0"
        or manifest.bootstrap_sha256 != PINNED_RENDERER_BOOTSTRAP_SHA256
        or manifest.renderer_bundle_sha256 != PINNED_RENDERER_BUNDLE_SHA256
        or canonical_sha256(manifest_value) != PINNED_RENDERER_BUILD_DIGEST
    ):
        raise _ResourceViolation
    bootstrap_bytes = _read_verified_resource_impl(
        root / "bootstrap.js", MAX_RENDERER_BOOTSTRAP_BYTES
    )
    bundle_bytes = _read_verified_resource_impl(
        root / "renderer.bundle.js", MAX_RENDERER_BUNDLE_BYTES
    )
    if (
        sha256_bytes(bootstrap_bytes) != PINNED_RENDERER_BOOTSTRAP_SHA256
        or sha256_bytes(bundle_bytes) != PINNED_RENDERER_BUNDLE_SHA256
    ):
        raise _ResourceViolation
    build_digest = canonical_sha256(manifest_value)
    runtime = RendererRuntimeBinding(
        node_version="22.19.0",
        echarts_version="6.1.0",
        renderer_build_digest=build_digest,
        render_profile_id="ranking-svg-ja-jp-node22-echarts6.v1",
    )
    return RendererResources(
        manifest=manifest,
        manifest_bytes=manifest_bytes,
        bootstrap_bytes=bootstrap_bytes,
        bundle_bytes=bundle_bytes,
        renderer_build_digest=build_digest,
        runtime=runtime,
    )


def load_verified_renderer_resources() -> RendererResources:
    resources: RendererResources | None = None
    failed = False
    try:
        resources = _load_verified_renderer_resources_impl()
    except (
        _ResourceViolation,
        OSError,
        TypeError,
        ValueError,
        OverflowError,
        RecursionError,
    ):
        failed = True
    if failed or resources is None:
        raise RendererProtocolError() from None
    return resources


def _load_verified_matrix_renderer_resources_impl() -> RendererResources:
    root = _renderer_resource_root()
    manifest_bytes = _read_verified_resource_impl(
        root / "matrix-renderer-build-manifest.json",
        MAX_RENDERER_BUILD_MANIFEST_BYTES,
    )
    if sha256_bytes(manifest_bytes) != PINNED_MATRIX_RENDERER_BUILD_MANIFEST_SHA256:
        raise _ResourceViolation
    manifest_schema_bytes = _load_verified_renderer_schema_bytes(
        "renderer-build-manifest.schema.json"
    )
    try:
        manifest_schema = json.loads(manifest_schema_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        raise _ResourceViolation from None
    if not isinstance(manifest_schema, dict):
        raise _ResourceViolation
    from patent_analysis.analysis_contracts import StrictDraft202012Validator

    manifest = _parse_manifest(manifest_bytes)
    manifest_value = {
        "renderer_build_manifest_version": manifest.renderer_build_manifest_version,
        "bootstrap_sha256": manifest.bootstrap_sha256,
        "renderer_bundle_sha256": manifest.renderer_bundle_sha256,
        "renderer_protocol_version": manifest.renderer_protocol_version,
        "echarts_version": manifest.echarts_version,
        "build_tool_id": manifest.build_tool_id,
        "build_tool_version": manifest.build_tool_version,
    }
    if next(StrictDraft202012Validator(manifest_schema).iter_errors(manifest_value), None):
        raise _ResourceViolation
    if (
        manifest.build_tool_version != "1.0.0"
        or manifest.bootstrap_sha256 != PINNED_MATRIX_RENDERER_BOOTSTRAP_SHA256
        or manifest.renderer_bundle_sha256 != PINNED_MATRIX_RENDERER_BUNDLE_SHA256
        or canonical_sha256(manifest_value) != PINNED_MATRIX_RENDERER_BUILD_DIGEST
    ):
        raise _ResourceViolation
    bootstrap_bytes = _read_verified_resource_impl(
        root / "matrix-bootstrap.js", MAX_RENDERER_BOOTSTRAP_BYTES
    )
    bundle_bytes = _read_verified_resource_impl(
        root / "matrix-renderer.bundle.js", MAX_RENDERER_BUNDLE_BYTES
    )
    if (
        sha256_bytes(bootstrap_bytes) != PINNED_MATRIX_RENDERER_BOOTSTRAP_SHA256
        or sha256_bytes(bundle_bytes) != PINNED_MATRIX_RENDERER_BUNDLE_SHA256
    ):
        raise _ResourceViolation
    build_digest = canonical_sha256(manifest_value)
    runtime = RendererRuntimeBinding(
        node_version="22.19.0",
        echarts_version="6.1.0",
        renderer_build_digest=build_digest,
        render_profile_id="matrix-svg-ja-jp-node22-echarts6.v1",
    )
    return RendererResources(
        manifest=manifest,
        manifest_bytes=manifest_bytes,
        bootstrap_bytes=bootstrap_bytes,
        bundle_bytes=bundle_bytes,
        renderer_build_digest=build_digest,
        runtime=runtime,
    )


def load_verified_matrix_renderer_resources() -> RendererResources:
    """Load the separately pinned Matrix renderer profile resources."""

    resources: RendererResources | None = None
    failed = False
    try:
        resources = _load_verified_matrix_renderer_resources_impl()
    except (
        _ResourceViolation,
        OSError,
        TypeError,
        ValueError,
        OverflowError,
        RecursionError,
    ):
        failed = True
    if failed or resources is None:
        raise RendererProtocolError() from None
    return resources


def _load_verified_categorical_renderer_resources_impl() -> RendererResources:
    root = _renderer_resource_root()
    manifest_bytes = _read_verified_resource_impl(
        root / "categorical-renderer-build-manifest.json",
        MAX_RENDERER_BUILD_MANIFEST_BYTES,
    )
    if sha256_bytes(manifest_bytes) != PINNED_CATEGORICAL_RENDERER_BUILD_MANIFEST_SHA256:
        raise _ResourceViolation
    manifest_schema_bytes = _load_verified_renderer_schema_bytes(
        "renderer-build-manifest.schema.json"
    )
    try:
        manifest_schema = json.loads(manifest_schema_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        raise _ResourceViolation from None
    if not isinstance(manifest_schema, dict):
        raise _ResourceViolation
    from patent_analysis.analysis_contracts import StrictDraft202012Validator

    manifest = _parse_manifest(manifest_bytes)
    manifest_value = {
        "renderer_build_manifest_version": (manifest.renderer_build_manifest_version),
        "bootstrap_sha256": manifest.bootstrap_sha256,
        "renderer_bundle_sha256": manifest.renderer_bundle_sha256,
        "renderer_protocol_version": manifest.renderer_protocol_version,
        "echarts_version": manifest.echarts_version,
        "build_tool_id": manifest.build_tool_id,
        "build_tool_version": manifest.build_tool_version,
    }
    if next(
        StrictDraft202012Validator(manifest_schema).iter_errors(manifest_value),
        None,
    ):
        raise _ResourceViolation
    if (
        manifest.build_tool_version != "1.0.0"
        or manifest.bootstrap_sha256 != PINNED_CATEGORICAL_RENDERER_BOOTSTRAP_SHA256
        or manifest.renderer_bundle_sha256 != PINNED_CATEGORICAL_RENDERER_BUNDLE_SHA256
        or canonical_sha256(manifest_value) != PINNED_CATEGORICAL_RENDERER_BUILD_DIGEST
    ):
        raise _ResourceViolation
    bootstrap_bytes = _read_verified_resource_impl(
        root / "categorical-bootstrap.js", MAX_RENDERER_BOOTSTRAP_BYTES
    )
    bundle_bytes = _read_verified_resource_impl(
        root / "categorical-renderer.bundle.js",
        MAX_RENDERER_BUNDLE_BYTES,
    )
    if (
        sha256_bytes(bootstrap_bytes) != PINNED_CATEGORICAL_RENDERER_BOOTSTRAP_SHA256
        or sha256_bytes(bundle_bytes) != PINNED_CATEGORICAL_RENDERER_BUNDLE_SHA256
    ):
        raise _ResourceViolation
    build_digest = canonical_sha256(manifest_value)
    runtime = RendererRuntimeBinding(
        node_version="22.19.0",
        echarts_version="6.1.0",
        renderer_build_digest=build_digest,
        render_profile_id="categorical-svg-ja-jp-node22-echarts6.v1",
    )
    return RendererResources(
        manifest=manifest,
        manifest_bytes=manifest_bytes,
        bootstrap_bytes=bootstrap_bytes,
        bundle_bytes=bundle_bytes,
        renderer_build_digest=build_digest,
        runtime=runtime,
    )


def load_verified_categorical_renderer_resources() -> RendererResources:
    """Load the separately pinned categorical renderer family resources."""

    resources: RendererResources | None = None
    failed = False
    try:
        resources = _load_verified_categorical_renderer_resources_impl()
    except (
        _ResourceViolation,
        OSError,
        TypeError,
        ValueError,
        OverflowError,
        RecursionError,
    ):
        failed = True
    if failed or resources is None:
        raise RendererProtocolError() from None
    return resources


def _load_verified_points_renderer_resources_impl() -> RendererResources:
    root = _renderer_resource_root()
    manifest_bytes = _read_verified_resource_impl(
        root / "points-renderer-build-manifest.json",
        MAX_RENDERER_BUILD_MANIFEST_BYTES,
    )
    if sha256_bytes(manifest_bytes) != PINNED_POINTS_RENDERER_BUILD_MANIFEST_SHA256:
        raise _ResourceViolation
    manifest_schema_bytes = _load_verified_renderer_schema_bytes(
        "renderer-build-manifest.schema.json"
    )
    try:
        manifest_schema = json.loads(manifest_schema_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        raise _ResourceViolation from None
    if not isinstance(manifest_schema, dict):
        raise _ResourceViolation
    from patent_analysis.analysis_contracts import StrictDraft202012Validator

    manifest = _parse_manifest(manifest_bytes)
    manifest_value = {
        "renderer_build_manifest_version": manifest.renderer_build_manifest_version,
        "bootstrap_sha256": manifest.bootstrap_sha256,
        "renderer_bundle_sha256": manifest.renderer_bundle_sha256,
        "renderer_protocol_version": manifest.renderer_protocol_version,
        "echarts_version": manifest.echarts_version,
        "build_tool_id": manifest.build_tool_id,
        "build_tool_version": manifest.build_tool_version,
    }
    if next(StrictDraft202012Validator(manifest_schema).iter_errors(manifest_value), None):
        raise _ResourceViolation
    if (
        manifest.build_tool_version != "1.0.0"
        or manifest.bootstrap_sha256 != PINNED_POINTS_RENDERER_BOOTSTRAP_SHA256
        or manifest.renderer_bundle_sha256 != PINNED_POINTS_RENDERER_BUNDLE_SHA256
        or canonical_sha256(manifest_value) != PINNED_POINTS_RENDERER_BUILD_DIGEST
    ):
        raise _ResourceViolation
    bootstrap_bytes = _read_verified_resource_impl(
        root / "points-bootstrap.js", MAX_RENDERER_BOOTSTRAP_BYTES
    )
    bundle_bytes = _read_verified_resource_impl(
        root / "points-renderer.bundle.js", MAX_RENDERER_BUNDLE_BYTES
    )
    if (
        sha256_bytes(bootstrap_bytes) != PINNED_POINTS_RENDERER_BOOTSTRAP_SHA256
        or sha256_bytes(bundle_bytes) != PINNED_POINTS_RENDERER_BUNDLE_SHA256
    ):
        raise _ResourceViolation
    build_digest = canonical_sha256(manifest_value)
    runtime = RendererRuntimeBinding(
        node_version="22.19.0",
        echarts_version="6.1.0",
        renderer_build_digest=build_digest,
        render_profile_id="points-svg-ja-jp-node22-echarts6.v1",
    )
    return RendererResources(
        manifest=manifest,
        manifest_bytes=manifest_bytes,
        bootstrap_bytes=bootstrap_bytes,
        bundle_bytes=bundle_bytes,
        renderer_build_digest=build_digest,
        runtime=runtime,
    )


def load_verified_points_renderer_resources() -> RendererResources:
    """Load the separately pinned Lifecycle points renderer resources."""

    resources: RendererResources | None = None
    failed = False
    try:
        resources = _load_verified_points_renderer_resources_impl()
    except (
        _ResourceViolation,
        OSError,
        TypeError,
        ValueError,
        OverflowError,
        RecursionError,
    ):
        failed = True
    if failed or resources is None:
        raise RendererProtocolError() from None
    return resources
