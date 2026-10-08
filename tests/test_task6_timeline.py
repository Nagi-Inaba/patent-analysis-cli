from __future__ import annotations

from types import MappingProxyType

import pytest

from patent_analysis.normalization import NormalizedRow
from patent_analysis.population import PopulationReceipt, PopulationResult


def _row(ordinal: int, **roles: tuple[str, ...]) -> NormalizedRow:
    return NormalizedRow(
        source_ordinal=ordinal,
        source_fields=tuple(value for values in roles.values() for value in values),
        values_by_role=MappingProxyType(dict(roles)),
    )


def _population(*rows: NormalizedRow) -> PopulationResult:
    receipt = PopulationReceipt(
        population_contract_version="1.0.0",
        normalization_row_stream_sha256="a" * 64,
        population_spec_sha256="b" * 64,
        family_mode="records",
        filter_count=0,
        input_rows=len(rows),
        included_rows=len(rows),
        filtered_rows=0,
    )
    return PopulationResult(rows=tuple(rows), receipt=receipt)


def test_timeline_uses_only_canonical_year_values_and_orders_years_ascending() -> None:
    from patent_analysis.analyses.timeline import analyze_timeline

    population = _population(
        _row(1, year=("2021",), applicant=("A社", "B社"), score=("10",)),
        _row(2, year=("2020",), applicant=("A社",), score=("20",)),
        _row(3, year=("2021",), applicant=("C社",), score=("30",)),
        _row(4, year=("Filed 2022",), applicant=("A社",), score=("40",)),
        _row(5, year=("2019",), applicant=("A社",), score=("50",)),
    )

    result = analyze_timeline(
        population,
        {
            "date_role": "year",
            "series_role": "applicant",
            "start_year": 2020,
            "end_year": 2021,
            "top_n": 1,
            "include_other": True,
            "measure": "count",
        },
    )

    assert result["x"] == ["2020", "2021"]
    assert result["series"] == [
        {
            "label": "A社",
            "values": [1, 1],
            "row_counts": [1, 1],
            "is_other": False,
        },
        {
            "label": "その他（上位外）",
            "values": [0, 2],
            "row_counts": [0, 2],
            "is_other": True,
        },
    ]
    assert result["population"] == {
        "input_rows": 5,
        "visible_rows": 3,
        "invalid_year_rows": 1,
        "outside_year_range_rows": 1,
        "blank_series_rows": 0,
        "excluded_rows": 2,
    }
    assert result["contributions"] == 4


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("count", [1, 2]),
        ("sum", [10, 50]),
        ("average", [10, 25]),
        ("max", [10, 30]),
        ("min", [10, 20]),
    ],
)
def test_timeline_closed_measure_modes_are_deterministic(
    mode: str,
    expected: list[int],
) -> None:
    from patent_analysis.analyses.timeline import analyze_timeline

    population = _population(
        _row(1, year=("2020",), applicant=("A社",), score=("10",)),
        _row(2, year=("2021",), applicant=("A社",), score=("20",)),
        _row(3, year=("2021",), applicant=("A社",), score=("30",)),
    )
    parameters: dict[str, object] = {
        "date_role": "year",
        "series_role": "applicant",
        "top_n": 10,
        "include_other": True,
        "measure": mode,
    }
    if mode != "count":
        parameters["measure_role"] = "score"

    result = analyze_timeline(population, parameters)

    assert result["x"] == ["2020", "2021"]
    assert result["series"][0]["label"] == "A社"
    assert result["series"][0]["values"] == expected


def test_timeline_top_n_tie_break_is_measure_then_rows_then_label() -> None:
    from patent_analysis.analyses.timeline import analyze_timeline

    population = _population(
        _row(1, year=("2021",), applicant=("B社",), score=("10",)),
        _row(2, year=("2021",), applicant=("A社",), score=("10",)),
        _row(3, year=("2021",), applicant=("C社",), score=("5",)),
        _row(4, year=("2021",), applicant=("C社",), score=("5",)),
    )

    result = analyze_timeline(
        population,
        {
            "date_role": "year",
            "series_role": "applicant",
            "top_n": 3,
            "include_other": False,
            "measure": "sum",
            "measure_role": "score",
        },
    )

    assert [item["label"] for item in result["series"]] == ["C社", "A社", "B社"]


def test_timeline_required_roles_are_analysis_owned_and_stable() -> None:
    from patent_analysis.analyses.timeline import required_roles

    assert required_roles(
        {
            "date_role": "year",
            "series_role": "applicant",
            "measure": "sum",
            "measure_role": "score",
        }
    ) == ("year", "applicant", "score")
    assert required_roles(
        {
            "date_role": "year",
            "series_role": "applicant",
            "measure": "count",
        }
    ) == ("year", "applicant")


def test_timeline_contribution_guard_fails_before_excess_increment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import patent_analysis.analyses.timeline as timeline

    monkeypatch.setattr(timeline, "MAX_EXPANDED_CONTRIBUTIONS", 2)
    population = _population(
        _row(1, year=("2021",), applicant=("A", "B")),
        _row(2, year=("2021",), applicant=("C",)),
    )

    with pytest.raises(timeline.TimelineBudgetError, match="contributions"):
        timeline.analyze_timeline(
            population,
            {
                "date_role": "year",
                "series_role": "applicant",
                "measure": "count",
                "top_n": 10,
                "include_other": True,
            },
        )
