from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import patent_analysis.rendering as rendering
from patent_analysis.analysis import _canonical_json, analyze_csv
from patent_analysis.cli import main

FIXTURES = Path(__file__).parent / "fixtures" / "v1-characterization"
RANKING_SPEC = {
    "analysis_type": "ranking",
    "dimension": "出願人",
    "measure": {"mode": "count", "column": None},
    "top_n": 1,
    "include_other": True,
    "multi_value_mode": "all",
}


def _write_input(tmp_path: Path) -> Path:
    source = tmp_path / "input.csv"
    source.write_bytes("出願人,スコア\nA社,10\nB社,20\nA社,30\n".encode())
    return source


def _canonical_v1_bytes(value: object) -> bytes:
    return _canonical_json(value).encode("utf-8")


def _trusted_renderer_node() -> Path:
    if sys.platform not in {"win32", "darwin"}:
        pytest.skip("trusted-local v1 requires Windows x64 or macOS")
    candidate = os.environ.get("PATENT_ANALYSIS_TEST_NODE") or shutil.which("node")
    if candidate is None:
        pytest.skip("exact Node installation is unavailable")
    node = Path(candidate).resolve()
    try:
        version = subprocess.run(
            [str(node), "--version"], capture_output=True, check=True, text=True
        ).stdout.strip()
    except OSError:
        pytest.skip("exact Node installation is unavailable")
    if version != "v22.23.4":
        pytest.skip("exact Node 22.23.4 installation is unavailable")
    return node


def test_v1_spec_without_version_keeps_ranking_contract(tmp_path: Path) -> None:
    source = _write_input(tmp_path)

    envelope = analyze_csv(source, RANKING_SPEC, allowed_root=tmp_path)

    assert envelope["analysis_contract_version"] == "1.0.0"
    assert envelope["receipt"]["algorithm_id"] == "ranking.v1"


def test_v1_cli_success_and_error_bytes_and_exit_codes_are_frozen(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = _write_input(tmp_path)
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps(RANKING_SPEC, ensure_ascii=False), encoding="utf-8")
    invalid_spec = tmp_path / "invalid-spec.json"
    invalid_spec.write_text('{"analysis_type":"ranking"}', encoding="utf-8")
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))

    success = main(["analyze", str(source), "--spec", str(spec), "--json"])
    success_stdout = capsys.readouterr().out.encode("utf-8")
    error = main(["analyze", str(source), "--spec", str(invalid_spec), "--json"])
    error_stdout = capsys.readouterr().out.encode("utf-8")

    assert (success, success_stdout) == (
        0,
        (FIXTURES / "analyze-success.stdout.json").read_bytes(),
    )
    assert (error, error_stdout) == (
        2,
        (FIXTURES / "analyze-error.stdout.json").read_bytes(),
    )


def test_v1_result_hash_and_real_renderer_are_frozen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    source = _write_input(tmp_path)
    envelope = analyze_csv(source, RANKING_SPEC, allowed_root=tmp_path)
    analysis_bytes = json.dumps(envelope, ensure_ascii=False).encode("utf-8")
    expected_receipt = json.loads(
        (FIXTURES / "render-success-receipt.json").read_text(encoding="utf-8")
    )
    node = _trusted_renderer_node()

    receipt = rendering.render_ranking_svg(
        analysis_bytes,
        output_directory=tmp_path,
        node_executable=node,
    )

    assert _canonical_v1_bytes(envelope["result"]) == bytes.fromhex(
        "7b22616e616c797369735f74797065223a2272616e6b696e67222c2264696d656e73696f6e223a22e587bae9a198e4baba222c226d656173757265223a7b22636f6c756d6e223a6e756c6c2c226d6f6465223a22636f756e74227d2c22706f70756c6174696f6e223a7b22616e616c797a65645f726f7773223a332c22696e7075745f726f7773223a337d2c22726f7773223a5b7b22636f756e74223a322c226c6162656c223a2241e7a4be222c22726f775f6b696e64223a2264696d656e73696f6e5f76616c7565222c227368617265223a302e363636363636363636363636363636362c2276616c7565223a327d2c7b22636f756e74223a312c226c6162656c223a22e3819de381aee4bb96222c22726f775f6b696e64223a2272656d61696e646572222c227368617265223a302e333333333333333333333333333333332c2276616c7565223a317d5d2c227761726e696e6773223a5b5d7d"
    )
    assert envelope["receipt"]["result_sha256"] == (
        "f1608b951bb602379880d32e950735f94465fc2c0305e5868c5408d64f8f76d0"
    )
    assert receipt == expected_receipt
    svg = (tmp_path / str(receipt["svg"])).read_bytes()
    assert hashlib.sha256(svg).hexdigest() == expected_receipt["svg_sha256"]
    analysis = tmp_path / "analysis.json"
    analysis.write_bytes(analysis_bytes)
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))
    assert main([
        "render", "--analysis", analysis.name, "--output", str(tmp_path),
        "--node", str(node), "--json",
    ]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {**expected_receipt, "status": "reused"}
    assert (tmp_path / str(receipt["svg"])).read_bytes() == svg
