from __future__ import annotations

import hashlib
import importlib
import json
import traceback
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace

import pytest


def _resources_module():
    try:
        return importlib.import_module("patent_analysis.renderer_resources")
    except ModuleNotFoundError:
        pytest.fail("missing renderer resource interfaces", pytrace=False)


def test_renderer_resource_interfaces_exist_with_exact_limits() -> None:
    module = _resources_module()

    assert module.MAX_RENDERER_BUILD_MANIFEST_BYTES == 16 * 1024
    assert module.MAX_RENDERER_BOOTSTRAP_BYTES == 64 * 1024
    assert module.MAX_RENDERER_BUNDLE_BYTES == 4 * 1024 * 1024
    assert module.RendererResources is not None
    assert module.RendererBuildManifest is not None
    assert module.RendererRuntimeBinding is not None
    assert callable(module.load_verified_renderer_resources)


def test_python_trust_anchors_are_exact_reviewed_values() -> None:
    module = _resources_module()

    assert getattr(module, "PINNED_RENDERER_BUILD_MANIFEST_SHA256", None) == (
        "7d703dcd25c2c67ee2c4c2096b96e48abe278926f1b4c3218bfcf83979d03396"
    )
    assert getattr(module, "PINNED_RENDERER_BUILD_DIGEST", None) == (
        "0476648d6fda1dca713fe78703c6ccad05529880362e5c8a767efa1161fec11b"
    )
    assert getattr(module, "PINNED_RENDERER_BOOTSTRAP_SHA256", None) == (
        "677528c5a5a884668ad7e64be91ab13996b0d1684d2ef69eefb72ad561551641"
    )
    assert getattr(module, "PINNED_RENDERER_BUNDLE_SHA256", None) == (
        "1870a731cc2222d3ceed199706b163881993f7918ed7dd25ae087a4442ef11ae"
    )


def test_schema_trust_anchors_are_exact_and_discoverable() -> None:
    module = _resources_module()

    assert getattr(module, "RENDERER_BUILD_MANIFEST_SCHEMA_SHA256", None) == (
        "c9c0cf2581b5467fe5941672093ab26ebacf9f5d33d4c218c9ee0e61077f8b2b"
    )
    assert getattr(module, "RENDERER_REQUEST_SCHEMA_SHA256", None) == (
        "cefcb2c0e7bfb295d99b9a284078917e2aa7234fd881ba725b69eef19a8ba0cd"
    )
    assert getattr(module, "RENDERER_RESPONSE_SCHEMA_SHA256", None) == (
        "ce39d618d39ca29b0451a58fa6fda2c5da1c3de874b7a6da99f71c6df075e72b"
    )


def test_packaged_renderer_resources_have_exact_current_digests() -> None:
    module = _resources_module()

    resources = module.load_verified_renderer_resources()

    assert hashlib.sha256(resources.manifest_bytes).hexdigest() == (
        "7d703dcd25c2c67ee2c4c2096b96e48abe278926f1b4c3218bfcf83979d03396"
    )
    assert hashlib.sha256(resources.bootstrap_bytes).hexdigest() == (
        "677528c5a5a884668ad7e64be91ab13996b0d1684d2ef69eefb72ad561551641"
    )
    assert hashlib.sha256(resources.bundle_bytes).hexdigest() == (
        "1870a731cc2222d3ceed199706b163881993f7918ed7dd25ae087a4442ef11ae"
    )
    assert resources.renderer_build_digest == (
        "0476648d6fda1dca713fe78703c6ccad05529880362e5c8a767efa1161fec11b"
    )
    assert resources.runtime == module.RendererRuntimeBinding(
        node_version="22.19.0",
        echarts_version="6.1.0",
        renderer_build_digest=(
            "0476648d6fda1dca713fe78703c6ccad05529880362e5c8a767efa1161fec11b"
        ),
        render_profile_id="ranking-svg-ja-jp-node22-echarts6.v1",
    )
    with pytest.raises(FrozenInstanceError):
        resources.bundle_bytes = b"changed"


def test_manifest_is_exactly_seven_fields_and_typed() -> None:
    module = _resources_module()
    resources = module.load_verified_renderer_resources()
    parsed = json.loads(resources.manifest_bytes)

    assert list(parsed) == [
        "bootstrap_sha256",
        "build_tool_id",
        "build_tool_version",
        "echarts_version",
        "renderer_build_manifest_version",
        "renderer_bundle_sha256",
        "renderer_protocol_version",
    ]
    assert resources.manifest.renderer_build_manifest_version == "1.0.0"
    assert resources.manifest.bootstrap_sha256 == parsed["bootstrap_sha256"]
    assert resources.manifest.renderer_bundle_sha256 == parsed["renderer_bundle_sha256"]
    assert resources.manifest.renderer_protocol_version == "1.0.0"
    assert resources.manifest.echarts_version == "6.1.0"
    assert resources.manifest.build_tool_id == "patent-analysis.renderer-bundler"
    assert resources.manifest.build_tool_version == "1.0.0"


@pytest.mark.parametrize(
    ("mutation", "target_name"),
    [
        ("manifest-extra-field", "renderer-build-manifest.json"),
        ("manifest-bundle-digest", "renderer-build-manifest.json"),
        ("manifest-build-version", "renderer-build-manifest.json"),
        ("bootstrap-bytes", "bootstrap.js"),
        ("bundle-bytes", "renderer.bundle.js"),
    ],
)
def test_resource_mutations_fail_closed_without_payload_leakage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    target_name: str,
) -> None:
    module = _resources_module()
    package_renderer = Path(module.__file__).parent / "renderer"
    fixture_root = tmp_path / "renderer"
    fixture_root.mkdir()
    for name in ("renderer-build-manifest.json", "bootstrap.js", "renderer.bundle.js"):
        (fixture_root / name).write_bytes((package_renderer / name).read_bytes())
    secret = b"TASK3-RESOURCE-SECRET"
    target = fixture_root / target_name
    if mutation == "manifest-extra-field":
        value = json.loads(target.read_bytes())
        value["secret"] = secret.decode()
        target.write_text(json.dumps(value), encoding="utf-8")
    elif mutation == "manifest-bundle-digest":
        value = json.loads(target.read_bytes())
        value["renderer_bundle_sha256"] = "0" * 64
        target.write_text(json.dumps(value), encoding="utf-8")
    elif mutation == "manifest-build-version":
        value = json.loads(target.read_bytes())
        value["build_tool_version"] = "1.0.1"
        target.write_text(json.dumps(value), encoding="utf-8")
    else:
        target.write_bytes(target.read_bytes() + secret)
    monkeypatch.setattr(module, "_renderer_resource_root", lambda: fixture_root)

    with pytest.raises(module.RendererProtocolError) as caught:
        module.load_verified_renderer_resources()

    rendered = "".join(traceback.format_exception(caught.value))
    assert caught.value.code == "renderer.protocol_invalid"
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert secret.decode() not in rendered
    assert secret.decode() not in repr(caught.value.__dict__)


def test_coordinated_manifest_bootstrap_bundle_substitution_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _resources_module()
    package_renderer = Path(module.__file__).parent / "renderer"
    fixture_root = tmp_path / "renderer"
    fixture_root.mkdir()
    bootstrap = (package_renderer / "bootstrap.js").read_bytes() + b"\n// substituted"
    bundle = (package_renderer / "renderer.bundle.js").read_bytes() + b"\n// substituted"
    manifest = {
        "bootstrap_sha256": hashlib.sha256(bootstrap).hexdigest(),
        "build_tool_id": "patent-analysis.renderer-bundler",
        "build_tool_version": "1.0.1",
        "echarts_version": "6.1.0",
        "renderer_build_manifest_version": "1.0.0",
        "renderer_bundle_sha256": hashlib.sha256(bundle).hexdigest(),
        "renderer_protocol_version": "1.0.0",
    }
    (fixture_root / "bootstrap.js").write_bytes(bootstrap)
    (fixture_root / "renderer.bundle.js").write_bytes(bundle)
    (fixture_root / "renderer-build-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    monkeypatch.setattr(module, "_renderer_resource_root", lambda: fixture_root)

    with pytest.raises(module.RendererProtocolError):
        module.load_verified_renderer_resources()


@pytest.mark.parametrize(
    ("name", "expected_digest"),
    [
        (
            "renderer-build-manifest.schema.json",
            "c9c0cf2581b5467fe5941672093ab26ebacf9f5d33d4c218c9ee0e61077f8b2b",
        ),
        (
            "renderer-request.schema.json",
            "cefcb2c0e7bfb295d99b9a284078917e2aa7234fd881ba725b69eef19a8ba0cd",
        ),
        (
            "renderer-response.schema.json",
            "ce39d618d39ca29b0451a58fa6fda2c5da1c3de874b7a6da99f71c6df075e72b",
        ),
    ],
)
def test_schema_bytes_are_descriptor_checked_and_digest_pinned(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    expected_digest: str,
) -> None:
    module = _resources_module()
    loader = getattr(module, "_load_verified_renderer_schema_bytes", None)
    assert callable(loader), "missing descriptor-checked schema loader"
    package_schemas = Path(module.__file__).parent / "schemas"
    fixture_root = tmp_path / "schemas"
    fixture_root.mkdir()
    original = (package_schemas / name).read_bytes()
    (fixture_root / name).write_bytes(original)
    monkeypatch.setattr(module, "_schema_resource_root", lambda: fixture_root)

    assert hashlib.sha256(loader(name)).hexdigest() == expected_digest
    (fixture_root / name).write_bytes(original + b" ")
    with pytest.raises(module.RendererProtocolError):
        loader(name)


def test_resource_reader_rejects_symlink(tmp_path: Path) -> None:
    module = _resources_module()
    target = tmp_path / "target.bin"
    target.write_bytes(b"safe")
    link = tmp_path / "link.bin"
    try:
        link.symlink_to(target)
    except OSError as error:
        pytest.skip(f"symlink unavailable: {type(error).__name__}")

    with pytest.raises(module.RendererProtocolError):
        module._read_verified_resource(link, 4)


def test_resource_reader_rejects_opened_identity_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _resources_module()
    target = tmp_path / "target.bin"
    target.write_bytes(b"safe")
    monkeypatch.setattr(module.os.path, "samestat", lambda _left, _right: False)
    with pytest.raises(module.RendererProtocolError):
        module._read_verified_resource(target, 4)


def test_resource_reader_rejects_windows_reparse_attribute_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _resources_module()
    target = tmp_path / "target.bin"
    target.write_bytes(b"safe")
    original_lstat = Path.lstat

    def reparse_lstat(path: Path):
        result = original_lstat(path)
        if path != target:
            return result
        return SimpleNamespace(
            st_mode=result.st_mode,
            st_file_attributes=0x0400,
        )

    monkeypatch.setattr(Path, "lstat", reparse_lstat)
    with pytest.raises(module.RendererProtocolError):
        module._read_verified_resource(target, 4)


def test_resource_reader_rejects_opened_descriptor_reparse_attribute(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _resources_module()
    target = tmp_path / "target.bin"
    target.write_bytes(b"safe")
    original_fstat = module.os.fstat

    class ReparseStat:
        st_file_attributes = 0x0400

        def __init__(self, wrapped: object) -> None:
            self._wrapped = wrapped

        def __getattr__(self, name: str):
            return getattr(self._wrapped, name)

    monkeypatch.setattr(module.os, "fstat", lambda fd: ReparseStat(original_fstat(fd)))

    with pytest.raises(module.RendererProtocolError):
        module._read_verified_resource(target, 4)


def test_resource_reader_reads_limit_plus_one_and_rejects_one_over(tmp_path: Path) -> None:
    module = _resources_module()
    exact = tmp_path / "exact.bin"
    exact.write_bytes(b"x" * 16)
    one_over = tmp_path / "one-over.bin"
    one_over.write_bytes(b"x" * 17)

    assert module._read_verified_resource(exact, 16) == b"x" * 16
    with pytest.raises(module.RendererProtocolError):
        module._read_verified_resource(one_over, 16)


def test_renderer_package_is_internal_and_has_no_root_export() -> None:
    renderer_package = importlib.import_module("patent_analysis.renderer")
    package = importlib.import_module("patent_analysis")

    assert getattr(renderer_package, "__all__", None) == [], "missing internal package boundary"
    assert not hasattr(package, "load_verified_renderer_resources")
    assert not hasattr(package, "encode_renderer_frame")
    assert not hasattr(package, "decode_renderer_response")
