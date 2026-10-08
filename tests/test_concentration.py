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


def test_concentration_hhi_uses_share_squared_sum_and_half_up_rounding() -> None:
    from patent_analysis.analyses.concentration import concentration_hhi

    assert concentration_hhi((50, 30, 20)) == 0.38
    assert concentration_hhi((2, 1)) == 0.556
    assert concentration_hhi((1,)) == 1.0


def test_concentration_classification_uses_persisted_thresholds() -> None:
    from patent_analysis.analyses.concentration import classify_hhi

    assert classify_hhi(0.149) == "competitive"
    assert classify_hhi(0.15) == "moderate"
    assert classify_hhi(0.25) == "moderate"
    assert classify_hhi(0.251) == "concentrated"


def test_concentration_orders_years_and_uses_expanded_contribution_denominator() -> None:
    from patent_analysis.analyses.concentration import analyze_concentration

    population = _population(
        _row(1, year=("2021",), applicant=("A",)),
        _row(2, year=("2020",), applicant=("A", "B")),
        _row(3, year=("2020",), applicant=("A",)),
        _row(4, year=("Filed 2021",), applicant=("A",)),
        _row(5, year=("2021",), applicant=()),
    )

    result = analyze_concentration(
        population,
        {"date_role": "year", "category_role": "applicant"},
    )

    assert result["x"] == ["2020", "2021"]
    assert result["series"] == [
        {
            "label": "HHI",
            "values": [0.556, 1.0],
            "row_counts": [2, 1],
            "contribution_counts": [3, 1],
            "classifications": ["concentrated", "concentrated"],
            "is_other": False,
        }
    ]
    assert result["population"] == {
        "input_rows": 5,
        "visible_rows": 3,
        "invalid_year_rows": 1,
        "blank_category_rows": 1,
        "excluded_rows": 2,
    }
    assert result["contributions"] == 4


def test_concentration_does_not_apply_top_n_or_other_before_hhi() -> None:
    from patent_analysis.analyses.concentration import analyze_concentration

    result = analyze_concentration(
        _population(
            _row(1, year=("2020",), applicant=("A",)),
            _row(2, year=("2020",), applicant=("B",)),
            _row(3, year=("2020",), applicant=("C",)),
            _row(4, year=("2020",), applicant=("D",)),
        ),
        {"date_role": "year", "category_role": "applicant"},
    )

    assert result["series"][0]["values"] == [0.25]
    assert result["series"][0]["classifications"] == ["moderate"]


def test_concentration_required_roles_and_parameters_are_closed() -> None:
    from patent_analysis.analyses.concentration import analyze_concentration, required_roles

    parameters = {"date_role": "year", "category_role": "applicant"}
    assert required_roles(parameters) == ("year", "applicant")

    with pytest.raises(ValueError, match="must differ"):
        analyze_concentration(
            _population(),
            {"date_role": "year", "category_role": "year"},
        )
    with pytest.raises(ValueError, match="unsupported"):
        analyze_concentration(
            _population(),
            {**parameters, "top_n": 10},
        )


def test_concentration_contribution_guard_fails_before_limit_plus_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import patent_analysis.analyses.concentration as concentration

    monkeypatch.setattr(concentration, "MAX_EXPANDED_CONTRIBUTIONS", 2)
    population = _population(
        _row(1, year=("2020",), applicant=("A", "B")),
        _row(2, year=("2020",), applicant=("C",)),
    )

    with pytest.raises(concentration.ConcentrationBudgetError, match="contributions"):
        concentration.analyze_concentration(
            population,
            {"date_role": "year", "category_role": "applicant"},
        )


def test_concentration_year_bucket_guard_fails_before_limit_plus_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import patent_analysis.analyses.concentration as concentration

    monkeypatch.setattr(concentration, "MAX_YEAR_BUCKETS", 1)
    population = _population(
        _row(1, year=("2020",), applicant=("A",)),
        _row(2, year=("2021",), applicant=("A",)),
    )

    with pytest.raises(concentration.ConcentrationBudgetError, match="year buckets"):
        concentration.analyze_concentration(
            population,
            {"date_role": "year", "category_role": "applicant"},
        )


def test_concentration_distinct_bucket_guard_fails_before_limit_plus_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import patent_analysis.analyses.concentration as concentration

    monkeypatch.setattr(concentration, "MAX_DISTINCT_BUCKETS", 1)
    population = _population(
        _row(1, year=("2020",), applicant=("A", "B")),
    )

    with pytest.raises(concentration.ConcentrationBudgetError, match="distinct buckets"):
        concentration.analyze_concentration(
            population,
            {"date_role": "year", "category_role": "applicant"},
        )
