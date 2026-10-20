import hashlib
import json
import os
import subprocess
import sys
from io import StringIO
from pathlib import Path

import pytest
from advanced_inventory import ANALYSIS_IDS

import patent_analysis.access as access_module
import patent_analysis.analysis as analysis_module
from patent_analysis.cli import MAX_INPUT_BYTES, main


@pytest.fixture(autouse=True)
def _approved_analysis_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))


def _valid_analysis_spec() -> dict[str, object]:
    return {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "count", "column": None},
        "top_n": 10,
        "include_other": True,
        "multi_value_mode": "all",
    }


def _write_analysis_csv(tmp_path: Path) -> tuple[Path, bytes]:
    csv_bytes = "出願人,スコア\nA社,10\nB社,20\nA社,30\n".encode()
    csv_path = tmp_path / "analysis.csv"
    csv_path.write_bytes(csv_bytes)
    return csv_path, csv_bytes


def _assert_safe_json_failure(
    captured,
    *,
    exit_code: int,
    expected_exit_code: int,
    expected_error_code: str,
    forbidden: tuple[str, ...] = (),
) -> dict[str, object]:
    payload = json.loads(captured.out)
    assert exit_code == expected_exit_code
    assert captured.err == ""
    assert payload["analysis_contract_version"] == "1.0.0"
    assert payload["ok"] is False
    assert payload["error"]["code"] == expected_error_code
    assert payload["error"]["details"] == {}
    assert "Traceback" not in captured.out
    for value in forbidden:
        assert value not in captured.out
    return payload


def test_contract_command_outputs_machine_readable_contract(capsys):
    exit_code = main(["contract", "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert captured.err == ""
    assert payload["contract_version"] == "1.0.0"
    assert "validate-plan" in payload["commands"]


def test_capabilities_command_needs_no_allowed_root_and_is_exact(
    monkeypatch,
    capsys,
):
    monkeypatch.delenv("PATENT_ANALYSIS_ALLOWED_ROOT", raising=False)

    exit_code = main(["capabilities", "--json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["capabilities_contract_version"] == "1.0.0"
    assert tuple(item["analysis_id"] for item in payload["analyses"]) == ANALYSIS_IDS


def test_capabilities_human_mode_prints_analysis_ids_only(monkeypatch, capsys):
    monkeypatch.delenv("PATENT_ANALYSIS_ALLOWED_ROOT", raising=False)

    assert main(["capabilities"]) == 0

    captured = capsys.readouterr()
    assert captured.out == "".join(name + "\n" for name in ANALYSIS_IDS)
    assert captured.err == ""


@pytest.mark.parametrize("command", ["inspect", "analyze"])
@pytest.mark.parametrize("root_value", [None, "", "relative-root"])
def test_analysis_commands_require_valid_allowed_root_environment(
    tmp_path,
    monkeypatch,
    capsys,
    command,
    root_value,
):
    csv_path, _ = _write_analysis_csv(tmp_path)
    if root_value is None:
        monkeypatch.delenv("PATENT_ANALYSIS_ALLOWED_ROOT", raising=False)
    else:
        monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", root_value)
    argv = [command, str(csv_path), "--json"]
    if command == "analyze":
        monkeypatch.setattr(sys, "stdin", StringIO(json.dumps(_valid_analysis_spec())))
        argv[2:2] = ["--spec", "-"]

    exit_code = main(argv)

    captured = capsys.readouterr()
    payload = _assert_safe_json_failure(
        captured,
        exit_code=exit_code,
        expected_exit_code=3,
        expected_error_code="input.invalid",
    )
    assert payload["error"]["message"] in {
        "Dataset input could not be read or parsed",
        "AnalysisSpec input could not be read or parsed",
    }


def test_analyze_missing_root_precedes_invalid_stdin_spec(
    tmp_path,
    monkeypatch,
    capsys,
):
    csv_path, _ = _write_analysis_csv(tmp_path)
    monkeypatch.delenv("PATENT_ANALYSIS_ALLOWED_ROOT", raising=False)
    monkeypatch.setattr(sys, "stdin", StringIO('{"top_n":0}'))

    exit_code = main(["analyze", str(csv_path), "--spec", "-", "--json"])

    captured = capsys.readouterr()
    _assert_safe_json_failure(
        captured,
        exit_code=exit_code,
        expected_exit_code=3,
        expected_error_code="input.invalid",
    )


def test_analysis_commands_resolve_relative_csv_and_spec_against_allowed_root(
    tmp_path,
    monkeypatch,
    capsys,
):
    _write_analysis_csv(tmp_path)
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(_valid_analysis_spec()), encoding="utf-8")
    monkeypatch.chdir(tmp_path.parent)

    exit_code = main(["analyze", "analysis.csv", "--spec", "spec.json", "--json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert json.loads(captured.out)["ok"] is True


def test_json_dataset_and_spec_accept_a_utf8_bom(tmp_path, capsys):
    dataset = tmp_path / "bom-dataset.json"
    dataset.write_bytes(
        b"\xef\xbb\xbf"
        + json.dumps([{"出願人": "A社"}, {"出願人": "B社"}], ensure_ascii=False).encode("utf-8")
    )
    spec_path = tmp_path / "bom-spec.json"
    spec_path.write_bytes(
        b"\xef\xbb\xbf" + json.dumps(_valid_analysis_spec(), ensure_ascii=False).encode("utf-8")
    )

    exit_code = main(["analyze", dataset.name, "--spec", spec_path.name, "--json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert json.loads(captured.out)["ok"] is True


def test_validate_plan_accepts_a_utf8_bom(tmp_path, capsys):
    plan_path = tmp_path / "bom-plan.json"
    plan_path.write_bytes(
        b"\xef\xbb\xbf"
        + json.dumps(
            {
                "intent": "applicant ranking",
                "operations": [
                    {
                        "type": "create_analysis",
                        "params": {"analysis_type": "ranking", "x": "applicant"},
                    }
                ],
            }
        ).encode("utf-8")
    )

    exit_code = main(["validate-plan", plan_path.name, "--json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert json.loads(captured.out) == {"contract_version": "1.0.0", "ok": True}


def test_top_level_help_lists_capabilities(capsys):
    assert main(["--help"]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    listing = " ".join(captured.out.split("positional arguments:", 1)[1].split())
    assert "capabilities List implemented analyses, render marks, and schema names" in listing


def test_capabilities_help_prints_its_usage(capsys):
    assert main(["capabilities", "--help"]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out.startswith("usage: patent-analysis capabilities")


def test_analysis_spec_file_outside_allowed_root_is_rejected(tmp_path, capsys):
    csv_path, _ = _write_analysis_csv(tmp_path)
    outside = tmp_path.parent / "TASK-5A-OUTSIDE-SPEC.json"
    outside.write_text(json.dumps(_valid_analysis_spec()), encoding="utf-8")
    try:
        exit_code = main(["analyze", str(csv_path), "--spec", str(outside), "--json"])
    finally:
        outside.unlink(missing_ok=True)

    captured = capsys.readouterr()
    _assert_safe_json_failure(
        captured,
        exit_code=exit_code,
        expected_exit_code=3,
        expected_error_code="input.invalid",
        forbidden=("TASK-5A-OUTSIDE-SPEC", str(outside)),
    )


def test_analysis_commands_do_not_accept_allowed_root_cli_option(tmp_path, capsys):
    csv_path, _ = _write_analysis_csv(tmp_path)

    exit_code = main(["inspect", str(csv_path), "--allowed-root", str(tmp_path), "--json"])

    captured = capsys.readouterr()
    assert exit_code == 4
    assert captured.err == ""
    assert json.loads(captured.out)["error"]["code"] == "usage.invalid"


def test_analysis_spec_cannot_set_allowed_root(tmp_path, monkeypatch, capsys):
    csv_path, _ = _write_analysis_csv(tmp_path)
    spec = _valid_analysis_spec()
    spec["allowed_root"] = str(tmp_path)
    monkeypatch.setattr(sys, "stdin", StringIO(json.dumps(spec)))

    exit_code = main(["analyze", str(csv_path), "--spec", "-", "--json"])

    captured = capsys.readouterr()
    _assert_safe_json_failure(
        captured,
        exit_code=exit_code,
        expected_exit_code=2,
        expected_error_code="analysis.invalid",
        forbidden=(str(tmp_path),),
    )


def test_contract_does_not_require_allowed_root_environment(monkeypatch, capsys):
    monkeypatch.delenv("PATENT_ANALYSIS_ALLOWED_ROOT", raising=False)
    assert main(["contract", "--json"]) == 0
    contract_output = capsys.readouterr()
    assert json.loads(contract_output.out)["contract_version"] == "1.0.0"


def test_validate_plan_stdin_does_not_require_allowed_root_environment(
    monkeypatch,
    capsys,
):
    monkeypatch.delenv("PATENT_ANALYSIS_ALLOWED_ROOT", raising=False)
    monkeypatch.setattr(
        sys,
        "stdin",
        StringIO(
            json.dumps(
                {
                    "intent": "applicant ranking",
                    "operations": [
                        {
                            "type": "create_analysis",
                            "params": {
                                "analysis_type": "ranking",
                                "x": "applicant",
                            },
                        }
                    ],
                }
            )
        ),
    )

    assert main(["validate-plan", "-", "--json"]) == 0
    validate_output = capsys.readouterr()
    assert json.loads(validate_output.out)["ok"] is True


def test_validate_plan_file_requires_allowed_root_without_path_leakage(
    tmp_path,
    monkeypatch,
    capsys,
):
    plan_path = tmp_path / "TASK-5E-SECRET-PLAN.json"
    plan_path.write_text(
        json.dumps({"intent": "empty plan", "operations": []}),
        encoding="utf-8",
    )
    monkeypatch.delenv("PATENT_ANALYSIS_ALLOWED_ROOT", raising=False)

    exit_code = main(["validate-plan", str(plan_path), "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 3
    assert captured.err == ""
    assert payload["error"] == {
        "code": "input.invalid",
        "message": "OperationPlan input could not be read or parsed",
        "retryable": False,
        "details": {},
    }
    assert str(plan_path) not in captured.out
    assert plan_path.name not in captured.out


@pytest.mark.parametrize(
    "source",
    [r"\\server\share\TASK-5E-SECRET.json", r"\\?\C:\TASK-5E-SECRET.json"],
)
def test_validate_plan_rejects_unc_and_device_before_filesystem_access(
    monkeypatch,
    capsys,
    source,
):
    def unexpected_stat(*_args, **_kwargs):
        raise AssertionError("untrusted path reached Path.stat")

    def unexpected_lstat(*_args, **_kwargs):
        raise AssertionError("untrusted path reached lstat")

    monkeypatch.setattr(Path, "stat", unexpected_stat)
    monkeypatch.setattr(access_module, "_lstat", unexpected_lstat)

    exit_code = main(["validate-plan", source, "--json"])

    captured = capsys.readouterr()
    assert exit_code == 3
    assert captured.err == ""
    assert json.loads(captured.out)["error"] == {
        "code": "input.invalid",
        "message": "OperationPlan input could not be read or parsed",
        "retryable": False,
        "details": {},
    }
    assert "TASK-5E-SECRET" not in captured.out


def test_inspect_command_outputs_exact_public_manifest_wrapper(tmp_path, capsys):
    csv_path, csv_bytes = _write_analysis_csv(tmp_path)

    exit_code = main(["inspect", str(csv_path), "--json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "analysis_contract_version": "1.0.0",
        "ok": True,
        "dataset": {
            "columns": ["出願人", "スコア"],
            "row_count": 3,
            "column_count": 2,
            "byte_size": len(csv_bytes),
            "encoding": "utf-8",
            "content_sha256": hashlib.sha256(csv_bytes).hexdigest(),
        },
    }


def test_legacy_inspect_stdout_bytes_remain_exact(tmp_path, capsys):
    csv_path = tmp_path / "legacy.csv"
    csv_path.write_bytes(b"a,b\n1,2\n")

    exit_code = main(["inspect", str(csv_path), "--json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert captured.out.encode() == (
        b'{"analysis_contract_version": "1.0.0", "dataset": {"byte_size": 8, '
        b'"column_count": 2, "columns": ["a", "b"], "content_sha256": '
        b'"492d5ea496056f1a6a6592241032fab764c321596317930b4fa0e1e8bc3b7470", '
        b'"encoding": "utf-8", "row_count": 1}, "ok": true}\n'
    )


def test_profiled_inspect_returns_exact_candidates_without_data_or_path_leakage(
    tmp_path,
    capsys,
):
    csv_path = tmp_path / "PRIVATE-NAME.csv"
    csv_bytes = b"Applicants\nPRIVATE-CELL\n"
    csv_path.write_bytes(csv_bytes)

    exit_code = main(["inspect", str(csv_path), "--profile", "column-alias.v2", "--json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "analysis_contract_version": "2.0.0",
        "ok": True,
        "dataset": {
            "columns": ["Applicants"],
            "row_count": 1,
            "column_count": 1,
            "byte_size": len(csv_bytes),
            "encoding": "utf-8",
            "preamble": None,
        },
        "resolution": {
            "profile": "column-alias.v2",
            "candidates": [
                {
                    "header_ordinal": 0,
                    "raw_header": "Applicants",
                    "status": "active",
                    "role": "applicant",
                    "normalized_name": "applicants",
                    "display_label": "出願人",
                    "numeric_suffix": None,
                    "identifier_like": False,
                }
            ],
            "warning_counts": {"staged_aliases": 0, "unmatched_headers": 0},
        },
    }
    assert "PRIVATE-CELL" not in captured.out
    assert csv_path.name not in captured.out
    assert str(csv_path) not in captured.out
    assert "receipt" not in captured.out
    assert "column_catalog_sha256" not in captured.out


def test_inspect_rejects_unknown_resolution_profile_as_usage_error(capsys):
    exit_code = main(["inspect", "dataset.csv", "--profile", "unknown.v1", "--json"])

    captured = capsys.readouterr()
    assert exit_code == 4
    assert captured.err == ""
    assert json.loads(captured.out)["error"]["code"] == "usage.invalid"


def test_analyze_command_outputs_public_envelope_from_spec_file(tmp_path, capsys):
    csv_path, _ = _write_analysis_csv(tmp_path)
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(_valid_analysis_spec()), encoding="utf-8")

    exit_code = main(["analyze", str(csv_path), "--spec", str(spec_path), "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert captured.err == ""
    assert set(payload) == {"analysis_contract_version", "ok", "result", "receipt"}
    assert payload["analysis_contract_version"] == "1.0.0"
    assert payload["ok"] is True
    assert payload["result"] == {
        "analysis_type": "ranking",
        "dimension": "出願人",
        "measure": {"mode": "count", "column": None},
        "population": {"input_rows": 3, "analyzed_rows": 3},
        "rows": [
            {
                "row_kind": "dimension_value",
                "label": "A社",
                "value": 2,
                "count": 2,
                "share": 2 / 3,
            },
            {
                "row_kind": "dimension_value",
                "label": "B社",
                "value": 1,
                "count": 1,
                "share": 1 / 3,
            },
        ],
        "warnings": [],
    }
    assert set(payload["receipt"]) == {
        "algorithm_id",
        "package_version",
        "input_sha256",
        "spec_sha256",
        "result_sha256",
    }
    assert payload["receipt"]["algorithm_id"] == "ranking.v1"


def test_analyze_command_accepts_bounded_spec_from_stdin(tmp_path, monkeypatch, capsys):
    csv_path, _ = _write_analysis_csv(tmp_path)
    monkeypatch.setattr(sys, "stdin", StringIO(json.dumps(_valid_analysis_spec())))

    exit_code = main(["analyze", str(csv_path), "--spec", "-", "--json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["ok"] is True
    assert payload["result"]["population"] == {"input_rows": 3, "analyzed_rows": 3}


def test_analyze_command_rejects_malformed_spec_as_safe_input_error(tmp_path, capsys):
    csv_path, _ = _write_analysis_csv(tmp_path)
    spec_path = tmp_path / "secret-spec-name.json"
    spec_path.write_text('{"dimension":"RAW-SPEC-VALUE"', encoding="utf-8")

    exit_code = main(["analyze", str(csv_path), "--spec", str(spec_path), "--json"])

    captured = capsys.readouterr()
    _assert_safe_json_failure(
        captured,
        exit_code=exit_code,
        expected_exit_code=3,
        expected_error_code="input.invalid",
        forbidden=(str(spec_path), spec_path.name, "RAW-SPEC-VALUE"),
    )


def test_analyze_command_rejects_oversized_stdin_as_safe_input_error(tmp_path, monkeypatch, capsys):
    csv_path, _ = _write_analysis_csv(tmp_path)
    monkeypatch.setattr(sys, "stdin", StringIO("SENSITIVE" + " " * MAX_INPUT_BYTES))

    exit_code = main(["analyze", str(csv_path), "--spec", "-", "--json"])

    captured = capsys.readouterr()
    _assert_safe_json_failure(
        captured,
        exit_code=exit_code,
        expected_exit_code=3,
        expected_error_code="input.invalid",
        forbidden=("SENSITIVE",),
    )


def test_analyze_command_rejects_invalid_spec_as_safe_analysis_error(tmp_path, capsys):
    csv_path, _ = _write_analysis_csv(tmp_path)
    spec_path = tmp_path / "invalid-spec.json"
    invalid_spec = _valid_analysis_spec()
    invalid_spec["top_n"] = 0
    invalid_spec["dimension"] = "SECRET-DIMENSION"
    spec_path.write_text(json.dumps(invalid_spec), encoding="utf-8")

    exit_code = main(["analyze", str(csv_path), "--spec", str(spec_path), "--json"])

    captured = capsys.readouterr()
    _assert_safe_json_failure(
        captured,
        exit_code=exit_code,
        expected_exit_code=2,
        expected_error_code="analysis.invalid",
        forbidden=(str(spec_path), spec_path.name, "SECRET-DIMENSION"),
    )


def test_inspect_command_rejects_missing_csv_as_safe_input_error(tmp_path, capsys):
    csv_path = tmp_path / "secret-dataset-name.csv"

    exit_code = main(["inspect", str(csv_path), "--json"])

    captured = capsys.readouterr()
    _assert_safe_json_failure(
        captured,
        exit_code=exit_code,
        expected_exit_code=3,
        expected_error_code="input.invalid",
        forbidden=(str(csv_path), csv_path.name),
    )


def test_analyze_command_rejects_missing_csv_as_safe_input_error(tmp_path, capsys):
    csv_path = tmp_path / "secret-dataset-name.csv"
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(_valid_analysis_spec()), encoding="utf-8")

    exit_code = main(["analyze", str(csv_path), "--spec", str(spec_path), "--json"])

    captured = capsys.readouterr()
    _assert_safe_json_failure(
        captured,
        exit_code=exit_code,
        expected_exit_code=3,
        expected_error_code="input.invalid",
        forbidden=(str(csv_path), csv_path.name),
    )


def test_analyze_budget_error_maps_to_stable_exit_three_json_without_secrets(
    tmp_path,
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(analysis_module, "MAX_DIMENSION_TOKENS_PER_CELL", 1, raising=False)
    csv_path = tmp_path / "SECRET-BUDGET-DATASET.csv"
    secret_label = "SECRET-BUDGET-LABEL"
    secret_value = "SECRET-BUDGET-VALUE"
    csv_path.write_text(
        f"出願人,スコア\nsafe|{secret_label},{secret_value}\n",
        encoding="utf-8",
    )
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(_valid_analysis_spec()), encoding="utf-8")

    exit_code = main(["analyze", str(csv_path), "--spec", str(spec_path), "--json"])

    captured = capsys.readouterr()
    payload = _assert_safe_json_failure(
        captured,
        exit_code=exit_code,
        expected_exit_code=3,
        expected_error_code="input.invalid",
        forbidden=(str(csv_path), csv_path.name, secret_label, secret_value),
    )
    assert payload["error"] == {
        "code": "input.invalid",
        "message": "Dataset input could not be read or parsed",
        "retryable": False,
        "details": {},
    }


def test_inspect_command_rejects_invalid_csv_without_raw_value_leakage(tmp_path, capsys):
    csv_path = tmp_path / "invalid.csv"
    csv_path.write_text("出願人,スコア\nA社,RAW-CELL-VALUE,extra\n", encoding="utf-8")

    exit_code = main(["inspect", str(csv_path), "--json"])

    captured = capsys.readouterr()
    _assert_safe_json_failure(
        captured,
        exit_code=exit_code,
        expected_exit_code=3,
        expected_error_code="input.invalid",
        forbidden=(str(csv_path), csv_path.name, "RAW-CELL-VALUE"),
    )


def test_analyze_command_rejects_missing_referenced_columns_as_analysis_error(tmp_path, capsys):
    csv_path, _ = _write_analysis_csv(tmp_path)
    cases = [
        ("SECRET-MISSING-DIMENSION", {"mode": "count", "column": None}),
        ("出願人", {"mode": "sum", "column": "SECRET-MISSING-MEASURE"}),
    ]

    for index, (dimension, measure) in enumerate(cases):
        spec = _valid_analysis_spec()
        spec["dimension"] = dimension
        spec["measure"] = measure
        spec_path = tmp_path / f"spec-{index}.json"
        spec_path.write_text(json.dumps(spec), encoding="utf-8")

        exit_code = main(["analyze", str(csv_path), "--spec", str(spec_path), "--json"])

        captured = capsys.readouterr()
        _assert_safe_json_failure(
            captured,
            exit_code=exit_code,
            expected_exit_code=2,
            expected_error_code="analysis.invalid",
            forbidden=(str(spec_path), dimension, str(measure["column"])),
        )


def test_analysis_commands_reject_json_option_abbreviation(capsys):
    for argv in (["inspect", "dataset.csv", "--j"], ["analyze", "dataset.csv", "--j"]):
        exit_code = main(argv)

        captured = capsys.readouterr()
        assert exit_code == 4
        assert captured.out == ""
        assert captured.err == "Invalid patent-analysis command-line arguments\n"


def test_inspect_human_failure_is_short_and_only_on_stderr(tmp_path, capsys):
    csv_path = tmp_path / "secret-dataset-name.csv"

    exit_code = main(["inspect", str(csv_path)])

    captured = capsys.readouterr()
    assert exit_code == 3
    assert captured.out == ""
    assert captured.err == "Dataset input could not be read or parsed\n"
    assert str(csv_path) not in captured.err


def test_validate_command_resolves_valid_relative_plan_against_allowed_root(
    tmp_path,
    monkeypatch,
    capsys,
):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "intent": "applicant ranking",
                "operations": [
                    {
                        "type": "create_analysis",
                        "params": {"analysis_type": "ranking", "x": "applicant"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path.parent)

    exit_code = main(["validate-plan", "plan.json", "--json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "contract_version": "1.0.0",
        "ok": True,
    }


def test_validate_command_returns_two_without_traceback_for_invalid_plan(tmp_path, capsys):
    plan_path = tmp_path / "invalid-plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "intent": "unsafe",
                "operations": [{"type": "run_anything", "params": {}}],
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(["validate-plan", str(plan_path), "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 2
    assert captured.err == ""
    assert payload["ok"] is False
    assert payload["error"]["code"] == "operation.unknown"
    assert payload["error"]["retryable"] is False
    assert "Traceback" not in captured.out


def test_missing_command_returns_usage_error_as_json(capsys):
    exit_code = main(["--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 4
    assert captured.err == ""
    assert payload["error"]["code"] == "usage.invalid"
    assert payload["ok"] is False


def test_unknown_command_returns_usage_error_without_traceback(capsys):
    exit_code = main(["--json", "unknown-command"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 4
    assert captured.err == ""
    assert payload["error"]["code"] == "usage.invalid"
    assert payload["error"]["message"] == "Invalid patent-analysis command-line arguments"


def test_missing_validate_source_returns_json_without_argparse_stderr(capsys):
    exit_code = main(["validate-plan", "--json"])

    captured = capsys.readouterr()
    assert exit_code == 4
    assert captured.err == ""
    assert json.loads(captured.out)["error"]["code"] == "usage.invalid"


def test_json_help_request_returns_structured_usage_error_only(capsys):
    for argv in (
        ["--help", "--json"],
        ["validate-plan", "--help", "--json"],
        ["inspect", "--help", "--json"],
        ["analyze", "--help", "--json"],
    ):
        exit_code = main(argv)

        captured = capsys.readouterr()
        assert exit_code == 4
        assert captured.err == ""
        assert json.loads(captured.out)["error"]["code"] == "usage.invalid"


def test_analyze_missing_spec_returns_structured_usage_error_only(capsys):
    exit_code = main(["analyze", "dataset.csv", "--json"])

    captured = capsys.readouterr()
    assert exit_code == 4
    assert captured.err == ""
    assert json.loads(captured.out)["error"]["code"] == "usage.invalid"


def test_json_option_abbreviation_is_rejected(capsys):
    exit_code = main(["contract", "--j"])

    captured = capsys.readouterr()
    assert exit_code == 4
    assert captured.out == ""
    assert captured.err == "Invalid patent-analysis command-line arguments\n"


def test_validate_command_returns_three_for_unreadable_or_malformed_input(tmp_path, capsys):
    missing_path = tmp_path / "missing.json"

    exit_code = main(["validate-plan", str(missing_path), "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 3
    assert captured.err == ""
    assert payload["error"]["code"] == "input.invalid"


def test_validate_command_returns_three_for_malformed_json(tmp_path, capsys):
    malformed_path = tmp_path / "malformed.json"
    malformed_path.write_text('{"intent":', encoding="utf-8")

    exit_code = main(["validate-plan", str(malformed_path), "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 3
    assert captured.err == ""
    assert payload["error"]["code"] == "input.invalid"


def test_validate_command_rejects_non_standard_json_numbers(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "stdin",
        StringIO(
            '{"intent":"finite only","operations":[{"type":"set_filter",'
            '"params":{"field":"score","operator":"eq","value":NaN}}]}'
        ),
    )

    exit_code = main(["validate-plan", "-", "--json"])

    captured = capsys.readouterr()
    assert exit_code == 3
    assert captured.err == ""
    assert json.loads(captured.out)["error"]["code"] == "input.invalid"


def test_validate_command_rejects_oversized_stdin(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", StringIO(" " * (MAX_INPUT_BYTES + 1)))

    exit_code = main(["validate-plan", "-", "--json"])

    captured = capsys.readouterr()
    assert exit_code == 3
    assert captured.err == ""
    assert json.loads(captured.out)["error"]["code"] == "input.invalid"


def test_validate_command_rejects_oversized_verified_file(tmp_path, capsys):
    plan_path = tmp_path / "oversized-plan.json"
    plan_path.write_bytes(b" " * (MAX_INPUT_BYTES + 1))

    exit_code = main(["validate-plan", str(plan_path), "--json"])

    captured = capsys.readouterr()
    assert exit_code == 3
    assert captured.err == ""
    assert json.loads(captured.out)["error"] == {
        "code": "input.invalid",
        "message": "OperationPlan input could not be read or parsed",
        "retryable": False,
        "details": {},
    }


def test_validate_command_maps_excessive_json_nesting_to_stable_contract_error(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", StringIO("[" * 1_100 + "]" * 1_100))

    exit_code = main(["validate-plan", "-", "--json"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.err == ""
    assert "Traceback" not in captured.out
    assert json.loads(captured.out)["error"]["code"] == "contract.invalid"


def test_python_module_entrypoint_preserves_json_stdout_contract():
    project_root = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(project_root / "src")

    completed = subprocess.run(
        [sys.executable, "-m", "patent_analysis", "contract", "--json"],
        cwd=project_root,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert completed.returncode == 0
    assert completed.stderr == ""
    assert json.loads(completed.stdout)["contract_version"] == "1.0.0"


def _run_module_with_cp932_stdout(project_root: Path, *arguments: str):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(project_root / "src")
    environment["PYTHONIOENCODING"] = "cp932"

    return subprocess.run(
        [sys.executable, "-m", "patent_analysis", *arguments],
        cwd=project_root,
        env=environment,
        capture_output=True,
        check=False,
    )


def test_python_module_inspect_json_is_ascii_safe_with_cp932_stdout(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    csv_path = tmp_path / "emoji-inspect.csv"
    csv_path.write_bytes("😀列,値\n😀,1\n".encode())

    completed = _run_module_with_cp932_stdout(
        project_root,
        "inspect",
        str(csv_path),
        "--json",
    )

    assert completed.returncode == 0
    assert completed.stderr == b""
    ascii_stdout = completed.stdout.decode("ascii")
    assert ascii_stdout.encode("utf-8") == completed.stdout
    payload = json.loads(ascii_stdout)
    assert payload["dataset"]["columns"] == ["😀列", "値"]


def test_python_module_analyze_json_is_ascii_safe_with_cp932_stdout(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    csv_path = tmp_path / "emoji-analyze.csv"
    csv_path.write_bytes("😀列,値\n😀,1\nA社,2\n".encode())
    spec_path = tmp_path / "emoji-spec.json"
    spec = _valid_analysis_spec()
    spec["dimension"] = "😀列"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")

    completed = _run_module_with_cp932_stdout(
        project_root,
        "analyze",
        str(csv_path),
        "--spec",
        str(spec_path),
        "--json",
    )

    assert completed.returncode == 0
    assert completed.stderr == b""
    ascii_stdout = completed.stdout.decode("ascii")
    assert ascii_stdout.encode("utf-8") == completed.stdout
    payload = json.loads(ascii_stdout)
    assert payload["result"]["dimension"] == "😀列"
    assert any(row["label"] == "😀" for row in payload["result"]["rows"])


def test_v2_missing_column_returns_safe_json_input_error(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    spec = json.loads((project_root / "examples/basic/composition.json").read_bytes())
    spec["resolution"]["bindings"]["group"] = "PRIVATE-MISSING-COLUMN"
    spec_bytes = json.dumps(spec).encode("utf-8")
    source_bytes = b"group,year\nPRIVATE-CELL,2021\n"
    (tmp_path / "input.csv").write_bytes(source_bytes)
    (tmp_path / "spec.json").write_bytes(spec_bytes)

    completed = _run_module_with_cp932_stdout(
        project_root, "analyze", "input.csv", "--spec", "spec.json", "--json"
    )

    assert completed.returncode == 3
    assert completed.stderr == b""
    assert json.loads(completed.stdout) == {
        "analysis_contract_version": "1.0.0",
        "ok": False,
        "error": {
            "code": "input.invalid",
            "message": "Dataset input could not be read or parsed",
            "retryable": False,
            "details": {},
        },
    }
    assert (tmp_path / "input.csv").read_bytes() == source_bytes
    assert (tmp_path / "spec.json").read_bytes() == spec_bytes


@pytest.mark.parametrize(
    ("effect", "expected"),
    [
        ("include", {"Arabic": 1, "Ascii": 1, "Fullwidth": 1}),
        ("exclude", {"Blank": 1, "Malformed": 1, "Outside": 1, "Superscript": 1}),
    ],
)
def test_v2_year_filter_ignores_non_decimal_digits(tmp_path, effect, expected):
    project_root = Path(__file__).resolve().parents[1]
    spec = json.loads((project_root / "examples/basic/composition.json").read_bytes())
    spec["resolution"]["bindings"]["raw_year"] = "year"
    spec["population"]["filters"] = [{
        "role": "raw_year",
        "match": "year_range",
        "effect": effect,
        "start_year": 2020,
        "end_year": 2025,
    }]
    spec_bytes = json.dumps(spec).encode("utf-8")
    source_bytes = (
        "group,year\nAscii,2021\nFullwidth,２０２２\nArabic,٢٠٢٣\n"
        "Superscript,²⁰²¹\nBlank,\nOutside,2019\nMalformed,2021abc\n"
    ).encode()
    (tmp_path / "input.csv").write_bytes(source_bytes)
    (tmp_path / "spec.json").write_bytes(spec_bytes)

    completed = _run_module_with_cp932_stdout(
        project_root, "analyze", "input.csv", "--spec", "spec.json", "--json"
    )

    assert completed.returncode == 0
    assert completed.stderr == b""
    payload = json.loads(completed.stdout)
    assert {item["label"]: item["value"] for item in payload["data"]["items"]} == expected
    assert payload["population"] == {
        "input_rows": 7, "analyzed_rows": len(expected), "excluded_rows": 7 - len(expected),
    }
    assert (tmp_path / "input.csv").read_bytes() == source_bytes
    assert (tmp_path / "spec.json").read_bytes() == spec_bytes
