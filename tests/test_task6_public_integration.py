from __future__ import annotations

import json
from pathlib import Path

import pytest

from patent_analysis.canonical_v2 import canonical_json_bytes
from patent_analysis.column_resolution import COLUMN_ALIAS_PROFILE

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "cli"


def _spec(analysis_id: str, parameters: dict[str, object]) -> bytes:
    return canonical_json_bytes(
        {
            "analysis_contract_version": "2.0.0",
            "analysis_id": analysis_id,
            "resolution": {
                "profile": COLUMN_ALIAS_PROFILE,
                "bindings": {
                    "filing_date": "出願日",
                    "applicant": "出願人",
                    "score": "スコア",
                },
            },
            "normalization": {"profiles": []},
            "population": {
                "filters": [],
                "selection_sets": [],
                "family_mode": "records",
            },
            "parameters": parameters,
        }
    )


def _source(tmp_path: Path) -> Path:
    path = tmp_path / "input.csv"
    path.write_text(
        "出願日,出願人,スコア\n"
        "2021-01-01,A社,10\n"
        "2022-01-01,A社,20\n"
        "2022-02-01,B社,30\n",
        encoding="utf-8",
    )
    return path


def test_public_v2_execution_rejects_oversized_canonical_result_without_label_leakage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import patent_analysis.analysis_budgets as analysis_budgets
    from patent_analysis.analysis_contracts import AnalysisContractError
    from patent_analysis.api import run_analysis_csv

    secret_label = "SECRET-LABEL-" + "A" * 1_024
    source = tmp_path / "input.csv"
    source.write_text(
        f"出願日,出願人,スコア\n2021-01-01,{secret_label},10\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(analysis_budgets, "MAX_CANONICAL_NEUTRAL_RESULT_BYTES", 512)

    with pytest.raises(AnalysisContractError) as caught:
        run_analysis_csv(
            source.name,
            _spec(
                "timeline.v1",
                {
                    "date_role": "filing_date",
                    "series_role": "applicant",
                    "top_n": 10,
                    "include_other": True,
                    "measure": "count",
                },
            ),
            allowed_root=tmp_path,
        )

    assert caught.value.code == "analysis.invalid"
    assert caught.value.details == {}
    assert secret_label not in str(caught.value)


def test_timeline_cli_human_mode_reports_the_v2_result_without_v1_assumptions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from patent_analysis.cli import main

    source = _source(tmp_path)
    spec = tmp_path / "timeline-spec.json"
    spec.write_bytes(
        _spec(
            "timeline.v1",
            {
                "date_role": "filing_date",
                "series_role": "applicant",
                "top_n": 10,
                "include_other": True,
                "measure": "count",
            },
        )
    )
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))

    assert main(["analyze", source.name, "--spec", spec.name]) == 0
    captured = capsys.readouterr()
    assert captured.out == "Analysis complete: timeline.v1 (series)\n"
    assert captured.err == ""


@pytest.mark.parametrize("fixture_name", ["timeline", "composition"])
def test_task6_source_derived_cli_golden_is_byte_stable(fixture_name: str) -> None:
    from patent_analysis.api import run_analysis_csv

    fixture = FIXTURE_ROOT / fixture_name
    spec = (fixture / "spec.json").read_bytes()
    expected = json.loads((fixture / "expected.json").read_text(encoding="utf-8"))

    first = run_analysis_csv("input.csv", spec, allowed_root=fixture)
    second = run_analysis_csv("input.csv", spec, allowed_root=fixture)

    assert canonical_json_bytes(first) == canonical_json_bytes(second)
    if fixture_name == "timeline":
        projection = {
            "analysis_id": first["analysis_id"],
            "x": first["data"]["x"],
            "series": [
                {"label": item["label"], "values": item["values"]}
                for item in first["data"]["series"]
            ],
        }
    else:
        projection = {
            "analysis_id": first["analysis_id"],
            "items": [
                {
                    key: item[key]
                    for key in ("label", "value", "row_count", "share", "share_basis")
                }
                for item in first["data"]["items"]
            ],
        }
    assert projection == expected
