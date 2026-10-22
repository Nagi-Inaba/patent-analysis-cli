from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from patent_analysis import cli
from patent_analysis.api import run_analysis_csv
from patent_analysis.canonical_v2 import canonical_json_bytes


def _lifecycle_result(tmp_path: Path) -> bytes:
    source = tmp_path / "input.csv"
    source.write_text("year,category\n2020,A\n2024,A\n2024,B\n", encoding="utf-8")
    spec = {
        "analysis_contract_version": "2.0.0",
        "analysis_id": "lifecycle.v1",
        "resolution": {"bindings": {"year": "year", "category": "category"}},
        "normalization": {"profiles": []},
        "population": {"filters": [], "selection_sets": [], "family_mode": "records"},
        "parameters": {"date_role": "year", "category_role": "category"},
    }
    return canonical_json_bytes(
        run_analysis_csv(source.name, canonical_json_bytes(spec), allowed_root=tmp_path)
    )


def test_lifecycle_fixture_has_literal_expected_analytics(tmp_path: Path) -> None:
    result = json.loads(_lifecycle_result(tmp_path))
    assert result["data"]["window"] == {"start_year": 2020, "end_year": 2024, "years": 5}
    # A has one record at each endpoint: zero CAGR, earliest tied peak, total two.
    # B's +100 is the existing zero-start convention, not a measured growth rate.
    assert result["data"]["points"] == [
        {"label": "A", "x": 2020, "y": 0.0, "size": 2, "stage": "stable"},
        {"label": "B", "x": 2024, "y": 100.0, "size": 1, "stage": "growth"},
    ]


@pytest.mark.parametrize(
    ("mark", "with_overlay"),
    [("series-line-svg.v1", False), ("points-bubble-svg.v1", True), (None, True)],
)
def test_cli_rejects_incompatible_mark_or_overlay_for_valid_lifecycle_result(
    mark: str | None,
    with_overlay: bool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    analysis = tmp_path / "analysis.json"
    analysis.write_bytes(_lifecycle_result(tmp_path))
    output = tmp_path / "output"
    output.mkdir()
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))
    argv = ["render", "--analysis", analysis.name, "--output", str(output), "--json"]
    if mark is not None:
        argv.extend(["--mark", mark])
    if with_overlay:
        overlay = tmp_path / "overlay.json"
        overlay.write_text("{}", encoding="utf-8")
        argv.extend(["--overlay", overlay.name])

    assert cli.main(argv) == 2
    captured = capsys.readouterr()
    failure = json.loads(captured.out)
    assert failure["ok"] is False
    assert failure["error"]["code"] == "render.invalid"
    assert captured.err == ""
    assert list(output.iterdir()) == []


def _exact_renderer_node() -> str | None:
    node = shutil.which("node")
    if sys.platform not in {"win32", "darwin"} or not node:
        return None
    version = subprocess.run(
        [node, "--version"], capture_output=True, text=True, timeout=10, check=False
    )
    return node if version.returncode == 0 and version.stdout.strip() == "v22.23.4" else None


@pytest.mark.skipif(
    sys.platform not in {"win32", "darwin"},
    reason="requires Windows x64 or macOS",
)
@pytest.mark.parametrize("mark", ["points-bubble-svg.v1", None])
def test_cli_real_native_points_created_then_reused(
    mark: str | None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    node = _exact_renderer_node()
    assert node is not None, "Native renderer acceptance requires Node 22.23.4, not a skip"
    analysis = tmp_path / "analysis.json"
    analysis.write_bytes(_lifecycle_result(tmp_path))
    source_bytes = (tmp_path / "input.csv").read_bytes()
    analysis_bytes = analysis.read_bytes()
    output = tmp_path / "output"
    output.mkdir()
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))
    argv = [
        "render",
        "--analysis",
        str(analysis),
        "--output",
        str(output),
        "--node",
        node,
        "--json",
    ]
    if mark is not None:
        argv[7:7] = ["--mark", mark]

    assert cli.main(argv) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["status"] == "created"
    svg_path = output / first["svg"]
    svg_bytes = svg_path.read_bytes()
    assert b"<svg" in svg_bytes
    assert hashlib.sha256(svg_bytes).hexdigest() == first["svg_sha256"]
    assert cli.main(argv) == 0
    second = json.loads(capsys.readouterr().out)
    assert second == {**first, "status": "reused"}
    assert svg_path.read_bytes() == svg_bytes
    assert analysis.read_bytes() == analysis_bytes
    assert (tmp_path / "input.csv").read_bytes() == source_bytes
