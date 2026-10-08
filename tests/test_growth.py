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


def test_growth_compares_only_explicit_endpoint_years_and_orders_output() -> None:
    from patent_analysis.analyses.growth import analyze_growth

    population = _population(
        _row(1, year=("2018",), applicant=("A社",)),
        _row(2, year=("2018",), applicant=("A社",)),
        _row(3, year=("2020",), applicant=("A社",)),
        _row(4, year=("2022",), applicant=("A社",)),
        _row(5, year=("2022",), applicant=("A社",)),
        _row(6, year=("2022",), applicant=("A社",)),
        _row(7, year=("2022",), applicant=("A社",)),
        _row(8, year=("2022",), applicant=("A社",)),
        _row(9, year=("2018",), applicant=("B社",)),
        _row(10, year=("2018",), applicant=("B社",)),
        _row(11, year=("2022",), applicant=("C社",)),
        _row(12, year=("2022",), applicant=("C社",)),
        _row(13, year=("Filed 2022",), applicant=("A社",)),
        _row(14, year=("2022",), applicant=()),
    )

    result = analyze_growth(
        population,
        {
            "date_role": "year",
            "series_role": "applicant",
            "start_year": 2018,
            "end_year": 2022,
            "top_n": 3,
        },
    )

    assert result["x"] == ["2018", "2022"]
    assert [item["label"] for item in result["series"]] == ["C社", "A社", "B社"]
    by_label = {item["label"]: item for item in result["series"]}
    assert by_label["A社"] == {
        "label": "A社",
        "values": [2, 5],
        "row_counts": [2, 5],
        "is_other": False,
        "growth_rate": 1.5,
        "growth_state": "measured",
    }
    assert by_label["B社"]["growth_rate"] == -1.0
    assert by_label["B社"]["growth_state"] == "measured"
    assert by_label["C社"]["growth_rate"] is None
    assert by_label["C社"]["growth_state"] == "new"
    assert result["population"] == {
        "input_rows": 14,
        "visible_rows": 11,
        "invalid_year_rows": 1,
        "outside_endpoint_rows": 1,
        "blank_series_rows": 1,
        "excluded_rows": 3,
    }
    assert result["contributions"] == 11


def test_growth_dedupes_repeated_labels_within_each_source_row() -> None:
    from patent_analysis.analyses.growth import analyze_growth

    result = analyze_growth(
        _population(
            _row(1, year=("2018",), applicant=("A", "A", "B")),
            _row(2, year=("2022",), applicant=("A", "B")),
        ),
        {
            "date_role": "year",
            "series_role": "applicant",
            "start_year": 2018,
            "end_year": 2022,
            "top_n": 20,
        },
    )

    assert result["contributions"] == 4
    assert [item["values"] for item in result["series"]] == [[1, 1], [1, 1]]


def test_growth_required_roles_and_parameters_are_closed() -> None:
    from patent_analysis.analyses.growth import analyze_growth, required_roles

    parameters = {
        "date_role": "year",
        "series_role": "applicant",
        "start_year": 2018,
        "end_year": 2022,
        "top_n": 20,
    }
    assert required_roles(parameters) == ("year", "applicant")

    with pytest.raises(ValueError, match="must differ"):
        analyze_growth(
            _population(),
            {**parameters, "series_role": "year"},
        )
    with pytest.raises(ValueError, match="year range"):
        analyze_growth(
            _population(),
            {**parameters, "end_year": 2018},
        )
    with pytest.raises(ValueError, match="top_n"):
        analyze_growth(
            _population(),
            {**parameters, "top_n": 21},
        )
    with pytest.raises(ValueError, match="unsupported"):
        analyze_growth(
            _population(),
            {**parameters, "include_other": True},
        )


def test_growth_contribution_guard_fails_before_limit_plus_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import patent_analysis.analyses.growth as growth

    monkeypatch.setattr(growth, "MAX_EXPANDED_CONTRIBUTIONS", 2)
    population = _population(
        _row(1, year=("2018",), applicant=("A", "B")),
        _row(2, year=("2022",), applicant=("C",)),
    )

    with pytest.raises(growth.GrowthBudgetError, match="contributions"):
        growth.analyze_growth(
            population,
            {
                "date_role": "year",
                "series_role": "applicant",
                "start_year": 2018,
                "end_year": 2022,
                "top_n": 20,
            },
        )


def test_growth_distinct_bucket_guard_fails_before_limit_plus_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import patent_analysis.analyses.growth as growth

    monkeypatch.setattr(growth, "MAX_DISTINCT_BUCKETS", 1)
    population = _population(
        _row(1, year=("2018",), applicant=("A", "B")),
    )

    with pytest.raises(growth.GrowthBudgetError, match="distinct buckets"):
        growth.analyze_growth(
            population,
            {
                "date_role": "year",
                "series_role": "applicant",
                "start_year": 2018,
                "end_year": 2022,
                "top_n": 20,
            },
        )
