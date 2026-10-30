"""Ranking v2 keeps common population selection separate from contributions."""

from __future__ import annotations

import csv
import io
import json
from copy import deepcopy
from importlib.resources import files
from pathlib import Path

import pytest

from patent_analysis.analyses import ranking
from patent_analysis.analysis_contracts import (
    AnalysisContractError,
    StrictDraft202012Validator,
    validate_analysis_result,
)
from patent_analysis.normalization import NormalizedRow
from patent_analysis.population import PopulationReceipt, PopulationResult
from patent_analysis.v2_contracts import validate_analysis_result_v2


def _row(ordinal: int, **roles: tuple[str, ...]) -> NormalizedRow:
    return NormalizedRow(ordinal, (), roles)


def _population(*rows: NormalizedRow) -> PopulationResult:
    return PopulationResult(
        rows,
        PopulationReceipt("1.0.0", "a" * 64, "b" * 64, "records", 0, len(rows), len(rows), 0),
    )


def _spec(**parameters: object) -> dict:
    return {
        "analysis_contract_version": "2.0.0",
        "analysis_id": "ranking.v2",
        "resolution": {
            "bindings": {
                "group": "group", "score": "score", "family_id": "family",
                "filing_date": "filed", "year": "filed", "status": "status",
            }
        },
        "normalization": {"profiles": []},
        "population": {"filters": [], "selection_sets": [], "family_mode": "records"},
        "parameters": {"role": "group", **parameters},
    }


def _csv(path: Path, rows: list[list[str]]) -> bytes:
    stream = io.StringIO(newline="")
    csv.writer(stream, lineterminator="\n").writerows(rows)
    raw = stream.getvalue().encode("utf-8")
    path.write_bytes(raw)
    return raw


def _schema(name: str) -> dict:
    return json.loads(files("patent_analysis").joinpath("schemas", name).read_text("utf-8"))


def test_all_contributions_keep_blank_and_real_other_distinct_from_remainder() -> None:
    result = ranking.analyze_ranking(
        _population(
            _row(1, group=("その他", "A")),
            _row(2, group=("その他",)),
            _row(3, group=()),
            _row(4, group=("B", "C")),
        ),
        {"role": "group", "top_n": 1},
    )
    assert result["population"] == {"input_rows": 4, "analyzed_rows": 6}
    assert result["rows"] == [
        {"row_kind": "dimension_value", "label": "その他", "value": 2,
         "count": 2, "share": pytest.approx(2 / 6)},
        {"row_kind": "remainder", "label": "その他", "value": 4,
         "count": 4, "share": pytest.approx(4 / 6)},
    ]
    full = ranking.analyze_ranking(_population(_row(1, group=())), {"role": "group"})
    assert full["rows"][0]["label"] == "(空白)"
    assert validate_analysis_result(result) == result


def test_tokens_are_not_resplit_and_first_preserves_normalized_order() -> None:
    population = _population(
        _row(1, group=("B|C", "A", "B|C")), _row(2, group=("A",)),
    )
    all_values = ranking.analyze_ranking(population, {"role": "group"})
    assert [row["label"] for row in all_values["rows"]] == ["A", "B|C"]
    first = ranking.analyze_ranking(population, {"role": "group", "multi_value_mode": "first"})
    assert first["population"]["analyzed_rows"] == 2
    assert [row["label"] for row in first["rows"]] == ["A", "B|C"]
    assert [row["value"] for row in first["rows"]] == [1, 1]


@pytest.mark.parametrize("mode", ["count", "sum", "average", "max", "min"])
def test_top_n_does_not_change_share_denominator(mode: str) -> None:
    parameters = {"role": "group", "measure": mode, "top_n": 1, "include_other": False}
    if mode != "count":
        parameters["measure_role"] = "score"
    population = _population(
        _row(1, group=("A",), score=("30",)),
        _row(2, group=("A",), score=("30",)),
        _row(3, group=("B",), score=("20",)),
    )
    top = ranking.analyze_ranking(population, parameters)["rows"][0]
    assert top["label"] == "A"
    assert top["share"] == pytest.approx(0.75 if mode == "sum" else 2 / 3)


@pytest.mark.parametrize("mode, expected", [("sum", 33), ("average", 11), ("max", 30), ("min", 1)])
def test_remainder_reaggregates_contributions_not_bucket_averages(
    mode: str, expected: float,
) -> None:
    population = _population(
        _row(1, group=("A",), score=("100",)),
        _row(2, group=("B",), score=("1",)),
        _row(3, group=("B",), score=("2",)),
        _row(4, group=("C",), score=("30",)),
    )
    result = ranking.analyze_ranking(
        population, {"role": "group", "measure": mode, "measure_role": "score", "top_n": 1},
    )
    assert result["rows"][1]["value"] == expected
    assert result["rows"][1]["count"] == 3


def test_remainder_does_not_deduplicate_multi_value_contributions() -> None:
    result = ranking.analyze_ranking(
        _population(
            _row(1, group=("A",), score=("100",)),
            _row(2, group=("B", "C"), score=("10",)),
            _row(3, group=("D",), score=("40",)),
        ),
        {"role": "group", "measure": "average", "measure_role": "score", "top_n": 1},
    )
    assert result["rows"][1]["value"] == 20
    assert result["rows"][1]["count"] == 3


@pytest.mark.parametrize(
    "mode, expected", [("sum", 1202), ("average", 601), ("max", 1200), ("min", 2)],
)
def test_numeric_values_use_first_finite_normalized_token(mode: str, expected: float) -> None:
    result = ranking.analyze_ranking(
        _population(
            _row(1, group=("A",), score=("bad", "1,200", "99")),
            _row(2, group=("A",), score=("NaN", "Infinity", "2")),
            _row(3, group=("A",), score=("invalid",)),
        ),
        {"role": "group", "measure": mode, "measure_role": "score"},
    )
    assert result["rows"][0]["value"] == expected
    assert result["rows"][0]["count"] == 3


@pytest.mark.parametrize(
    "scores, shares", [(("10", "-2"), (1.25, -0.25)), (("0", "0"), (0.5, 0.5))],
)
def test_sum_share_retains_legacy_positive_total_rule(scores, shares) -> None:
    result = ranking.analyze_ranking(
        _population(_row(1, group=("A",), score=(scores[0],)),
                    _row(2, group=("B",), score=(scores[1],))),
        {"role": "group", "measure": "sum", "measure_role": "score"},
    )
    assert [row["share"] for row in result["rows"]] == list(shares)


def test_empty_population_has_no_invented_bucket() -> None:
    result = ranking.analyze_ranking(_population(), {"role": "group"})
    assert result["rows"] == []
    assert result["population"] == {"input_rows": 0, "analyzed_rows": 0}


@pytest.mark.parametrize("parameters", [
    {}, {"role": ""}, {"role": " "}, {"role": "x" * 65},
    {"role": "group", "top_n": True}, {"role": "group", "top_n": 0},
    {"role": "group", "top_n": 101}, {"role": "group", "top_n": 1.5},
    {"role": "group", "include_other": 1}, {"role": "group", "measure": "median"},
    {"role": "group", "measure": "sum"}, {"role": "group", "measure_role": "score"},
    {"role": "group", "measure_role": None},
    {"role": "group", "measure": "sum", "measure_role": " "},
    {"role": "group", "measure": "sum", "measure_role": "x" * 65},
    {"role": "group", "multi_value_mode": "both"}, {"role": "group", "unknown": 1},
])
def test_invalid_parameters_fail_closed_in_runtime_and_schema(parameters: dict) -> None:
    with pytest.raises(ValueError):
        ranking.required_roles(parameters)
    validator = StrictDraft202012Validator(_schema("ranking-parameters-v2.schema.json"))
    assert not validator.is_valid({**_spec(), "parameters": parameters})


def test_required_roles_and_defaults() -> None:
    assert ranking.required_roles({"role": "group"}) == ("group",)
    assert ranking.required_roles({"role": "group", "measure": "sum", "measure_role": "score"}) == (
        "group", "score",
    )
    assert ranking.required_roles({"role": "score", "measure": "sum", "measure_role": "score"}) == (
        "score",
    )
    assert ranking._validate_parameters({"role": "group"}) == {
        "role": "group", "measure": "count", "measure_role": None,
        "top_n": 10, "include_other": True, "multi_value_mode": "all",
    }


@pytest.mark.parametrize("limit", ["MAX_EXPANDED_CONTRIBUTIONS", "MAX_DISTINCT_BUCKETS"])
def test_bounded_failure_leaves_population_unchanged(monkeypatch, limit: str) -> None:
    monkeypatch.setattr(ranking, limit, 2)
    population = _population(_row(1, group=("A", "B", "C")))
    before = population.to_dict()
    with pytest.raises(ValueError, match="limit"):
        ranking.analyze_ranking(population, {"role": "group"})
    assert population.to_dict() == before


@pytest.mark.parametrize("mode", ["sum", "average"])
def test_non_finite_aggregate_fails_closed(mode: str) -> None:
    with pytest.raises(AnalysisContractError, match="finite"):
        ranking.analyze_ranking(
            _population(_row(1, group=("A",), score=("1e308",)),
                        _row(2, group=("A",), score=("1e308",))),
            {"role": "group", "measure": mode, "measure_role": "score"},
        )


def test_wrapper_filters_and_selection_sets_precede_family_selection(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    raw = _csv(source, [
        ["family", "filed", "group", "status"],
        ["F", "2018-01-01", "outside", "keep"],
        ["F", "2020-01-01", "selection-excluded", "drop"],
        ["F", "2020-09-01", "A|B", "keep"],
        ["G", "2020-10-01", "must-not-win", "keep"],
        ["G", "2020-01-01", "", "keep"],
    ])
    spec = _spec()
    spec["population"] = {
        "family_mode": "earliest", "family_role": "family_id", "date_role": "year",
        "filters": [{"role": "year", "effect": "include", "match": "year", "value": 2020}],
        "selection_sets": [{"dimension_role": "status", "mode": "include", "values": ["keep"]}],
    }
    before = deepcopy(spec)
    result = ranking.analyze_ranking_csv(source, spec, allowed_root=tmp_path)
    assert result["population"] == {"input_rows": 5, "analyzed_rows": 2, "excluded_rows": 3}
    assert result["data"]["population"] == {"input_rows": 2, "analyzed_rows": 3}
    assert {row["label"] for row in result["data"]["rows"]} == {"A", "B", "(空白)"}
    assert result["family_selection"]["matched_rows"] == 3
    assert result["family_selection"]["representative_rows"] == 2
    assert result["family_selection"]["collapsed_rows"] == 1
    assert validate_analysis_result_v2(result) == result
    assert source.read_bytes() == raw and spec == before
    assert result == ranking.analyze_ranking_csv(source, spec, allowed_root=tmp_path)


def test_wrapper_equal_missing_dates_and_missing_family_are_stable(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    _csv(source, [
        ["family", "filed", "group"],
        ["tie", "2020-01-01", "tie-first"], ["tie", "2020/01/01", "tie-second"],
        ["missing", "", "missing-first"], ["missing", "2019-01-01", "missing-second"],
        ["", "2020-01-01", "blank-one"], ["", "2020-01-01", "blank-two"],
    ])
    spec = _spec()
    spec["population"].update(
        family_mode="earliest", family_role="family_id", date_role="filing_date",
    )
    result = ranking.analyze_ranking_csv(source, spec, allowed_root=tmp_path)
    assert {row["label"] for row in result["data"]["rows"]} == {
        "tie-first", "missing-first", "blank-one", "blank-two",
    }
    assert result["family_selection"]["unidentified_rows"] == 2
    del spec["population"]["date_role"]
    no_date = ranking.analyze_ranking_csv(source, spec, allowed_root=tmp_path)
    assert no_date["data"] == result["data"]
    assert no_date["family_selection"]["date_role"] is None


def test_wrapper_records_numeric_and_schemas(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    _csv(source, [["group", "score"], ["A|B", "bad|1,200|99"], ["A", "2e1"]])
    spec = _spec(measure="sum", measure_role="score", multi_value_mode="first")
    result = ranking.analyze_ranking_csv(source, spec, allowed_root=tmp_path)
    assert result["data"]["rows"][0]["value"] == 1220
    assert result["data"]["measure"] == {"mode": "sum", "column": "score"}
    assert result["analysis_id"] == "ranking.v2" and result["result_variant"] == "ranking"
    assert result["algorithm_version"] == "1.0.0" and "family_selection" not in result
    for name, value in (("ranking-parameters-v2.schema.json", spec),
                        ("ranking-result-v2.schema.json", result["data"])):
        schema = _schema(name)
        StrictDraft202012Validator.check_schema(schema)
        StrictDraft202012Validator(schema).validate(value)
    assert validate_analysis_result(result["data"]) == result["data"]


@pytest.mark.parametrize(
    "changes", [{"analysis_id": "ranking.v1"}, {"analysis_contract_version": "1.0.0"}],
)
def test_wrapper_rejects_wrong_contract_before_source_read(tmp_path: Path, changes: dict) -> None:
    with pytest.raises(ValueError, match="spec"):
        ranking.analyze_ranking_csv("missing.csv", {**_spec(), **changes}, allowed_root=tmp_path)
