from __future__ import annotations

import hashlib
import importlib
import json
import os
import shutil
import stat
import subprocess
import sys
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

import pytest

from patent_analysis._render_canonical import canonical_json_bytes
from patent_analysis._version import PACKAGE_VERSION
from patent_analysis.analysis import _canonical_sha256 as result_sha256

pytestmark = pytest.mark.skipif(
    sys.platform not in {"win32", "darwin"},
    reason="trusted-local rendering contract is Windows x64 or macOS",
)


def _load_modules():
    try:
        errors = importlib.import_module("patent_analysis.render_errors")
        rendering = importlib.import_module("patent_analysis.rendering")
    except ModuleNotFoundError:
        return None, None
    return errors, rendering


def _trusted_renderer_node() -> Path:
    candidate = os.environ.get("PATENT_ANALYSIS_TEST_NODE") or shutil.which("node")
    if candidate is None:
        pytest.skip("exact Node 22.19.0 installation is unavailable")
    try:
        node = Path(candidate).resolve(strict=True)
        version = subprocess.run(
            [os.fspath(node), "--version"],
            capture_output=True,
            check=False,
            text=True,
            timeout=5.0,
        )
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        pytest.skip("exact Node 22.19.0 installation is unavailable")
    if version.returncode != 0 or version.stdout.strip() != "v22.19.0":
        pytest.skip("exact Node 22.19.0 installation is unavailable")
    return node


def _analysis_envelope() -> dict[str, object]:
    result = {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "count", "column": None},
        "population": {"input_rows": 3, "analyzed_rows": 3},
        "rows": [
            {
                "row_kind": "dimension_value",
                "label": "甲社",
                "value": 2,
                "count": 2,
                "share": 2 / 3,
            },
            {
                "row_kind": "remainder",
                "label": "その他",
                "value": 1,
                "count": 1,
                "share": 1 / 3,
            },
        ],
        "warnings": [],
    }
    return {
        "analysis_contract_version": "1.0.0",
        "ok": True,
        "result": result,
        "receipt": {
            "algorithm_id": "ranking.v1",
            "package_version": PACKAGE_VERSION,
            "input_sha256": "1" * 64,
            "spec_sha256": "2" * 64,
            "result_sha256": result_sha256(result),
        },
    }


def _analysis_bytes() -> bytes:
    return json.dumps(_analysis_envelope(), ensure_ascii=False).encode("utf-8")


def _assert_safe(error: Exception, secret: str = "secret-input") -> None:
    surfaces = "\n".join(
        [str(error), repr(error), repr(vars(error)), "".join(traceback.format_exception(error))]
    )
    assert secret not in surfaces
    assert error.retryable is False  # type: ignore[attr-defined]
    assert error.details == {}  # type: ignore[attr-defined]
    assert error.__cause__ is None
    assert error.__context__ is None


def test_render_error_is_factory_only_and_has_five_fixed_safe_pairs() -> None:
    errors, _rendering = _load_modules()
    assert errors is not None
    with pytest.raises(TypeError):
        errors.RenderError("secret-input", code="attacker.code")

    expected = {
        "render.invalid": "Render input was rejected",
        "input.invalid": "Render input could not be read or parsed",
        "usage.invalid": "Invalid patent-analysis render arguments",
        "renderer.unavailable": "Trusted local renderer is unavailable",
        "output.conflict": "Render output conflicts with an existing artifact",
    }
    for code, message in expected.items():
        error = errors._make_render_error(code)
        assert error.code == code
        assert error.safe_message == message
        assert error.retryable is False
        assert error.details == {}
        assert str(error) == message
        assert message in repr(error)
        assert error.as_dict() == {
            "code": code,
            "message": message,
            "retryable": False,
            "details": {},
        }
        _assert_safe(error)


@pytest.mark.parametrize(
    "document",
    [
        b'{"x":1,"x":2}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b"[]",
        b"\xff",
    ],
)
def test_public_api_rejects_malformed_json_as_input_invalid(
    tmp_path: Path,
    document: bytes,
) -> None:
    errors, rendering = _load_modules()
    assert errors is not None and rendering is not None
    with pytest.raises(errors.RenderError) as captured:
        rendering.render_ranking_svg(document, output_directory=tmp_path)
    assert captured.value.code == "input.invalid"


def test_public_api_bounds_documents_before_json_construction(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    errors, rendering = _load_modules()
    assert errors is not None and rendering is not None
    reached: list[str] = []
    monkeypatch.setattr(
        rendering.json,
        "loads",
        lambda *_a, **_k: reached.append("json") or {},
    )

    for analysis, overlay in (
        (b" " * (16 * 1024 * 1024 + 1), None),
        (_analysis_bytes(), b" " * (4 * 1024 * 1024 + 1)),
    ):
        with pytest.raises(errors.RenderError) as captured:
            rendering.render_ranking_svg(
                analysis,
                overlay_document=overlay,
                output_directory=tmp_path,
            )
        assert captured.value.code == "input.invalid"
    assert reached == []


def test_semantic_contract_failure_maps_to_render_invalid(tmp_path: Path) -> None:
    errors, rendering = _load_modules()
    assert errors is not None and rendering is not None
    invalid = _analysis_envelope()
    invalid["ok"] = False

    with pytest.raises(errors.RenderError) as captured:
        rendering.render_ranking_svg(
            json.dumps(invalid).encode(),
            output_directory=tmp_path,
        )

    assert captured.value.code == "render.invalid"


@pytest.mark.parametrize("output", [r"relative\invalid", r"\\server\share\output"])
@pytest.mark.parametrize("node", [None, r"C:\missing\node.exe"])
def test_semantic_invalid_precedes_platform_output_and_node_cross_product(
    monkeypatch: pytest.MonkeyPatch,
    output: str,
    node: str | None,
) -> None:
    errors, rendering = _load_modules()
    assert errors is not None and rendering is not None
    invalid = _analysis_envelope()
    invalid["ok"] = False
    touched: list[str] = []

    def forbidden(name: str):
        def fail(*_args: object, **_kwargs: object) -> None:
            touched.append(name)
            raise AssertionError(f"semantic invalid reached {name}")

        return fail

    monkeypatch.setattr(rendering, "require_supported_platform", forbidden("platform"))
    monkeypatch.setattr(rendering, "validate_local_directory", forbidden("output"))
    monkeypatch.setattr(rendering, "resolve_node_executable", forbidden("node"))
    monkeypatch.setattr(rendering, "launch_trusted_node", forbidden("subprocess"))

    with pytest.raises(errors.RenderError) as captured:
        rendering.render_ranking_svg(
            json.dumps(invalid).encode(),
            output_directory=output,
            node_executable=node,
        )

    assert captured.value.code == "render.invalid"
    assert touched == []


def test_render_spec_semantic_failure_precedes_platform_output_and_node(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    errors, rendering = _load_modules()
    assert errors is not None and rendering is not None
    touched: list[str] = []
    monkeypatch.setattr(
        rendering,
        "build_ranking_render_spec",
        lambda **_kwargs: (_ for _ in ()).throw(rendering.RenderContractError()),
    )
    for name in (
        "require_supported_platform",
        "validate_local_directory",
        "resolve_node_executable",
        "launch_trusted_node",
    ):
        monkeypatch.setattr(
            rendering,
            name,
            lambda *_a, _name=name, **_k: touched.append(_name),
        )

    with pytest.raises(errors.RenderError) as captured:
        rendering.render_ranking_svg(
            _analysis_bytes(),
            output_directory=r"relative\invalid",
        )

    assert captured.value.code == "render.invalid"
    assert touched == []


@pytest.mark.parametrize(
    ("depth", "valid"),
    [(64, True), (65, False)],
)
def test_json_preflight_depth_exact_and_one_over(depth: int, valid: bool) -> None:
    errors, rendering = _load_modules()
    assert errors is not None and rendering is not None
    arrays = depth - 1
    raw = b'{"x":' + b"[" * arrays + b"0" + b"]" * arrays + b"}"

    if valid:
        assert isinstance(rendering._parse_document(raw, len(raw)), dict)
    else:
        with pytest.raises(errors.RenderError) as captured:
            rendering._parse_document(raw, len(raw))
        assert captured.value.code == "input.invalid"


@pytest.mark.parametrize(
    ("token_count", "valid"),
    [(250_000, True), (250_001, False)],
)
def test_json_preflight_token_exact_and_one_over(token_count: int, valid: bool) -> None:
    errors, rendering = _load_modules()
    assert errors is not None and rendering is not None
    value_count = token_count - 3
    raw = b'{"x":[' + b",".join([b"null"] * value_count) + b"]}"

    if valid:
        assert isinstance(rendering._parse_document(raw, len(raw)), dict)
    else:
        with pytest.raises(errors.RenderError) as captured:
            rendering._parse_document(raw, len(raw))
        assert captured.value.code == "input.invalid"


@pytest.mark.parametrize(
    ("total_code_points", "valid"),
    [(2_000_000, True), (2_000_001, False)],
)
def test_json_preflight_decoded_string_exact_and_one_over(
    total_code_points: int,
    valid: bool,
) -> None:
    errors, rendering = _load_modules()
    assert errors is not None and rendering is not None
    raw = b'{"x":"' + b"a" * (total_code_points - 1) + b'"}'

    if valid:
        assert isinstance(rendering._parse_document(raw, len(raw)), dict)
    else:
        with pytest.raises(errors.RenderError) as captured:
            rendering._parse_document(raw, len(raw))
        assert captured.value.code == "input.invalid"


@pytest.mark.parametrize(
    ("lexeme_bytes", "valid"),
    [(128, True), (129, False)],
)
def test_json_preflight_numeric_lexeme_exact_and_one_over(
    monkeypatch: pytest.MonkeyPatch,
    lexeme_bytes: int,
    valid: bool,
) -> None:
    errors, rendering = _load_modules()
    assert errors is not None and rendering is not None
    raw = b'{"n":' + b"1" + b"0" * (lexeme_bytes - 1) + b"}"
    parser_calls: list[bytes] = []
    original_parser = getattr(rendering, "_parse_json_object", None)

    if original_parser is not None:
        monkeypatch.setattr(
            rendering,
            "_parse_json_object",
            lambda value: parser_calls.append(value) or original_parser(value),
        )

    if valid:
        assert isinstance(rendering._parse_document(raw, len(raw)), dict)
        if original_parser is not None:
            assert parser_calls == [raw]
    else:
        with pytest.raises(errors.RenderError) as captured:
            rendering._parse_document(raw, len(raw))
        assert captured.value.code == "input.invalid"
        assert parser_calls == []


@pytest.mark.parametrize(
    "raw",
    [
        b'{"x":1,"x":2}',
        b'{"x":"nul\x00value"}',
        b"[]",
        b"\xff",
    ],
)
def test_json_preflight_rejects_duplicate_nul_nonobject_and_invalid_utf8(raw: bytes) -> None:
    errors, rendering = _load_modules()
    assert errors is not None and rendering is not None

    with pytest.raises(errors.RenderError) as captured:
        rendering._parse_document(raw, len(raw))

    assert captured.value.code == "input.invalid"


def test_json_preflight_accepts_raw_japanese_utf8_and_noncanonical_whitespace() -> None:
    _errors, rendering = _load_modules()
    assert rendering is not None
    raw = '  { "見出し" : "出願人", "値" : [1, 2] } \r\n'.encode()

    assert rendering._parse_document(raw, len(raw)) == {
        "見出し": "出願人",
        "値": [1, 2],
    }


@pytest.mark.parametrize("mutation", ["nfd", "unsafe-integer"])
def test_builder_semantics_continue_to_reject_nfd_and_unsafe_integer(
    tmp_path: Path,
    mutation: str,
) -> None:
    errors, rendering = _load_modules()
    assert errors is not None and rendering is not None
    envelope = _analysis_envelope()
    result = envelope["result"]
    receipt = envelope["receipt"]
    assert isinstance(result, dict) and isinstance(receipt, dict)
    rows = result["rows"]
    assert isinstance(rows, list) and isinstance(rows[0], dict)
    if mutation == "nfd":
        rows[0]["label"] = "e\u0301"
    else:
        rows[0]["value"] = 2**53
    receipt["result_sha256"] = result_sha256(result)

    with pytest.raises(errors.RenderError) as captured:
        rendering.render_ranking_svg(
            json.dumps(envelope, ensure_ascii=False).encode(),
            output_directory=tmp_path,
        )

    assert captured.value.code == "render.invalid"
    assert list(tmp_path.iterdir()) == []


def test_render_composition_uses_existing_builders_and_exact_canonical_frame_once(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    errors, rendering = _load_modules()
    assert errors is not None and rendering is not None
    calls: list[tuple[str, object]] = []
    model = {"chart_model_contract_version": "1.0.0", "rows": []}
    model_bytes = canonical_json_bytes(model)
    spec = {"render_spec_contract_version": "1.0.0"}
    spec_bytes = canonical_json_bytes(spec)
    receipt = {
        "chart_model_sha256": hashlib.sha256(model_bytes).hexdigest(),
        "chart_model_bytes": __import__("base64").b64encode(model_bytes).decode(),
    }

    def build_model(value: object, *, overlay: object = None):
        calls.append(("model", (value, overlay)))
        return model, receipt

    def build_spec(*, row_count: int, palette: str | None = None):
        calls.append(("spec", row_count))
        return spec

    class Resources:
        bootstrap_bytes = b"bootstrap"
        bundle_bytes = b"bundle"
        renderer_build_digest = "d" * 64
        runtime = object()

    monkeypatch.setattr(rendering, "build_ranking_chart_model", build_model)
    monkeypatch.setattr(rendering, "build_ranking_render_spec", build_spec)
    monkeypatch.setattr(rendering, "load_verified_renderer_resources", Resources)
    monkeypatch.setattr(
        rendering,
        "build_renderer_request",
        lambda got_model, got_spec, _resources: calls.append(
            ("frame", (got_model, got_spec))
        )
        or b"frame",
    )
    monkeypatch.setattr(rendering, "resolve_node_executable", lambda _value: Path("C:/node.exe"))
    monkeypatch.setattr(rendering, "validate_local_directory", lambda value: Path(value))
    monkeypatch.setattr(
        rendering,
        "run_bound_renderer",
        lambda launcher, frame, binding, **_kw: calls.append(("run", (launcher, frame, binding)))
        or b"<svg/>\n",
    )
    monkeypatch.setattr(rendering, "_publish_svg", lambda *_a, **_k: "created")

    response = rendering.render_ranking_svg(
        _analysis_bytes(),
        output_directory=tmp_path,
        node_executable=r"C:\node.exe",
    )

    assert [name for name, _value in calls] == ["model", "spec", "frame", "run"]
    assert calls[2] == ("frame", (model_bytes, spec_bytes))
    assert response["status"] == "created"


def test_artifact_identity_receipt_created_reused_and_conflict(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    errors, rendering = _load_modules()
    assert errors is not None and rendering is not None
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"/>\n'
    monkeypatch.setattr(
        rendering,
        "_render_svg",
        lambda *_a, **_k: (
            "a" * 64,
            "b" * 64,
            "c" * 64,
            svg,
        ),
    )

    created = rendering.render_ranking_svg(
        _analysis_bytes(), output_directory=tmp_path, node_executable=r"C:\node.exe"
    )
    expected_svg_hash = hashlib.sha256(svg).hexdigest()
    expected_id = hashlib.sha256(
        canonical_json_bytes(
            {
                "chart_model_sha256": "a" * 64,
                "render_spec_sha256": "b" * 64,
                "renderer_build_digest": "c" * 64,
                "svg_sha256": expected_svg_hash,
            }
        )
    ).hexdigest()
    expected_name = f"ranking-svg-{expected_id}.svg"
    assert created == {
        "render_contract_version": "1.0.0",
        "ok": True,
        "status": "created",
        "artifact_id": expected_id,
        "svg": expected_name,
        "svg_sha256": expected_svg_hash,
        "renderer_build_digest": "c" * 64,
    }
    assert (tmp_path / expected_name).read_bytes() == svg
    assert rendering.render_ranking_svg(
        _analysis_bytes(), output_directory=tmp_path, node_executable=r"C:\node.exe"
    )["status"] == "reused"

    (tmp_path / expected_name).write_bytes(b"different")
    with pytest.raises(errors.RenderError) as captured:
        rendering.render_ranking_svg(
            _analysis_bytes(), output_directory=tmp_path, node_executable=r"C:\node.exe"
        )
    assert captured.value.code == "output.conflict"
    assert (tmp_path / expected_name).read_bytes() == b"different"


def test_existing_artifact_reparse_is_rejected_before_open(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    errors, rendering = _load_modules()
    assert errors is not None and rendering is not None
    opened: list[Path] = []
    monkeypatch.setattr(
        Path,
        "lstat",
        lambda _self: SimpleNamespace(
            st_mode=stat.S_IFLNK,
            st_file_attributes=0x0400,
        ),
    )
    monkeypatch.setattr(
        Path,
        "open",
        lambda self, *_a, **_k: opened.append(self) or (_ for _ in ()).throw(
            AssertionError("reparse artifact was opened")
        ),
    )

    with pytest.raises(errors.RenderError) as captured:
        rendering._publish_svg(tmp_path, "ranking-svg-test.svg", b"same")

    assert captured.value.code == "output.conflict"
    assert captured.value.__context__ is None
    assert opened == []


def test_publish_never_uses_following_exists_or_stat_for_missing_final(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _errors, rendering = _load_modules()
    assert rendering is not None

    final = tmp_path / "ranking-svg-test.svg"
    calls: list[str] = []
    original_exists = Path.exists
    original_stat = Path.stat

    def exists_spy(self: Path) -> bool:
        if self == final:
            calls.append("exists")
        return original_exists(self)

    def stat_spy(self: Path, *, follow_symlinks: bool = True) -> os.stat_result:
        if self == final:
            calls.append("stat")
        return original_stat(self, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(Path, "exists", exists_spy)
    monkeypatch.setattr(Path, "stat", stat_spy)

    assert rendering._publish_svg(tmp_path, "ranking-svg-test.svg", b"same") == "created"
    assert final.read_bytes() == b"same"
    assert calls == []


def test_publish_lstat_oserror_maps_to_safe_conflict_without_path_or_context(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    errors, rendering = _load_modules()
    assert errors is not None and rendering is not None
    secret = r"C:\Users\private\remote-target.svg"

    def failing_lstat(_self: Path) -> os.stat_result:
        raise OSError(secret)

    monkeypatch.setattr(Path, "lstat", failing_lstat)

    with pytest.raises(errors.RenderError) as captured:
        rendering._publish_svg(tmp_path, "ranking-svg-test.svg", b"same")

    error = captured.value
    assert error.code == "output.conflict"
    assert error.__cause__ is None
    assert error.__context__ is None
    assert secret not in str(error)
    assert secret not in repr(error)


def test_publish_rejects_real_symlink_without_following_target(tmp_path: Path) -> None:
    errors, rendering = _load_modules()
    assert errors is not None and rendering is not None
    output = tmp_path / "output"
    output.mkdir()
    target = tmp_path / "remote-target.svg"
    target.write_bytes(b"same")
    final = output / "ranking-svg-test.svg"
    try:
        final.symlink_to(target)
    except OSError as error:
        pytest.skip(f"real symlink unavailable: {type(error).__name__}")

    with pytest.raises(errors.RenderError) as captured:
        rendering._publish_svg(output, final.name, b"same")

    assert captured.value.code == "output.conflict"
    assert target.read_bytes() == b"same"
    assert final.is_symlink()


def test_publish_rejects_final_identity_change_after_open(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    errors, rendering = _load_modules()
    assert errors is not None and rendering is not None
    output = tmp_path / "output"
    output.mkdir()
    first = tmp_path / "first.svg"
    second = tmp_path / "second.svg"
    first.write_bytes(b"same")
    second.write_bytes(b"other")
    final = output / "ranking-svg-test.svg"
    original_lstat = Path.lstat
    original_open = Path.open
    final_lstats = 0

    def swapped_lstat(self: Path) -> os.stat_result:
        nonlocal final_lstats
        if self != final:
            return original_lstat(self)
        final_lstats += 1
        return original_lstat(first if final_lstats == 1 else second)

    def opened_old_file(self: Path, *args: object, **kwargs: object):
        if self == final:
            return original_open(first, *args, **kwargs)
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", swapped_lstat)
    monkeypatch.setattr(Path, "open", opened_old_file)

    with pytest.raises(errors.RenderError) as captured:
        rendering._publish_svg(output, final.name, b"same")

    assert captured.value.code == "output.conflict"
    assert final_lstats >= 2


@pytest.mark.parametrize(("winner", "expected"), [(b"same", "reused"), (b"other", None)])
def test_concurrent_publish_winner_is_revalidated_and_own_temp_is_removed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    winner: bytes,
    expected: str | None,
) -> None:
    errors, rendering = _load_modules()
    assert errors is not None and rendering is not None
    final = tmp_path / "ranking-svg-test.svg"
    fsync_calls: list[int] = []

    def concurrent_publish(_source: Path, destination: Path, **_kwargs: object) -> None:
        Path(destination).write_bytes(winner)
        raise FileExistsError

    monkeypatch.setattr(rendering.os, "rename" if os.name == "nt" else "link", concurrent_publish)
    monkeypatch.setattr(rendering.os, "fsync", lambda fd: fsync_calls.append(fd))
    if expected is None:
        with pytest.raises(errors.RenderError) as captured:
            rendering._publish_svg(tmp_path, final.name, b"same")
        assert captured.value.code == "output.conflict"
        assert captured.value.__cause__ is None
        assert captured.value.__context__ is None
    else:
        assert rendering._publish_svg(tmp_path, final.name, b"same") == expected
    assert fsync_calls
    assert not list(tmp_path.glob("*.tmp"))
    assert final.read_bytes() == winner


@pytest.mark.parametrize(
    "output",
    [r"relative\output", r"\\server\share\output", r"\\?\C:\output"],
)
def test_output_requires_existing_absolute_local_non_reparse_directory(
    output: str,
) -> None:
    errors, rendering = _load_modules()
    assert errors is not None and rendering is not None
    with pytest.raises(errors.RenderError) as captured:
        rendering.render_ranking_svg(_analysis_bytes(), output_directory=output)
    assert captured.value.code == "output.conflict"


def test_non_windows_platform_wins_before_output_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    errors, rendering = _load_modules()
    assert errors is not None and rendering is not None
    monkeypatch.setattr(
        rendering,
        "require_supported_platform",
        lambda: (_ for _ in ()).throw(rendering.LocalRendererError()),
    )

    with pytest.raises(errors.RenderError) as captured:
        rendering.render_ranking_svg(
            _analysis_bytes(),
            output_directory=r"relative\invalid",
        )

    assert captured.value.code == "renderer.unavailable"
    assert captured.value.__cause__ is None
    assert captured.value.__context__ is None


def test_receipt_and_errors_never_expose_absolute_path_or_stderr(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    errors, rendering = _load_modules()
    assert errors is not None and rendering is not None
    secret = "secret-label C:\\Users\\user\\private.json"
    monkeypatch.setattr(
        rendering,
        "_render_svg",
        lambda *_a, **_k: (_ for _ in ()).throw(ValueError(secret)),
    )

    with pytest.raises(errors.RenderError) as captured:
        rendering.render_ranking_svg(
            _analysis_bytes(), output_directory=tmp_path, node_executable=r"C:\node.exe"
        )
    _assert_safe(captured.value, secret)


@pytest.mark.skipif(
    sys.platform not in {"win32", "darwin"},
    reason="trusted-local v1 is Windows x64 or macOS",
)
def test_real_packaged_node_renderer_creates_parseable_svg_and_reuses(tmp_path: Path) -> None:
    errors, rendering = _load_modules()
    assert errors is not None and rendering is not None
    node = _trusted_renderer_node()
    analysis = _analysis_envelope()
    analysis["result"]["dimension"] = '出願人 <&> "引用"'
    analysis["receipt"]["result_sha256"] = result_sha256(analysis["result"])
    document = json.dumps(analysis, ensure_ascii=False).encode()

    first = rendering.render_ranking_svg(
        document, output_directory=tmp_path, node_executable=node
    )
    second = rendering.render_ranking_svg(
        document, output_directory=tmp_path, node_executable=node
    )

    assert first["status"] == "created"
    assert second == {**first, "status": "reused"}
    root = ET.fromstring((tmp_path / str(first["svg"])).read_bytes())
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    assert root.attrib["role"] == "img"
    for attribute, tag in (("aria-labelledby", "title"), ("aria-describedby", "desc")):
        element = root.find(f"{{http://www.w3.org/2000/svg}}{tag}")
        assert element is not None and element.text
        assert element.attrib["id"] == root.attrib[attribute]
    assert root.find("{http://www.w3.org/2000/svg}title").text == '出願人 <&> "引用"のランキング'
