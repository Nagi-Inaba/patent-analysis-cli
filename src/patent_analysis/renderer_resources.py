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
    "682d16ff286965ff24732d2df19da93886cd8e1c2be3c1f1abdb59d131560f18"
)
PINNED_RENDERER_BUILD_DIGEST = "dff4c6dcce7b636ed0345c663a119714f4511eedf65d3727917a4aa1b5dc0aeb"
PINNED_RENDERER_BOOTSTRAP_SHA256 = (
    "9d0bd0a364c5c96c6224913ced51c1eb316774b0387c29de3fa8adc5f86b76aa"
)
PINNED_RENDERER_BUNDLE_SHA256 = "f90a25664ce4ba931ddc04e43cfbc2f1c53360a379a3f03f279d44eb89c9a6f6"
PINNED_MATRIX_RENDERER_BUILD_MANIFEST_SHA256 = (
    "29add2352602c6676c2980075f87b720f3dd7390e5856713e75c194d60ca1c90"
)
PINNED_MATRIX_RENDERER_BUILD_DIGEST = (
    "625703c76fe32b7b26b083d5185ad4effdfd71ae6565f2ab689a43f47ce8de9d"
)
PINNED_MATRIX_RENDERER_BOOTSTRAP_SHA256 = (
    "448d8250d45bb473b51b669310f37c147fe39e29d0a777daea12d34b6c093999"
)
PINNED_MATRIX_RENDERER_BUNDLE_SHA256 = (
    "24cd8cfbfff86e926c08730037fb2e2eba15894027755efeac32a415adaba547"
)
PINNED_CATEGORICAL_RENDERER_BUILD_MANIFEST_SHA256 = (
    "a3ac05b8e1fa531a46eef6eb5213acf9f302b1b76eb989a02a6b2bc500bf1a97"
)
PINNED_CATEGORICAL_RENDERER_BUILD_DIGEST = (
    "8d854927dc22c40de22c0c9916d875adfca45ed9ee24dac363f86c2d50f330e3"
)
PINNED_CATEGORICAL_RENDERER_BOOTSTRAP_SHA256 = (
    "933a0e1d6907111ee5962650846c5b8a37054856a7bf5134f198ca43be1a7c59"
)
PINNED_CATEGORICAL_RENDERER_BUNDLE_SHA256 = (
    "433b4f894097bb616d12d25e8913b43b4aaa693b9de57e7bbfcdf9363ae40526"
)
PINNED_POINTS_RENDERER_BUILD_MANIFEST_SHA256 = (
    "ab8a4aa1c5945084fc370441998fc7c4747eaf089052abb855ce38a7c41f69a8"
)
PINNED_POINTS_RENDERER_BUILD_DIGEST = (
    "2bf0108fd0e4dc40cc422e5ab05cb0ed8f63b34c4984ffe87e9193076a135719"
)
PINNED_POINTS_RENDERER_BOOTSTRAP_SHA256 = (
    "69b86dbf693a2fbbd943fb3503a5698da4299248e1d939887176478adf26262e"
)
PINNED_POINTS_RENDERER_BUNDLE_SHA256 = (
    "2798df1e7feb5686b270d92772fb82e44fb375fc68f7ecf5a0074b8b465b6793"
)
RENDERER_BUILD_MANIFEST_SCHEMA_SHA256 = (
    "c9c0cf2581b5467fe5941672093ab26ebacf9f5d33d4c218c9ee0e61077f8b2b"
)
RENDERER_REQUEST_SCHEMA_SHA256 = "cefcb2c0e7bfb295d99b9a284078917e2aa7234fd881ba725b69eef19a8ba0cd"
RENDERER_RESPONSE_SCHEMA_SHA256 = "968a0ff43a1b5e84532cb2589c46cac8eea17a3f61ceadabba84d7c6d28e077e"
MATRIX_RENDERER_RESPONSE_SCHEMA_SHA256 = (
    "7a16f681421fda129f62ae17f224a960352b499f994104716385d701c595452b"
)
PINNED_CATEGORICAL_RENDERER_RESPONSE_SCHEMA_SHA256 = (
    "77643677416f756f2f97ed8bb9cfe2e27b233d2f5baa76abaf310415a913954b"
)
PINNED_POINTS_RENDERER_RESPONSE_SCHEMA_SHA256 = (
    "4d766ce0cbef4e568a112ff1c184a064b37df8db712f60300089f768b019e812"
)

_RENDER_PROFILE_IDS = frozenset(
    {
        "ranking-svg-ja-jp-node24-echarts6.v1",
        "matrix-svg-ja-jp-node24-echarts6.v1",
        "categorical-svg-ja-jp-node24-echarts6.v1",
        "points-svg-ja-jp-node24-echarts6.v1",
        "advanced-svg-ja-jp-node24-echarts6.v1",
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
            self.node_version != "24.22.1"
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
        "e1fcc68329a9deb02b220fa472edf32acc1521e428e3b5030977a9126270bc18"
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
        node_version="24.22.1",
        echarts_version="6.1.0",
        renderer_build_digest=build_digest,
        render_profile_id="ranking-svg-ja-jp-node24-echarts6.v1",
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
        node_version="24.22.1",
        echarts_version="6.1.0",
        renderer_build_digest=build_digest,
        render_profile_id="matrix-svg-ja-jp-node24-echarts6.v1",
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
        node_version="24.22.1",
        echarts_version="6.1.0",
        renderer_build_digest=build_digest,
        render_profile_id="categorical-svg-ja-jp-node24-echarts6.v1",
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
        node_version="24.22.1",
        echarts_version="6.1.0",
        renderer_build_digest=build_digest,
        render_profile_id="points-svg-ja-jp-node24-echarts6.v1",
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
