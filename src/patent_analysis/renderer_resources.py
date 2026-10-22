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
    "e8d3ce622f2fd018c12f821eb8680c2bf6ca296b0c21ea97c78d4baa22d8fe41"
)
PINNED_RENDERER_BUILD_DIGEST = "bdc9904cb2cec503cdfdb7884f6f9cedb8c247f9778ffcd20aa0c9fb7f8ebb30"
PINNED_RENDERER_BOOTSTRAP_SHA256 = (
    "6dec5126cec4ab7f9792c17b3513825d093318a995b614de217ab5567b2b6c0f"
)
PINNED_RENDERER_BUNDLE_SHA256 = "29f39e960291b7601533a63d6cde44f2f94aa6622adacbe85e3eca828eb1a3bb"
PINNED_MATRIX_RENDERER_BUILD_MANIFEST_SHA256 = (
    "263c7585920b0b5b64c7bcd8160be98aaf6e13d03dc5f42919ebb622240c95dc"
)
PINNED_MATRIX_RENDERER_BUILD_DIGEST = (
    "5b40d87ed38ada463bb6e180adc33f017bb782b0be1e02d6a1e15e9e75df7cc2"
)
PINNED_MATRIX_RENDERER_BOOTSTRAP_SHA256 = (
    "eac2ce045474fafe87eff03c9ed807357a990d05b4ccfe738fcc613e96627cea"
)
PINNED_MATRIX_RENDERER_BUNDLE_SHA256 = (
    "6606fe8683a6502c5b61867f988fbbdb79667ab4fafd8bb7c87b98aeb5655700"
)
PINNED_CATEGORICAL_RENDERER_BUILD_MANIFEST_SHA256 = (
    "5e9305b5e221eed623834a2ba6f96960ba4a668fa4e2d209207934c190a31aab"
)
PINNED_CATEGORICAL_RENDERER_BUILD_DIGEST = (
    "0c0c0949e46a55bf0a349b4e8ca80c3acf5d379a38ca93671e1c309974ed25d6"
)
PINNED_CATEGORICAL_RENDERER_BOOTSTRAP_SHA256 = (
    "71b57253de1c13b25ed9f027462173aef663045903bc88c1a5273eb1290f7ca2"
)
PINNED_CATEGORICAL_RENDERER_BUNDLE_SHA256 = (
    "8b86b969e8b176713dedbcac13912680e444f5859f9ee6d6dc5343d419f42571"
)
PINNED_POINTS_RENDERER_BUILD_MANIFEST_SHA256 = (
    "bfad40fd19b2d90ab2cfd9d2dae3758e5c818305b0fd9453a319d551718cd1a0"
)
PINNED_POINTS_RENDERER_BUILD_DIGEST = (
    "a7724a3aff9a213a2f7e3fc0655858e5205adb95489d5b3481020a5e8cf95ac6"
)
PINNED_POINTS_RENDERER_BOOTSTRAP_SHA256 = (
    "190e4f246407d8839416586027c5983ce0fcf95ca00a95e449c358e6899a8569"
)
PINNED_POINTS_RENDERER_BUNDLE_SHA256 = (
    "b34e506ae66973d9da2e537d2be206df3be86e7bfdac28656e15977e608ffd4f"
)
RENDERER_BUILD_MANIFEST_SCHEMA_SHA256 = (
    "c9c0cf2581b5467fe5941672093ab26ebacf9f5d33d4c218c9ee0e61077f8b2b"
)
RENDERER_REQUEST_SCHEMA_SHA256 = "cefcb2c0e7bfb295d99b9a284078917e2aa7234fd881ba725b69eef19a8ba0cd"
RENDERER_RESPONSE_SCHEMA_SHA256 = "3d04889677d44d6c9a37af843f290281921931d59664b3bc5a0dd6bbb0a8102f"
MATRIX_RENDERER_RESPONSE_SCHEMA_SHA256 = (
    "9dd7fdb8910638cca47d6640d038f2ebf6d7e9547858a6fd48651aca009ba0a7"
)
PINNED_CATEGORICAL_RENDERER_RESPONSE_SCHEMA_SHA256 = (
    "0b1f394e469799d0b5a68b5d351375f22875b1b6fdcebeae43e929a0fbe92245"
)
PINNED_POINTS_RENDERER_RESPONSE_SCHEMA_SHA256 = (
    "16df3f0755684690d2bdb2528962dae75844e8ff9ca81ddccb1f1c6b1c6d87b9"
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
            self.node_version != "22.23.4"
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
        "edbc5ab7250792142321de799fa76aa4a139adf330c42b4a4f1beb29f109d1ed"
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
        node_version="22.23.4",
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
        node_version="22.23.4",
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
        node_version="22.23.4",
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
        node_version="22.23.4",
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
