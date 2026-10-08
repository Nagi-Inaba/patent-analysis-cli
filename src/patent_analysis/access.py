from __future__ import annotations

import ctypes
import ntpath
import os
import stat
from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import BinaryIO

from patent_analysis.errors import DatasetInputError

_FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
_DRIVE_FIXED = 3
_FILE_READ_ATTRIBUTES = 0x0080
_FILE_SHARE_ALL = 0x00000001 | 0x00000002 | 0x00000004
_OPEN_EXISTING = 3
_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


class _AccessRejected(Exception):
    pass


@dataclass(frozen=True)
class _ApprovedRoot:
    lexical: Path
    final: Path


def _coerce_path_text(value: str | os.PathLike[str] | object) -> str:
    raw = os.fspath(value)  # type: ignore[arg-type]
    if not isinstance(raw, str) or not raw.strip() or "\x00" in raw:
        raise _AccessRejected
    return raw


def _validate_raw_path(raw: str) -> None:
    normalized = raw.replace("/", "\\")
    lowered = normalized.lower()
    if lowered.startswith(("\\\\", "\\??\\", "\\?\\", "\\.\\")):
        raise _AccessRejected

    drive, tail = ntpath.splitdrive(normalized)
    if drive:
        if not tail.startswith("\\"):
            raise _AccessRejected
        if ":" in tail:
            raise _AccessRejected
    elif ":" in normalized:
        raise _AccessRejected


def _contains_parent_reference(raw: str) -> bool:
    return ".." in PurePath(raw).parts


def _normalize_absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.path.normpath(os.fspath(path))))


def _is_within(root: Path, candidate: Path) -> bool:
    try:
        root_text = os.path.normcase(os.fspath(root))
        candidate_text = os.path.normcase(os.fspath(candidate))
        return os.path.commonpath((root_text, candidate_text)) == root_text
    except ValueError:
        return False


def _lstat(path: Path) -> os.stat_result:
    return path.lstat()


def _is_reparse_or_symlink(path: Path, result: os.stat_result) -> bool:
    attributes = getattr(result, "st_file_attributes", 0)
    return bool(attributes & _FILE_ATTRIBUTE_REPARSE_POINT) or stat.S_ISLNK(result.st_mode)


def _path_components(path: Path) -> list[Path]:
    parts = path.parts
    if not parts:
        return []
    current = Path(parts[0])
    components = [current]
    for part in parts[1:]:
        current = current / part
        components.append(current)
    return components


def _ensure_no_reparse_components(path: Path) -> os.stat_result:
    final_result: os.stat_result | None = None
    for component in _path_components(path):
        final_result = _lstat(component)
        if _is_reparse_or_symlink(component, final_result):
            raise _AccessRejected
    if final_result is None:
        raise _AccessRejected
    return final_result


def _windows_kernel32():
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    from ctypes import wintypes

    kernel32.GetDriveTypeW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetDriveTypeW.restype = wintypes.UINT
    kernel32.QueryDosDeviceW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    kernel32.QueryDosDeviceW.restype = wintypes.DWORD
    kernel32.GetFinalPathNameByHandleW.argtypes = [
        wintypes.HANDLE,
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
    ]
    kernel32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    return kernel32


def _windows_drive_is_local(path: Path) -> bool:
    if os.name != "nt":
        return True
    anchor = path.anchor
    if not anchor:
        return False
    return int(_windows_kernel32().GetDriveTypeW(anchor)) == _DRIVE_FIXED


def _windows_drive_is_subst(path: Path) -> bool:
    if os.name != "nt":
        return False
    drive = path.drive
    if not drive:
        return True
    buffer = ctypes.create_unicode_buffer(32768)
    result = _windows_kernel32().QueryDosDeviceW(drive, buffer, len(buffer))
    if result == 0:
        raise OSError(ctypes.get_last_error(), "drive mapping query failed")
    target = buffer.value
    return target.startswith("\\??\\")


def _normalize_windows_final_path(raw: str) -> Path:
    lowered = raw.lower()
    if lowered.startswith("\\\\?\\unc\\"):
        raise _AccessRejected
    if lowered.startswith("\\\\?\\"):
        raw = raw[4:]
    _validate_raw_path(raw)
    final_path = _normalize_absolute(Path(raw))
    if not final_path.is_absolute():
        raise _AccessRejected
    return final_path


def _windows_final_path_from_handle(handle: int) -> Path:
    kernel32 = _windows_kernel32()
    buffer_size = 32768
    buffer = ctypes.create_unicode_buffer(buffer_size)
    length = kernel32.GetFinalPathNameByHandleW(handle, buffer, buffer_size, 0)
    if length == 0 or length >= buffer_size:
        raise OSError(ctypes.get_last_error(), "final path query failed")
    return _normalize_windows_final_path(buffer.value)


def _windows_final_path_from_file(file: BinaryIO) -> Path:
    if os.name != "nt":
        raise _AccessRejected
    import msvcrt

    return _windows_final_path_from_handle(msvcrt.get_osfhandle(file.fileno()))


def _windows_final_path_from_directory(path: Path) -> Path:
    if os.name != "nt":
        return path
    kernel32 = _windows_kernel32()
    handle = kernel32.CreateFileW(
        os.fspath(path),
        _FILE_READ_ATTRIBUTES,
        _FILE_SHARE_ALL,
        None,
        _OPEN_EXISTING,
        _FILE_FLAG_BACKUP_SEMANTICS | _FILE_FLAG_OPEN_REPARSE_POINT,
        None,
    )
    if handle in (None, _INVALID_HANDLE_VALUE):
        raise OSError(ctypes.get_last_error(), "directory handle open failed")
    try:
        return _windows_final_path_from_handle(handle)
    finally:
        kernel32.CloseHandle(handle)


def _validate_allowed_root_impl(raw_root: str) -> _ApprovedRoot:
    root_path = Path(raw_root)
    if not root_path.is_absolute() or _contains_parent_reference(raw_root):
        raise _AccessRejected
    lexical_root = _normalize_absolute(root_path)
    if os.name == "nt":
        if not _windows_drive_is_local(lexical_root) or _windows_drive_is_subst(lexical_root):
            raise _AccessRejected
    root_stat = _ensure_no_reparse_components(lexical_root)
    if not stat.S_ISDIR(root_stat.st_mode):
        raise _AccessRejected

    final_root = lexical_root
    if os.name == "nt":
        final_root = _windows_final_path_from_directory(lexical_root)
        if not _windows_drive_is_local(final_root) or _windows_drive_is_subst(final_root):
            raise _AccessRejected
        final_stat = _ensure_no_reparse_components(final_root)
        if not os.path.samestat(root_stat, final_stat):
            raise _AccessRejected

    return _ApprovedRoot(lexical=lexical_root, final=final_root)


def _resolve_source_impl(raw_source: str, root: _ApprovedRoot) -> Path:
    if _contains_parent_reference(raw_source):
        raise _AccessRejected
    source_path = Path(raw_source)
    if source_path.is_absolute():
        candidate = _normalize_absolute(source_path)
    else:
        candidate = _normalize_absolute(root.lexical / source_path)
    if not _is_within(root.lexical, candidate):
        raise _AccessRejected
    return candidate


def _read_verified_bytes_impl(
    raw_source: str,
    raw_root: str,
    *,
    max_bytes: int,
) -> bytes:
    root = _validate_allowed_root_impl(raw_root)
    source = _resolve_source_impl(raw_source, root)
    pre_stat = _ensure_no_reparse_components(source)
    if not stat.S_ISREG(pre_stat.st_mode) or pre_stat.st_size > max_bytes:
        raise _AccessRejected

    file = source.open("rb")
    try:
        opened_stat = os.fstat(file.fileno())
        if not stat.S_ISREG(opened_stat.st_mode) or not os.path.samestat(pre_stat, opened_stat):
            raise _AccessRejected

        if os.name == "nt":
            final_source = _windows_final_path_from_file(file)
            if not _windows_drive_is_local(final_source) or _windows_drive_is_subst(final_source):
                raise _AccessRejected
            if not _is_within(root.final, final_source):
                raise _AccessRejected
            final_stat = _ensure_no_reparse_components(final_source)
            if not os.path.samestat(opened_stat, final_stat):
                raise _AccessRejected

        # Size the initial read to the verified file rather than reserving the full budget
        # for tiny inputs. If the file grows, still read through the same bounded limit.
        content = file.read(min(opened_stat.st_size + 1, max_bytes + 1))
        if opened_stat.st_size < len(content) <= max_bytes:
            content += file.read(max_bytes - len(content) + 1)
        if len(content) > max_bytes:
            raise _AccessRejected
        return content
    finally:
        file.close()


def read_verified_bytes(
    source: str | Path,
    *,
    allowed_root: str | Path,
    max_bytes: int,
) -> bytes:
    """Read a regular file only after approved-root and opened-handle verification."""

    failed = False
    try:
        raw_source = _coerce_path_text(source)
        raw_root = _coerce_path_text(allowed_root)
        _validate_raw_path(raw_source)
        _validate_raw_path(raw_root)
        return _read_verified_bytes_impl(raw_source, raw_root, max_bytes=max_bytes)
    except (_AccessRejected, OSError, TypeError, ValueError):
        failed = True

    if failed:
        raise DatasetInputError("input path is not permitted") from None
    raise AssertionError("unreachable")


def validate_allowed_root(allowed_root: str | Path) -> None:
    """Validate an approved root without reading a source file."""

    failed = False
    try:
        raw_root = _coerce_path_text(allowed_root)
        _validate_raw_path(raw_root)
        _validate_allowed_root_impl(raw_root)
        return
    except (_AccessRejected, OSError, TypeError, ValueError):
        failed = True

    if failed:
        raise DatasetInputError("input path is not permitted") from None
    raise AssertionError("unreachable")
