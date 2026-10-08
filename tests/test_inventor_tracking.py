"""Public inventor tracking contracts, analytical oracle, and bounded input failures."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from patent_analysis import api, cli
from patent_analysis.analysis_contracts import AnalysisContractError

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "inventor-tracking"
SPEC = json.loads((EXAMPLES / "spec.json").read_bytes())


def run(root=EXAMPLES, spec=None):
    return api.run_analysis_csv(
        "patents.csv", json.dumps(spec or SPEC).encode(), allowed_root=root,
    )


def test_tracking_golden_public_api_cli_and_tables(monkeypatch, capsys):
    before = (EXAMPLES / "patents.csv").read_bytes()
    result = run()
    expected = json.loads((EXAMPLES.parent / "expected-aggregates.json").read_bytes())
    assert result["data"] == expected["inventor-tracking.v1"]
    monkeypatch.setenv("PATENT_ANALYSIS_ALLOWED_ROOT", str(EXAMPLES))
    assert cli.main(["analyze", "patents.csv", "--spec", "spec.json", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == result
    for format_name in ("csv", "text"):
        table = api.run_analysis_table(
            "patents.csv", (EXAMPLES / "spec.json").read_bytes(),
            allowed_root=EXAMPLES, table_format=format_name,
        )
        assert "cluster_links" in table and "affiliation_changes" in table
        assert "OrgX" in table and "OrgY" in table
    assert (EXAMPLES / "patents.csv").read_bytes() == before


@pytest.mark.parametrize("mutation", [
    {"inventor_role": "year"}, {"inventor_role": ""}, {"top_n": 10},
    {"identity_kind": "fuzzy"},
])
def test_tracking_invalid_spec_fails_preflight(mutation):
    spec = deepcopy(SPEC)
    spec["parameters"].update(mutation)
    with pytest.raises(AnalysisContractError):
        api.validate_analysis_spec_bytes(json.dumps(spec).encode())


def test_tracking_row_order_invariance_and_population_filter(tmp_path):
    lines = (EXAMPLES / "patents.csv").read_text(encoding="utf-8").splitlines()
    (tmp_path / "patents.csv").write_text(
        "\n".join([lines[0], *reversed(lines[1:])]) + "\n", encoding="utf-8",
    )
    assert run(tmp_path)["data"] == run()["data"]
    spec = deepcopy(SPEC)
    spec["population"]["filters"] = [
        {"role": "year", "effect": "include", "match": "year", "value": 2021},
    ]
    filtered = run(spec=spec)["data"]
    assert filtered["years"] == [2021]
    assert filtered["cluster_links"] == [] and filtered["affiliation_changes"] == []


@pytest.mark.parametrize("rows", [
    [f"2020,I{i},Org" for i in range(21)],
    ["2000,A,Org", "2012,A,Org"],
    ["2020|2021,A,Org"],
])
def test_tracking_refuses_ambiguous_year_or_incomplete_map(tmp_path, rows):
    (tmp_path / "patents.csv").write_text(
        "year,inventor,applicant\n" + "\n".join(rows) + "\n", encoding="utf-8",
    )
    from patent_analysis.data import DatasetInputError
    with pytest.raises(DatasetInputError):
        run(tmp_path)


def test_tracking_empty_and_explicit_ids(tmp_path):
    (tmp_path / "patents.csv").write_text("year,inventor,applicant\n", encoding="utf-8")
    data = run(tmp_path)["data"]
    assert data["observations"] == [] and data["clusters"] == []
    (tmp_path / "patents.csv").write_text(
        "year,inventor,applicant\n2020,ID-01|ID-02,Org\n2021,ID-01,Org\n", encoding="utf-8",
    )
    spec = deepcopy(SPEC)
    spec["parameters"]["identity_kind"] = "id"
    data = run(tmp_path, spec)["data"]
    assert data["identity_kind"] == "id"
    assert [x["inventor"] for x in data["inventors"]] == ["ID-01", "ID-02"]


def test_tracking_transitive_cluster_and_partial_applicant_missingness(tmp_path):
    (tmp_path / "patents.csv").write_text(
        "year,inventor,applicant\n2020,A|B,OrgX\n2020,B|C,OrgY\n2020,A,\n2021,A,OrgZ\n",
        encoding="utf-8",
    )
    data = run(tmp_path)["data"]
    assert data["clusters"][0]["members"] == ["A", "B", "C"]
    assert data["observations"][0]["applicants"] == ["OrgX"]
    assert data["affiliation_changes"][0]["status"] == "unknown"
    assert data["affiliation_changes"][0]["added_applicants"] == []


def test_tracking_model_has_calendar_gaps_and_changes():
    from patent_analysis.chart_models.advanced import build_advanced_chart_model
    model, _ = build_advanced_chart_model(run(), analysis_id="inventor-tracking.v1")
    p = model["projection"]
    assert p["kind"] == "tracking"
    assert p["years"] == [2020, 2021, 2022, 2023]
    assert len(p["nodes"]) == 12 and len(p["links"]) == 8
    assert sum(n["changed"] for n in p["nodes"]) == 5
    assert sum(e["gap"] for e in p["links"]) == 1


def test_tracking_full_twenty_inventors_twelve_years_fits_public_result(tmp_path):
    (tmp_path / "patents.csv").write_text(
        "year,inventor,applicant\n" + "".join(
            f"{year},発明者{i:02d},企業{(i + year) % 7}株式会社\n"
            for year in range(2010, 2022) for i in range(1, 21)
        ), encoding="utf-8",
    )
    result = run(tmp_path)
    assert len(result["data"]["observations"]) == 240
    assert len(result["data"]["affiliation_changes"]) == 220
    assert result["data"]["contributions"] == 480
    from patent_analysis.chart_models.advanced import build_advanced_chart_model
    model, _ = build_advanced_chart_model(result, analysis_id="inventor-tracking.v1")
    assert len(model["projection"]["nodes"]) == 240


@pytest.mark.parametrize(
    "field", ["clusters", "cluster_links", "affiliation_changes", "affiliations"],
)
def test_tracking_render_refuses_inconsistent_aggregates(field):
    from patent_analysis.advanced_projection import project_advanced_data
    data = run()["data"]
    data[field].pop()
    with pytest.raises(ValueError):
        project_advanced_data("inventor-tracking.v1", data)


@pytest.mark.parametrize("kind, expected_names", [("name", ["A"]), ("id", ["A", "Ａ"])])
def test_tracking_name_compatibility_normalization_preserves_explicit_ids(
    tmp_path, kind, expected_names,
):
    (tmp_path / "patents.csv").write_text(
        "year,inventor,applicant\n2020,Ａ|A,OrgX\n2021,A,OrgY\n", encoding="utf-8",
    )
    spec = deepcopy(SPEC)
    spec["parameters"]["identity_kind"] = kind
    data = run(tmp_path, spec)["data"]
    assert [i["inventor"] for i in data["inventors"]] == expected_names
    assert data["inventors"][0]["count"] == 2
    assert data["affiliation_changes"][0]["status"] == "changed"


def test_tracking_large_applicant_set_is_valid_in_public_result_and_model(tmp_path):
    rows = ["|".join(f"Org{i}" for i in range(start, min(start + 100, 1001)))
            for start in range(0, 1001, 100)]
    (tmp_path / "patents.csv").write_text(
        "year,inventor,applicant\n" + "".join(f"2020,A,{names}\n" for names in rows),
        encoding="utf-8",
    )
    result = run(tmp_path)
    assert len(result["data"]["observations"][0]["applicants"]) == 1001
    assert result["data"]["contributions"] == 1012
    from patent_analysis.chart_models.advanced import build_advanced_chart_model
    model, _ = build_advanced_chart_model(result, analysis_id="inventor-tracking.v1")
    assert model["projection"]["nodes"][0]["applicants"].endswith("…")


@pytest.mark.parametrize("suffix", ["a" * 4090, "x" + "\u035c" * 2000])
def test_tracking_long_applicants_are_shortened_only_for_display(tmp_path, suffix):
    labels = [str(i) + suffix for i in range(5)]
    (tmp_path / "patents.csv").write_text(
        "year,inventor,applicant\n2020,A," + "|".join(labels) + "\n", encoding="utf-8",
    )
    result = run(tmp_path)
    from patent_analysis.chart_models.advanced import build_advanced_chart_model
    model, _ = build_advanced_chart_model(result, analysis_id="inventor-tracking.v1")
    assert result["data"]["observations"][0]["applicants"] == labels
    assert len(model["projection"]["nodes"][0]["applicants"]) <= 28
    assert model["projection"]["nodes"][0]["applicants"].endswith("…")


def test_tracking_display_shortening_does_not_hide_unsafe_suffix(tmp_path):
    (tmp_path / "patents.csv").write_text(
        "year,inventor,applicant\n2020,A," + "a" * 100 + "\u202e\n", encoding="utf-8",
    )
    from patent_analysis.chart_models.advanced import build_advanced_chart_model
    with pytest.raises(ValueError):
        build_advanced_chart_model(run(tmp_path), analysis_id="inventor-tracking.v1")
