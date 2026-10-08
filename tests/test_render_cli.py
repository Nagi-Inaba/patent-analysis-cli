from __future__ import annotations

import json
import os
import subprocess
import sys
from io import BytesIO, TextIOWrapper
from pathlib import Path

import pytest

from patent_analysis import cli


@pytest.mark.parametrize("input_kind", ["stdin", "file"])
def test_render_entrypoint_rejects_deep_json_with_fixed_error(
    input_kind: str, tmp_path: Path,
) -> None:
    document = b'{"PRIVATE":' + b"[" * 100_000 + b"0" + b"]" * 100_000 + b"}"
    analysis = tmp_path / "analysis.json"
    analysis.write_bytes(document)
    output = tmp_path / "must-not-be-created"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    env["PATENT_ANALYSIS_ALLOWED_ROOT"] = str(tmp_path)
    source = "-" if input_kind == "stdin" else analysis.name
    result = subprocess.run(
        [sys.executable, "-m", "patent_analysis", "render", "--analysis", source,
         "--output", str(output), "--json"],
        input=document if input_kind == "stdin" else b"",
        capture_output=True, cwd=tmp_path, env=env, timeout=10, check=False,
    )
    assert result.returncode == cli.EXIT_INPUT_ERROR
    assert result.stderr == b""
    assert json.loads(result.stdout) == {
        "render_contract_version": "1.0.0",
        "ok": False,
        "error": {
            "code": "input.invalid",
            "message": "Render input could not be read or parsed",
            "retryable": False,
            "details": {},
        },
    }
    assert analysis.read_bytes() == document and not output.exists()


@pytest.mark.parametrize(
    "argv",
    [
        ["render", "--output", r"C:\out", "--json"],
        ["render", "--analysis", "a.json", "--json"],
        ["render", "--analysis", "a.json", "--output", r"C:\out"],
        ["render", "--help"],
        ["render", "--help", "--json"],
        [
            "render",
            "--analysis",
            "-",
            "--overlay",
            "-",
            "--output",
            r"C:\out",
            "--json",
        ],
    ],
)
def test_render_usage_errors_are_exact_json_and_exit_four(
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
) -> None:
    assert cli.main(argv) == 4
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "render_contract_version": "1.0.0",
        "ok": False,
        "error": {
            "code": "usage.invalid",
            "message": "Invalid patent-analysis render arguments",
            "retryable": False,
            "details": {},
        },
    }


def test_render_auto_detection_rejects_oversized_integer_without_side_effects(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    document = b'{"PRIVATE":' + b"9" * 5000 + b"}"
    output = tmp_path / "must-not-be-created"
    monkeypatch.delenv("PATENT_ANALYSIS_ALLOWED_ROOT", raising=False)
    monkeypatch.setattr(
        sys,
        "stdin",
        TextIOWrapper(BytesIO(document), encoding="utf-8"),
    )

    assert cli.main(
        ["render", "--analysis", "-", "--output", str(output), "--json"]
    ) == cli.EXIT_INPUT_ERROR

    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "render_contract_version": "1.0.0",
        "ok": False,
        "error": {
            "code": "input.invalid",
            "message": "Render input could not be read or parsed",
            "retryable": False,
            "details": {},
        },
    }
    assert not output.exists()


@pytest.mark.parametrize(
    ("code", "exit_code"),
    [
        ("render.invalid", 2),
        ("input.invalid", 3),
        ("usage.invalid", 4),
        ("renderer.unavailable", 5),
        ("output.conflict", 6),
    ],
)
def test_render_cli_maps_all_five_errors_to_fixed_exits(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    code: str,
    exit_code: int,
) -> None:
    try:
        from patent_analysis.render_errors import _make_render_error
    except ModuleNotFoundError:
        pytest.fail("render error interface is missing")
    analysis = tmp_path / "analysis.json"
    analysis.write_bytes(b"{}")
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))
    monkeypatch.setattr(cli, "render_analysis_svg", lambda *_a, **_k: (_ for _ in ()).throw(
        _make_render_error(code)
    ))

    assert cli.main(
        [
            "render",
            "--analysis",
            str(analysis),
            "--output",
            str(tmp_path),
            "--json",
        ]
    ) == exit_code
    payload = json.loads(capsys.readouterr().out)
    assert payload["render_contract_version"] == "1.0.0"
    assert payload["error"]["code"] == code


def test_render_cli_reads_analysis_from_bounded_stdin_and_passes_node(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    received: list[tuple[bytes, dict[str, object]]] = []
    monkeypatch.setattr(
        sys,
        "stdin",
        TextIOWrapper(BytesIO(b'{"analysis":true}'), encoding="utf-8"),
    )
    monkeypatch.setattr(
        cli,
        "render_analysis_svg",
        lambda document, **kwargs: received.append((document, kwargs))
        or {
            "render_contract_version": "1.0.0",
            "ok": True,
            "status": "created",
            "artifact_id": "a" * 64,
            "svg": f"ranking-svg-{'a' * 64}.svg",
            "svg_sha256": "b" * 64,
            "renderer_build_digest": "c" * 64,
        },
    )

    assert cli.main(
        [
            "render",
            "--analysis",
            "-",
            "--output",
            str(tmp_path),
            "--node",
            r"C:\node.exe",
            "--json",
        ]
    ) == 0
    assert received == [
        (
            b'{"analysis":true}',
            {
                "mark": None,
                "overlay": None,
                "output_directory": str(tmp_path),
                "node_executable": r"C:\node.exe",
            },
        )
    ]
    assert json.loads(capsys.readouterr().out)["status"] == "created"


def test_render_cli_rejects_file_input_without_allowed_root(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    analysis = tmp_path / "analysis.json"
    analysis.write_bytes(b"{}")
    monkeypatch.delenv("PATENT_ANALYSIS_ALLOWED_ROOT", raising=False)

    assert cli.main(
        [
            "render",
            "--analysis",
            str(analysis),
            "--output",
            str(tmp_path),
            "--json",
        ]
    ) == 3
    assert json.loads(capsys.readouterr().out)["error"]["code"] == "input.invalid"


@pytest.mark.parametrize(
    "mark",
    [
        "series-line-svg.v1",
        "series-stacked-bar-svg.v1",
        "composition-bar-svg.v1",
        "composition-pie-svg.v1",
    ],
)
def test_render_cli_dispatches_registered_categorical_marks(
    mark: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    analysis = tmp_path / "analysis.json"
    analysis.write_text(
        json.dumps({"analysis_id": "timeline.v1", "result_variant": "series"}),
        encoding="utf-8",
    )
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))
    received: dict[str, object] = {}

    def fake_render(document: bytes, **kwargs: object) -> dict[str, object]:
        received.update(document=document, **kwargs)
        return {"render_contract_version": "1.0.0", "ok": True, "mark": mark}

    monkeypatch.setattr(cli, "render_analysis_svg", fake_render)

    assert cli.main(
        [
            "render",
            "--analysis",
            analysis.name,
            "--output",
            str(tmp_path),
            "--mark",
            mark,
            "--json",
        ]
    ) == 0
    assert received["document"] == analysis.read_bytes()
    assert received["mark"] == mark
    assert json.loads(capsys.readouterr().out)["mark"] == mark
