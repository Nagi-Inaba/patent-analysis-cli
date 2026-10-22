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
    "7fd1b1faae80dd48fafbd11f22774baec1681c9781199f42a3135b9c64573a0f"
)
PINNED_RENDERER_BUILD_DIGEST = "7148882cf54591e805ec941907834c395e3283c8de64aabfbddadca44d4dbcb3"
PINNED_RENDERER_BOOTSTRAP_SHA256 = (
    "78bef3003d9e99519a06c9d1684c399a8a1a864a5bc51ee582652bcde1afe4a7"
)
PINNED_RENDERER_BUNDLE_SHA256 = "d9ec2822aa39b247be4b28049e703b77ad4eea421c2c99ae4be6cd9e291effe3"
PINNED_MATRIX_RENDERER_BUILD_MANIFEST_SHA256 = (
    "59e0d4ccc2c31d57bc7c18286b3885cc50757429b8909b20c3e4265742dfa9ee"
)
PINNED_MATRIX_RENDERER_BUILD_DIGEST = (
    "4f7213a38891bd22407a092751c31839197f41a9edadfc1be01e4b5012fa71da"
)
PINNED_MATRIX_RENDERER_BOOTSTRAP_SHA256 = (
    "06d5a99c74414ef0308e675bcdd521e970c0ca468420c57dd7fdcfaa40734eeb"
)
PINNED_MATRIX_RENDERER_BUNDLE_SHA256 = (
    "9063e199b83ab0e5970b9f181279f3ae2a79282656977e494bc8943a7ed509d9"
)
PINNED_CATEGORICAL_RENDERER_BUILD_MANIFEST_SHA256 = (
    "ed29ac1f0d852fe1af2a445c4d82c311c12a6edacd22352692d7ce0e6ea6edf4"
)
PINNED_CATEGORICAL_RENDERER_BUILD_DIGEST = (
    "9d8597ad0d4426656b618a52f90a567d4fddb71d43e487b4d0cedbbe05a52beb"
)
PINNED_CATEGORICAL_RENDERER_BOOTSTRAP_SHA256 = (
    "9064602a41f9ba966e8e69cb83beaa441f5700f1b13265d9223007fd4e0acb40"
)
PINNED_CATEGORICAL_RENDERER_BUNDLE_SHA256 = (
    "f7780884ca17e73cb030fea39c77c1602977a8c529150bc939f8aaa3520d9c55"
)
PINNED_POINTS_RENDERER_BUILD_MANIFEST_SHA256 = (
    "472e198886ffba563d60a22dc8e00616f0587a33ffc2af52f4cd46898afcf984"
)
PINNED_POINTS_RENDERER_BUILD_DIGEST = (
    "5cc530082ca979988efa457c257272b883e7862b52a567a0f22bb94cb1d29060"
)
PINNED_POINTS_RENDERER_BOOTSTRAP_SHA256 = (
    "529e4cc35bd1d6e2bdcc42d62a33f6308b7a50cb37f2803d1450cf6101ea42e6"
)
PINNED_POINTS_RENDERER_BUNDLE_SHA256 = (
    "8f8f2cdedff327241500ab2a59027c4c3e04bd1c076e369bc7066ddb0e53f169"
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
