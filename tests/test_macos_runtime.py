"""Platform acceptance and native no-clobber publication regressions."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from patent_analysis import local_renderer, rendering
from patent_analysis.render_errors import RenderError


@pytest.mark.parametrize(
    ("host", "machine", "supported"),
    [
        ("win32", "AMD64", True),
        ("win32", "ARM64", False),
        ("darwin", "arm64", True),
        ("darwin", "x86_64", True),
        ("darwin", "ppc", False),
        ("linux", "x86_64", False),
        ("linux", "aarch64", False),
    ],
)
def test_renderer_platform_contract(monkeypatch, host, machine, supported):
    monkeypatch.setattr(sys, "platform", host)
    monkeypatch.setattr(local_renderer.platform, "machine", lambda: machine)
    if supported:
        local_renderer.require_supported_platform()
    else:
        with pytest.raises(local_renderer.LocalRendererError):
            local_renderer.require_supported_platform()


@pytest.mark.parametrize("winner", [b"same", b"other"])
def test_concurrent_publication_preserves_the_winner(tmp_path, monkeypatch, winner):
    final = tmp_path / "chart.svg"
    original_probe = rendering._probe_final

    def race(path: Path, expected: bytes) -> str:
        state = original_probe(path, expected)
        if state == "missing":
            path.write_bytes(winner)
        return state

    monkeypatch.setattr(rendering, "_probe_final", race)
    if winner == b"same":
        assert rendering._publish_svg(tmp_path, final.name, b"same") == "reused"
    else:
        with pytest.raises(RenderError) as error:
            rendering._publish_svg(tmp_path, final.name, b"same")
        assert error.value.code == "output.conflict"
    assert final.read_bytes() == winner
    assert list(tmp_path.iterdir()) == [final]
