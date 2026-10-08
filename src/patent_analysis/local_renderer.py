from __future__ import annotations

import os
import platform
import shutil
import stat
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from patent_analysis.access import (
    _coerce_path_text,
    _ensure_no_reparse_components,
    _normalize_absolute,
    _validate_allowed_root_impl,
    _validate_raw_path,
    _windows_drive_is_local,
    _windows_drive_is_subst,
    _windows_final_path_from_file,
)

_STDOUT_LIMIT = 12 * 1024 * 1024
_STDERR_LIMIT = 64 * 1024
_WALL_TIMEOUT_SECONDS = 10.0
_THREAD_GRACE_SECONDS = 0.25
_CLEANUP_WAIT_SECONDS = 0.25
_CLEANUP_JOIN_SECONDS = 0.25


class LocalRendererError(RuntimeError):
    def __init__(self) -> None:
        super().__init__("Trusted local renderer is unavailable")
        self.__suppress_context__ = True


@dataclass(frozen=True)
class LocalProcessResult:
    returncode: int
    stdout: bytes
    stderr: bytes


def _raise_local_error() -> None:
    raise LocalRendererError() from None


def require_windows_x64() -> None:
    if os.name != "nt" or platform.machine().casefold() not in {"amd64", "x86_64"}:
        _raise_local_error()


def validate_local_directory(value: str | os.PathLike[str]) -> Path:
    try:
        raw = _coerce_path_text(value)
        _validate_raw_path(raw)
        path = Path(raw)
        if not path.is_absolute() or ".." in path.parts:
            raise ValueError
        approved = _validate_allowed_root_impl(raw)
        return approved.lexical
    except Exception:
        _raise_local_error()


def resolve_node_executable(value: str | os.PathLike[str] | None) -> Path:
    try:
        candidate_value = shutil.which("node") if value is None else value
        raw = _coerce_path_text(candidate_value)
        _validate_raw_path(raw)
        candidate = Path(raw)
        if not candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError
        normalized = _normalize_absolute(candidate)
        _validate_allowed_root_impl(os.fspath(normalized.parent))
        before = _ensure_no_reparse_components(normalized)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError
        with normalized.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode) or not os.path.samestat(before, opened):
                raise ValueError
            if os.name == "nt":
                final = _windows_final_path_from_file(stream)
                if (
                    not _windows_drive_is_local(final)
                    or _windows_drive_is_subst(final)
                    or os.path.normcase(os.fspath(final))
                    != os.path.normcase(os.fspath(normalized))
                ):
                    raise ValueError
        return normalized
    except Exception:
        _raise_local_error()


def _minimal_environment() -> dict[str, str]:
    environment = {"TZ": "UTC", "LANG": "ja-JP", "LC_ALL": "ja-JP"}
    system_root = os.environ.get("SystemRoot")
    if system_root:
        environment = {"SystemRoot": system_root, **environment}
    return environment


def _safe_kill(process: object) -> None:
    try:
        process.kill()  # type: ignore[attr-defined]
    except Exception:
        pass


def _safe_close(stream: object) -> None:
    try:
        stream.close()  # type: ignore[attr-defined]
    except Exception:
        pass


def _bounded_wait(process: object, timeout: float) -> int | None:
    try:
        result = process.wait(timeout=timeout)  # type: ignore[attr-defined]
    except Exception:
        return None
    return result if isinstance(result, int) and not isinstance(result, bool) else None


def _bounded_join(threads: list[threading.Thread], timeout: float) -> None:
    deadline = time.monotonic() + timeout
    for thread in threads:
        remaining = max(0.0, deadline - time.monotonic())
        try:
            thread.join(timeout=remaining)
        except Exception:
            pass


def _any_alive(threads: list[threading.Thread]) -> bool:
    for thread in threads:
        try:
            if thread.is_alive():
                return True
        except Exception:
            return True
    return False


def _bounded_cleanup(
    process: object,
    streams: tuple[object, object, object],
    started_threads: list[threading.Thread],
) -> None:
    _safe_kill(process)
    for stream in streams:
        _safe_close(stream)
    _bounded_wait(process, _CLEANUP_WAIT_SECONDS)
    _bounded_join(started_threads, _CLEANUP_JOIN_SECONDS)
    for stream in streams:
        _safe_close(stream)


def _read_pipe(
    stream: BinaryIO,
    limit: int,
    process: object,
    destination: dict[str, object],
) -> None:
    chunks: list[bytes] = []
    total = 0
    try:
        while True:
            chunk = stream.read(min(64 * 1024, limit + 1 - min(total, limit + 1)))
            if not chunk:
                break
            if not isinstance(chunk, bytes):
                raise TypeError
            chunks.append(chunk)
            total += len(chunk)
            if total > limit:
                destination["overflow"] = True
                _safe_kill(process)
                break
        destination["bytes"] = b"".join(chunks)
    except Exception:
        destination["failed"] = True
        _safe_kill(process)


def _write_pipe(
    stream: BinaryIO,
    frame: bytes,
    process: object,
    destination: dict[str, object],
) -> None:
    try:
        stream.write(frame)
        stream.flush()
    except Exception:
        destination["failed"] = True
        _safe_kill(process)
    finally:
        try:
            stream.close()
        except Exception:
            destination["failed"] = True
            _safe_kill(process)


def launch_trusted_node(
    node_executable: str | os.PathLike[str],
    bootstrap_bytes: bytes,
    frame: bytes,
) -> LocalProcessResult:
    require_windows_x64()
    if type(bootstrap_bytes) is not bytes or type(frame) is not bytes:
        _raise_local_error()
    node = resolve_node_executable(node_executable)
    try:
        bootstrap = bootstrap_bytes.decode("utf-8")
        process = subprocess.Popen(
            [
                os.fspath(node),
                "--permission",
                "--max-old-space-size=192",
                "--disable-proto=throw",
                "--eval",
                bootstrap,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            close_fds=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            env=_minimal_environment(),
        )
    except Exception:
        _raise_local_error()

    stdin = process.stdin
    stdout = process.stdout
    stderr = process.stderr
    if stdin is None or stdout is None or stderr is None:
        _bounded_cleanup(process, (stdin, stdout, stderr), [])
        _raise_local_error()

    stdout_result: dict[str, object] = {}
    stderr_result: dict[str, object] = {}
    writer_result: dict[str, object] = {}
    threads: list[threading.Thread] = []
    thread_setup_failed = False
    try:
        threads = [
            threading.Thread(
                target=_read_pipe,
                args=(stdout, _STDOUT_LIMIT, process, stdout_result),
                name="patent-render-stdout",
                daemon=True,
            ),
            threading.Thread(
                target=_read_pipe,
                args=(stderr, _STDERR_LIMIT, process, stderr_result),
                name="patent-render-stderr",
                daemon=True,
            ),
            threading.Thread(
                target=_write_pipe,
                args=(stdin, frame, process, writer_result),
                name="patent-render-stdin",
                daemon=True,
            ),
        ]
    except Exception:
        thread_setup_failed = True

    started_threads: list[threading.Thread] = []
    if not thread_setup_failed:
        for thread in threads:
            try:
                thread.start()
            except Exception:
                thread_setup_failed = True
                break
            started_threads.append(thread)

    if thread_setup_failed:
        _bounded_cleanup(process, (stdin, stdout, stderr), started_threads)
        _raise_local_error()

    wait_failed = False
    returncode: int | None = None
    try:
        returncode = process.wait(timeout=_WALL_TIMEOUT_SECONDS)
    except Exception:
        wait_failed = True

    if wait_failed or returncode != 0:
        _bounded_cleanup(process, (stdin, stdout, stderr), started_threads)
    else:
        _bounded_join(started_threads, _THREAD_GRACE_SECONDS)
        if _any_alive(started_threads):
            wait_failed = True
            _bounded_cleanup(process, (stdin, stdout, stderr), started_threads)
        else:
            for stream in (stdin, stdout, stderr):
                _safe_close(stream)

    failed = (
        wait_failed
        or returncode != 0
        or writer_result.get("failed") is True
        or stdout_result.get("failed") is True
        or stderr_result.get("failed") is True
        or stdout_result.get("overflow") is True
        or stderr_result.get("overflow") is True
    )
    stdout_bytes = stdout_result.get("bytes")
    stderr_bytes = stderr_result.get("bytes")
    if failed or type(stdout_bytes) is not bytes or type(stderr_bytes) is not bytes:
        _raise_local_error()
    return LocalProcessResult(returncode, stdout_bytes, stderr_bytes)
