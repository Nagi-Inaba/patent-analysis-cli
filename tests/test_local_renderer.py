from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform not in {"win32", "darwin"},
    reason="trusted-local renderer requires Windows x64 or macOS",
)


def _load_module():
    try:
        from patent_analysis import local_renderer
    except ImportError:
        return None
    return local_renderer


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


class _RecordingInput(io.BytesIO):
    def __init__(self) -> None:
        super().__init__()
        self.closed_bytes = b""

    def close(self) -> None:
        self.closed_bytes = self.getvalue()
        super().close()


class _FakeProcess:
    def __init__(
        self,
        *,
        stdout: bytes = b"response",
        stderr: bytes = b"",
        returncode: int = 0,
        timeout: bool = False,
    ) -> None:
        self.stdin = _RecordingInput()
        self.stdout = io.BytesIO(stdout)
        self.stderr = io.BytesIO(stderr)
        self.returncode = returncode
        self.timeout = timeout
        self.kill_count = 0
        self.wait_count = 0

    def wait(self, timeout: float | None = None) -> int:
        self.wait_count += 1
        if self.timeout and self.kill_count == 0:
            raise subprocess.TimeoutExpired("node", timeout)
        return self.returncode

    def kill(self) -> None:
        self.kill_count += 1


class _FailingRead(io.BytesIO):
    def read(self, _size: int = -1) -> bytes:
        raise OSError("reader failed with secret bytes")


class _FailingWrite(_RecordingInput):
    def write(self, _value: bytes) -> int:
        raise OSError("writer failed with secret frame")


def test_launcher_uses_exact_trusted_local_process_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    assert module is not None
    process = _FakeProcess(stdout=b"ok", stderr=b"warning")
    calls: list[tuple[list[str], dict[str, object]]] = []

    def fake_popen(argv: list[str], **kwargs: object) -> _FakeProcess:
        calls.append((argv, kwargs))
        return process

    monkeypatch.setattr(module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(module, "resolve_node_executable", lambda value: Path(value))
    monkeypatch.setenv("SystemRoot", r"C:\Windows")
    monkeypatch.setenv("SECRET_VALUE", "must-not-be-inherited")

    result = module.launch_trusted_node(
        r"C:\Program Files\nodejs\node.exe",
        b"bootstrap();",
        b"frame",
    )

    assert result == module.LocalProcessResult(0, b"ok", b"warning")
    assert len(calls) == 1
    argv, kwargs = calls[0]
    assert argv == [
        r"C:\Program Files\nodejs\node.exe",
        "--permission",
        "--max-old-space-size=192",
        "--disable-proto=throw",
        "--eval",
        "bootstrap();",
    ]
    assert kwargs == {
        "stdin": subprocess.PIPE,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "shell": False,
        "close_fds": True,
        "creationflags": subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        "env": {
            "SystemRoot": r"C:\Windows",
            "TZ": "UTC",
            "LANG": "ja-JP",
            "LC_ALL": "ja-JP",
        },
    }
    assert process.stdin.closed is True
    assert process.stdin.closed_bytes == b"frame"
    assert process.wait_count >= 1


@pytest.mark.parametrize(
    ("stream_name", "size", "must_kill"),
    [
        ("stdout", 12 * 1024 * 1024, False),
        ("stdout", 12 * 1024 * 1024 + 1, True),
        ("stderr", 64 * 1024, False),
        ("stderr", 64 * 1024 + 1, True),
    ],
)
def test_launcher_drains_both_pipes_with_exact_limits(
    monkeypatch: pytest.MonkeyPatch,
    stream_name: str,
    size: int,
    must_kill: bool,
) -> None:
    module = _load_module()
    assert module is not None
    process = _FakeProcess(
        stdout=b"x" * size if stream_name == "stdout" else b"",
        stderr=b"e" * size if stream_name == "stderr" else b"",
    )
    monkeypatch.setattr(module.subprocess, "Popen", lambda *_a, **_k: process)
    monkeypatch.setattr(module, "resolve_node_executable", lambda value: Path(value))

    if must_kill:
        with pytest.raises(module.LocalRendererError):
            module.launch_trusted_node(r"C:\node.exe", b"boot", b"frame")
        assert process.kill_count >= 1
    else:
        result = module.launch_trusted_node(r"C:\node.exe", b"boot", b"frame")
        assert len(getattr(result, stream_name)) == size
        assert process.kill_count == 0
    assert process.stdin.closed is True
    assert process.wait_count >= 1


def test_launcher_kills_and_waits_on_ten_second_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    assert module is not None
    process = _FakeProcess(timeout=True)
    monkeypatch.setattr(module.subprocess, "Popen", lambda *_a, **_k: process)
    monkeypatch.setattr(module, "resolve_node_executable", lambda value: Path(value))

    with pytest.raises(module.LocalRendererError):
        module.launch_trusted_node(r"C:\node.exe", b"boot", b"frame")

    assert process.kill_count >= 1
    assert process.wait_count >= 2
    assert process.stdin.closed is True


def test_launcher_maps_nonzero_exit_without_retaining_stderr(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    assert module is not None
    secret = "secret-label C:\\private\\case.json"
    process = _FakeProcess(returncode=7, stderr=secret.encode())
    monkeypatch.setattr(module.subprocess, "Popen", lambda *_a, **_k: process)
    monkeypatch.setattr(module, "resolve_node_executable", lambda value: Path(value))

    with pytest.raises(module.LocalRendererError) as captured:
        module.launch_trusted_node(r"C:\node.exe", b"boot", b"frame")

    error = captured.value
    assert secret not in str(error)
    assert secret not in repr(error)
    assert error.__cause__ is None
    assert error.__context__ is None
    assert process.stdin.closed is True


def test_node_path_must_be_exact_absolute_local_regular_non_reparse() -> None:
    module = _load_module()
    assert module is not None
    exact_node = _trusted_renderer_node()

    assert module.resolve_node_executable(exact_node) == exact_node
    for invalid in ("node.exe", r"\\server\share\node.exe", exact_node.parent):
        with pytest.raises(module.LocalRendererError):
            module.resolve_node_executable(invalid)


def test_platform_gate_rejects_windows_arm64(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    assert module is not None
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(module.platform, "machine", lambda: "ARM64")

    with pytest.raises(module.LocalRendererError):
        module.require_supported_platform()


@pytest.mark.parametrize("failing_pipe", ["stdin", "stdout", "stderr"])
def test_pipe_failures_kill_wait_close_and_leave_no_worker_thread(
    monkeypatch: pytest.MonkeyPatch,
    failing_pipe: str,
) -> None:
    module = _load_module()
    assert module is not None
    process = _FakeProcess()
    if failing_pipe == "stdin":
        process.stdin = _FailingWrite()
    elif failing_pipe == "stdout":
        process.stdout = _FailingRead()
    else:
        process.stderr = _FailingRead()
    monkeypatch.setattr(module.subprocess, "Popen", lambda *_a, **_k: process)
    monkeypatch.setattr(module, "resolve_node_executable", lambda value: Path(value))

    with pytest.raises(module.LocalRendererError) as captured:
        module.launch_trusted_node(r"C:\node.exe", b"boot", b"secret-frame")

    assert "secret" not in str(captured.value)
    assert process.kill_count >= 1
    assert process.wait_count >= 1
    assert process.stdin.closed is True
    assert not any(
        thread.name.startswith("patent-render-") and thread.is_alive()
        for thread in module.threading.enumerate()
    )


def test_path_resolved_node_is_normalized_and_validated_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    assert module is not None
    exact_node = _trusted_renderer_node()
    calls: list[str] = []
    monkeypatch.setattr(
        module.shutil,
        "which",
        lambda name: calls.append(name) or os.fspath(exact_node),
    )

    assert module.resolve_node_executable(None) == exact_node
    assert calls == ["node"]


def test_cleanup_threads_are_daemon_and_all_waits_and_joins_are_bounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    assert module is not None
    process = _FakeProcess()
    wait_timeouts: list[float | None] = []
    threads: list[object] = []

    def always_timeout(timeout: float | None = None) -> int:
        wait_timeouts.append(timeout)
        raise subprocess.TimeoutExpired("node", timeout)

    process.wait = always_timeout  # type: ignore[method-assign]

    class InspectableThread:
        def __init__(
            self,
            *,
            target: object,
            args: object,
            name: str,
            daemon: bool = False,
        ) -> None:
            del target, args, name
            self.daemon = daemon
            self.join_timeouts: list[float | None] = []
            threads.append(self)

        def start(self) -> None:
            pass

        def join(self, timeout: float | None = None) -> None:
            self.join_timeouts.append(timeout)

        def is_alive(self) -> bool:
            return True

    monkeypatch.setattr(module.threading, "Thread", InspectableThread)
    monkeypatch.setattr(module.subprocess, "Popen", lambda *_a, **_k: process)
    monkeypatch.setattr(module, "resolve_node_executable", lambda value: Path(value))

    with pytest.raises(module.LocalRendererError):
        module.launch_trusted_node(r"C:\node.exe", b"boot", b"frame")

    assert threads and all(thread.daemon is True for thread in threads)
    assert wait_timeouts and all(timeout is not None for timeout in wait_timeouts)
    assert all(
        timeout is not None
        for thread in threads
        for timeout in thread.join_timeouts
    )


def test_partial_thread_start_failure_runs_bounded_cleanup_and_sanitizes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    assert module is not None
    process = _FakeProcess()
    started = 0
    joins: list[float | None] = []

    class StartFailThread:
        def __init__(self, **_kwargs: object) -> None:
            self.daemon = bool(_kwargs.get("daemon"))

        def start(self) -> None:
            nonlocal started
            started += 1
            if started == 2:
                raise RuntimeError(r"secret C:\private\thread")

        def join(self, timeout: float | None = None) -> None:
            joins.append(timeout)

        def is_alive(self) -> bool:
            return False

    monkeypatch.setattr(module.threading, "Thread", StartFailThread)
    monkeypatch.setattr(module.subprocess, "Popen", lambda *_a, **_k: process)
    monkeypatch.setattr(module, "resolve_node_executable", lambda value: Path(value))

    with pytest.raises(module.LocalRendererError) as captured:
        module.launch_trusted_node(r"C:\node.exe", b"boot", b"secret-frame")

    assert "secret" not in str(captured.value)
    assert process.kill_count >= 1
    assert process.stdin.closed and process.stdout.closed and process.stderr.closed
    assert joins and all(timeout is not None for timeout in joins)


def test_ignoring_kill_and_retained_pipe_still_return_within_cleanup_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    assert module is not None

    class RetainedPipe(io.BytesIO):
        def read(self, _size: int = -1) -> bytes:
            time.sleep(1.5)
            return b""

    process = _FakeProcess()
    process.stdout = RetainedPipe()
    wait_timeouts: list[float | None] = []

    def always_timeout(timeout: float | None = None) -> int:
        wait_timeouts.append(timeout)
        raise subprocess.TimeoutExpired("node", timeout)

    def kill_fails() -> None:
        raise OSError(r"secret C:\private\node.exe")

    process.wait = always_timeout  # type: ignore[method-assign]
    process.kill = kill_fails  # type: ignore[method-assign]
    monkeypatch.setattr(module.subprocess, "Popen", lambda *_a, **_k: process)
    monkeypatch.setattr(module, "resolve_node_executable", lambda value: Path(value))

    started_at = time.monotonic()
    with pytest.raises(module.LocalRendererError) as captured:
        module.launch_trusted_node(r"C:\node.exe", b"boot", b"secret-frame")
    elapsed = time.monotonic() - started_at

    assert elapsed < 1.0
    assert all(timeout is not None for timeout in wait_timeouts)
    assert process.stdin.closed and process.stdout.closed and process.stderr.closed
    assert "secret" not in str(captured.value)
