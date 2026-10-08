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
    "7d703dcd25c2c67ee2c4c2096b96e48abe278926f1b4c3218bfcf83979d03396"
)
PINNED_RENDERER_BUILD_DIGEST = "0476648d6fda1dca713fe78703c6ccad05529880362e5c8a767efa1161fec11b"
PINNED_RENDERER_BOOTSTRAP_SHA256 = (
    "677528c5a5a884668ad7e64be91ab13996b0d1684d2ef69eefb72ad561551641"
)
PINNED_RENDERER_BUNDLE_SHA256 = "1870a731cc2222d3ceed199706b163881993f7918ed7dd25ae087a4442ef11ae"
PINNED_MATRIX_RENDERER_BUILD_MANIFEST_SHA256 = (
    "3336bf71aa71fbd30c7cd631923e2947c0a06e2df38e7750e1f81d4702ee3d94"
)
PINNED_MATRIX_RENDERER_BUILD_DIGEST = (
    "366ba210bf2eaf89413f27c166668eea1895f0c1259ac2e4378711ac5c09950e"
)
PINNED_MATRIX_RENDERER_BOOTSTRAP_SHA256 = (
    "4207577f056ed3a594e79677d58504373757582fd6f8f47bf6b7eac080c20830"
)
PINNED_MATRIX_RENDERER_BUNDLE_SHA256 = (
    "3f19654c938863d5892964961b2d5ec61b54fa8e7fcc74f29ba7eb8be33d2472"
)
PINNED_CATEGORICAL_RENDERER_BUILD_MANIFEST_SHA256 = (
    "edc222a1af30daf8e25fa89584f848f675b78e2553d37fdfe8b4dd24c0a14869"
)
PINNED_CATEGORICAL_RENDERER_BUILD_DIGEST = (
    "26c5744dab0151fe42c87ed37a104b3557d38e5ee7dfe6677b1248cdde8946e3"
)
PINNED_CATEGORICAL_RENDERER_BOOTSTRAP_SHA256 = (
    "9b32ff1b1ac5c1d523448d532a45af080bd39ddf93400dbd05ff7fa1c9f53dd7"
)
PINNED_CATEGORICAL_RENDERER_BUNDLE_SHA256 = (
    "b0ad1fc0f146b37169e8c321d5b31d2d08b15aa3ae2a68e08111fdeeffc1c7e3"
)
PINNED_POINTS_RENDERER_BUILD_MANIFEST_SHA256 = (
    "c54fc615e8d0140a0f13759e270981b2b63997bf7df45b3ad6a075db5eca0eb5"
)
PINNED_POINTS_RENDERER_BUILD_DIGEST = (
    "4d3e2dc1734ee60c5d1f9081948e4076e9ba9a59952e3015ba1c741b3a307fb4"
)
PINNED_POINTS_RENDERER_BOOTSTRAP_SHA256 = (
    "ef56e84a1e9e4a49944228e1e4ae86682f9a4bddf65f2c07344afee9f163f9dc"
)
PINNED_POINTS_RENDERER_BUNDLE_SHA256 = (
    "9d542e7b3322b06ebb37cec004a3cd5e3a075de176f8f1ef6f127e1bd70271f3"
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
