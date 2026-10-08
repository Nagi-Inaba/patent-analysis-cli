from __future__ import annotations

import importlib
import os
import traceback
from pathlib import Path
from types import SimpleNamespace

import pytest

from patent_analysis import AnalysisContractError, DatasetInputError, analyze_csv, inspect_csv


def _access_module():
    return importlib.import_module("patent_analysis.access")


def _write_csv(path: Path) -> None:
    path.write_text("a,b\n1,2\n", encoding="utf-8")


def _spec() -> dict[str, object]:
    return {
        "analysis_type": "ranking",
        "dimension": "a",
        "measure": {"mode": "count", "column": None},
        "top_n": 10,
        "include_other": False,
        "multi_value_mode": "all",
    }


def test_inspect_csv_requires_keyword_only_allowed_root(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    _write_csv(source)

    with pytest.raises(TypeError):
        inspect_csv(source)
    with pytest.raises(TypeError):
        inspect_csv(source, tmp_path)
    with pytest.raises(TypeError):
        analyze_csv(source, _spec())
    with pytest.raises(TypeError):
        analyze_csv(source, _spec(), tmp_path)


@pytest.mark.parametrize("surface", ["inspect", "analyze"])
@pytest.mark.parametrize("root_kind", ["none", "empty", "relative", "missing", "file"])
def test_invalid_allowed_root_fails_closed(
    tmp_path: Path,
    root_kind: str,
    surface: str,
) -> None:
    source = tmp_path / "input.csv"
    _write_csv(source)
    roots: dict[str, object] = {
        "none": None,
        "empty": "",
        "relative": "relative-root",
        "missing": tmp_path / "missing-root",
        "file": source,
    }

    with pytest.raises(DatasetInputError) as caught:
        if surface == "inspect":
            inspect_csv(source, allowed_root=roots[root_kind])  # type: ignore[arg-type]
        else:
            analyze_csv(
                source,
                _spec(),
                allowed_root=roots[root_kind],  # type: ignore[arg-type]
            )

    assert caught.value.code == "input.invalid"
    assert caught.value.details == {}


@pytest.mark.parametrize("allowed_root", [None, "TASK-5A-RELATIVE-SECRET-ROOT"])
def test_analyze_csv_rejects_invalid_root_before_invalid_spec_without_leakage(
    tmp_path: Path,
    allowed_root: object,
) -> None:
    source = tmp_path / "input.csv"
    _write_csv(source)
    secret = "TASK-5A-INVALID-SPEC-SECRET"
    invalid_spec = {"analysis_type": "ranking", "dimension": secret, "top_n": 0}

    with pytest.raises(DatasetInputError) as caught:
        analyze_csv(
            source,
            invalid_spec,
            allowed_root=allowed_root,  # type: ignore[arg-type]
        )

    error = caught.value
    rendered = "".join(traceback.format_exception(error))
    assert error.code == "input.invalid"
    assert error.details == {}
    assert error.__cause__ is None
    assert error.__context__ is None
    assert secret not in repr(error)
    assert secret not in repr(error.as_dict())
    assert secret not in rendered
    assert "TASK-5A-RELATIVE-SECRET-ROOT" not in rendered


def test_analyze_csv_with_valid_root_keeps_invalid_spec_contract_error(
    tmp_path: Path,
) -> None:
    source = tmp_path / "input.csv"
    _write_csv(source)
    invalid_spec = {"analysis_type": "ranking", "dimension": "secret", "top_n": 0}

    with pytest.raises(AnalysisContractError) as caught:
        analyze_csv(source, invalid_spec, allowed_root=tmp_path)

    assert caught.value.code == "analysis.invalid"


def test_relative_source_is_resolved_against_approved_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "approved"
    root.mkdir()
    source = root / "input.csv"
    _write_csv(source)
    monkeypatch.chdir(tmp_path)

    manifest = inspect_csv("input.csv", allowed_root=root)

    assert manifest["row_count"] == 1


@pytest.mark.parametrize("source_kind", ["outside", "sibling", "dotdot"])
def test_source_escape_is_rejected_without_private_path_leakage(
    tmp_path: Path,
    source_kind: str,
) -> None:
    root = tmp_path / "approved"
    sibling = tmp_path / "approved-sibling"
    root.mkdir()
    sibling.mkdir()
    outside = tmp_path / "TASK-5A-OUTSIDE.csv"
    sibling_source = sibling / "TASK-5A-SIBLING.csv"
    _write_csv(outside)
    _write_csv(sibling_source)
    sources = {
        "outside": outside,
        "sibling": sibling_source,
        "dotdot": Path("..") / outside.name,
    }

    with pytest.raises(DatasetInputError) as caught:
        inspect_csv(sources[source_kind], allowed_root=root)

    rendered = repr(caught.value)
    assert "TASK-5A-OUTSIDE" not in rendered
    assert "TASK-5A-SIBLING" not in rendered


@pytest.mark.parametrize(
    "raw_source",
    [
        r"\\server\share\private.csv",
        r"\\?\C:\private.csv",
        r"\\.\C:\private.csv",
        r"C:\private.csv:secret",
    ],
)
def test_namespace_and_ads_sources_are_rejected_before_filesystem_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    raw_source: str,
) -> None:
    access = _access_module()

    def unexpected_lstat(path: Path):
        raise AssertionError(f"filesystem was touched: {path}")

    monkeypatch.setattr(access, "_lstat", unexpected_lstat)

    with pytest.raises(DatasetInputError):
        inspect_csv(raw_source, allowed_root=tmp_path)


def test_source_symlink_is_rejected_when_creation_is_available(tmp_path: Path) -> None:
    root = tmp_path / "approved"
    root.mkdir()
    target = root / "target.csv"
    link = root / "link.csv"
    _write_csv(target)
    try:
        link.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {type(exc).__name__}")

    with pytest.raises(DatasetInputError):
        inspect_csv(link, allowed_root=root)


def test_root_symlink_is_rejected_when_creation_is_available(tmp_path: Path) -> None:
    target = tmp_path / "target-root"
    target.mkdir()
    source = target / "input.csv"
    _write_csv(source)
    root_link = tmp_path / "root-link"
    try:
        root_link.symlink_to(target, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlink creation unavailable: {type(exc).__name__}")

    with pytest.raises(DatasetInputError):
        inspect_csv(source, allowed_root=root_link)


@pytest.mark.parametrize("reparse_kind", ["file", "directory"])
def test_windows_reparse_attribute_is_rejected_deterministically(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    reparse_kind: str,
) -> None:
    access = _access_module()
    root = tmp_path / "approved"
    root.mkdir()
    source = root / "input.csv"
    _write_csv(source)
    reparse_path = source if reparse_kind == "file" else root
    original_lstat = access._lstat

    def reparse_lstat(path: Path):
        result = original_lstat(path)
        if path != reparse_path:
            return result
        return SimpleNamespace(
            st_file_attributes=0x0400,
            st_mode=result.st_mode,
            st_size=result.st_size,
        )

    monkeypatch.setattr(access, "_lstat", reparse_lstat)

    with pytest.raises(DatasetInputError):
        inspect_csv(source, allowed_root=root)


def test_preopen_and_opened_file_identity_mismatch_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    access = _access_module()
    source = tmp_path / "input.csv"
    _write_csv(source)
    monkeypatch.setattr(access.os.path, "samestat", lambda _left, _right: False)

    with pytest.raises(DatasetInputError):
        inspect_csv(source, allowed_root=tmp_path)


@pytest.mark.skipif(os.name != "nt", reason="Windows handle final-path control")
def test_windows_open_handle_final_path_outside_root_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    access = _access_module()
    root = tmp_path / "approved"
    root.mkdir()
    source = root / "input.csv"
    _write_csv(source)
    outside = tmp_path / "outside.csv"
    _write_csv(outside)
    monkeypatch.setattr(access, "_windows_final_path_from_file", lambda _file: outside)

    with pytest.raises(DatasetInputError):
        inspect_csv(source, allowed_root=root)


@pytest.mark.skipif(os.name != "nt", reason="Windows root handle final-path control")
def test_windows_root_handle_final_path_identity_mismatch_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    access = _access_module()
    root = tmp_path / "approved"
    root.mkdir()
    source = root / "input.csv"
    _write_csv(source)
    different_directory = tmp_path / "different"
    different_directory.mkdir()
    monkeypatch.setattr(
        access,
        "_windows_final_path_from_directory",
        lambda _path: different_directory,
    )

    with pytest.raises(DatasetInputError):
        inspect_csv(source, allowed_root=root)


@pytest.mark.skipif(os.name != "nt", reason="Windows drive classification")
def test_windows_remote_root_wrapper_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    access = _access_module()
    source = tmp_path / "input.csv"
    _write_csv(source)
    monkeypatch.setattr(access, "_windows_drive_is_local", lambda _path: False)
    monkeypatch.setattr(
        access,
        "_lstat",
        lambda _path: (_ for _ in ()).throw(AssertionError("remote path touched")),
    )

    with pytest.raises(DatasetInputError):
        inspect_csv(source, allowed_root=tmp_path)


@pytest.mark.skipif(os.name != "nt", reason="Windows SUBST classification")
def test_windows_subst_root_wrapper_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    access = _access_module()
    source = tmp_path / "input.csv"
    _write_csv(source)
    monkeypatch.setattr(access, "_windows_drive_is_subst", lambda _path: True)
    monkeypatch.setattr(
        access,
        "_lstat",
        lambda _path: (_ for _ in ()).throw(AssertionError("SUBST path touched")),
    )

    with pytest.raises(DatasetInputError):
        inspect_csv(source, allowed_root=tmp_path)
