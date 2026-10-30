import json
from pathlib import Path

from patent_analysis import api, cli


def composition_spec():
    return {
        "analysis_contract_version": "2.0.0", "analysis_id": "composition.v1",
        "resolution": {"bindings": {"group": "group", "year": "year",
                                    "family": "family", "filed": "filed"}},
        "normalization": {"profiles": []},
        "population": {"filters": [{"role": "year", "effect": "include", "match": "year",
                                     "value": 2020}], "selection_sets": [],
                       "family_mode": "earliest", "family_role": "family",
                       "date_role": "filed"},
        "parameters": {"role": "group"},
    }


def test_preflight_counts_filters_and_representatives_without_exposing_cells(tmp_path):
    source = tmp_path / "data.csv"
    source.write_text("group,year,family,filed\nSECRET_A,2020,F,2020-01-01\n"
                      "SECRET_B,2020,F,2020-02-01\nSECRET_C,garbage,G,\n", encoding="utf-8")
    before = source.read_bytes()
    report = api.preflight_analysis(source, json.dumps(composition_spec()).encode(),
                                    allowed_root=tmp_path)
    assert report["checks_passed"] is True
    assert report["population"] == {"input_rows": 3, "matched_rows": 2,
                                     "selected_rows": 1, "filtered_rows": 1,
                                     "collapsed_rows": 1}
    year = next(r for r in report["roles"] if r["role"] == "year")
    assert year["invalid_date_rows"] == 1
    assert "SECRET" not in json.dumps(report)
    assert str(tmp_path) not in json.dumps(report)
    assert report["analysis_eligibility_checked"] is False
    assert source.read_bytes() == before


def test_preflight_reports_missing_column_as_a_fixable_role(tmp_path):
    (tmp_path / "data.csv").write_text("other\nsecret\n", encoding="utf-8")
    report = api.preflight_analysis("data.csv", json.dumps(composition_spec()).encode(),
                                    allowed_root=tmp_path)
    assert report["checks_passed"] is False
    assert report["population"] is None
    assert {r["role"] for r in report["roles"] if not r["bound"]} == {
        "group", "year", "family", "filed"
    }
    assert "secret" not in json.dumps(report)


def test_cli_validate_spec_with_dataset_keeps_spec_only_behavior(tmp_path, monkeypatch, capsys):
    spec = composition_spec()
    (tmp_path / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
    (tmp_path / "data.csv").write_text("other\nsecret\n", encoding="utf-8")
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(tmp_path))
    assert cli.main(["validate-spec", "spec.json", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["valid"] is True
    assert cli.main(["validate-spec", "spec.json", "--dataset", "data.csv", "--json"]) == 3
    assert json.loads(capsys.readouterr().out)["checks_passed"] is False


def test_v2_numeric_and_case_insensitive_year_roles_follow_normalized_values(tmp_path):
    spec = composition_spec()
    spec["analysis_id"] = "ranking.v2"
    spec["resolution"]["bindings"] = {"group": "group", "score": "score", "Year": "year"}
    spec["parameters"] = {"role": "group", "measure": "sum", "measure_role": "score"}
    spec["population"] = {"filters": [{"role": "Year", "effect": "include", "match": "year",
                                       "value": 2020}], "selection_sets": [],
                          "family_mode": "records"}
    (tmp_path / "data.csv").write_text(
        'group,score,year\nA,not-a-number,2020\nB,NaN,2020\nC,"1,200",2020\n'
        'D,bad|2e1,nonsense\nE,,2020\n', encoding="utf-8",
    )
    report = api.preflight_analysis("data.csv", json.dumps(spec).encode(), allowed_root=tmp_path)
    roles = {r["role"]: r for r in report["roles"]}
    assert roles["score"]["invalid_numeric_rows"] == 2
    assert roles["score"]["missing_rows"] == 1
    assert roles["Year"]["invalid_date_rows"] == 1
    assert report["population"]["selected_rows"] == 4


def test_blank_date_is_missing_without_also_counting_as_invalid(tmp_path):
    (tmp_path / "data.csv").write_text(
        "group,year,family,filed\nA,2020,F,   \n", encoding="utf-8",
    )
    report = api.preflight_analysis(
        "data.csv", json.dumps(composition_spec()).encode(), allowed_root=tmp_path,
    )
    filed = next(r for r in report["roles"] if r["role"] == "filed")
    assert filed["missing_rows"] == 1
    assert filed["invalid_date_rows"] == 0
    assert report["population"]["selected_rows"] == 1


def test_native_inventor_dates_keep_strict_whitespace_validation(tmp_path):
    root = Path(__file__).resolve().parents[1] / "examples" / "inventor-analysis"
    spec = json.loads((root / "inventor-activity.v1.json").read_bytes())
    rows = json.loads((root / "patents.json").read_bytes())
    rows[0][spec["resolution"]["bindings"]["date"]] = "   "
    (tmp_path / "data.json").write_text(json.dumps(rows), encoding="utf-8")
    report = api.preflight_analysis("data.json", json.dumps(spec).encode(), allowed_root=tmp_path)
    date = next(r for r in report["roles"] if r["role"] == "date")
    assert date["invalid_date_rows"] == 1
    assert report["checks_passed"] is False
    assert {"code": "inventor.invalid_cells", "role": "date"} in report["issues"]
