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


def test_lifecycle_uses_peak_year_five_year_cagr_and_all_period_total() -> None:
    from patent_analysis.analyses.lifecycle import analyze_lifecycle

    population = _population(
        _row(1, year=("2020",), category=("X分類",)),
        _row(2, year=("2022",), category=("X分類",)),
        _row(3, year=("2022",), category=("X分類",)),
        _row(4, year=("2022",), category=("X分類",)),
        _row(5, year=("2024",), category=("X分類",)),
        _row(6, year=("2024",), category=("X分類",)),
        _row(7, year=("2018",), category=("Y分類",)),
        _row(8, year=("2018",), category=("Y分類",)),
        _row(9, year=("2018",), category=("Y分類",)),
        _row(10, year=("2018",), category=("Y分類",)),
        _row(11, year=("2020",), category=("Y分類",)),
        _row(12, year=("2024",), category=("Z分類",)),
        _row(13, year=("2024",), category=("Z分類",)),
    )

    result = analyze_lifecycle(
        population,
        {"date_role": "year", "category_role": "category", "top_n": 20},
    )

    assert result["window"] == {"start_year": 2020, "end_year": 2024, "years": 5}
    assert [item["label"] for item in result["points"]] == ["X分類", "Y分類", "Z分類"]
    by_label = {item["label"]: item for item in result["points"]}
    assert by_label["X分類"]["x"] == 2022
    assert by_label["X分類"]["y"] == pytest.approx(18.920711500272102)
    assert by_label["X分類"]["size"] == 6
    assert by_label["X分類"]["stage"] == "growth"
    assert by_label["Y分類"] == {
        "label": "Y分類",
        "x": 2018,
        "y": -100.0,
        "size": 5,
        "stage": "decline",
    }
    assert by_label["Z分類"] == {
        "label": "Z分類",
        "x": 2024,
        "y": 100.0,
        "size": 2,
        "stage": "growth",
    }
    assert result["contributions"] == 13


def test_lifecycle_peak_year_tie_uses_earliest_year() -> None:
    from patent_analysis.analyses.lifecycle import analyze_lifecycle

    result = analyze_lifecycle(
        _population(
            _row(1, year=("2021",), category=("A",)),
            _row(2, year=("2021",), category=("A",)),
            _row(3, year=("2022",), category=("A",)),
            _row(4, year=("2022",), category=("A",)),
        ),
        {"date_role": "year", "category_role": "category", "top_n": 20},
    )

    assert result["points"][0]["x"] == 2021


def test_lifecycle_cagr_zero_guards_and_stage_boundaries() -> None:
    from patent_analysis.analyses.lifecycle import lifecycle_cagr_percent, lifecycle_stage

    assert lifecycle_cagr_percent(1, 2) == pytest.approx(18.920711500272102)
    assert lifecycle_cagr_percent(0, 2) == 100.0
    assert lifecycle_cagr_percent(2, 0) == -100.0
    assert lifecycle_cagr_percent(0, 0) == 0.0
    assert lifecycle_stage(10.0) == "stable"
    assert lifecycle_stage(10.0001) == "growth"
    assert lifecycle_stage(0.0) == "stable"
    assert lifecycle_stage(-10.0) == "slowing"
    assert lifecycle_stage(-10.0001) == "decline"


def test_lifecycle_empty_result_has_null_window_and_explicit_counters() -> None:
    from patent_analysis.analyses.lifecycle import analyze_lifecycle

    result = analyze_lifecycle(
        _population(
            _row(1, year=("unknown",), category=("A",)),
            _row(2, year=("2024",), category=()),
        ),
        {"date_role": "year", "category_role": "category", "top_n": 20},
    )

    assert result["window"] is None
    assert result["points"] == []
    assert result["population"] == {
        "input_rows": 2,
        "visible_rows": 0,
        "invalid_year_rows": 1,
        "blank_category_rows": 1,
        "excluded_rows": 2,
    }


def test_lifecycle_required_roles_and_parameters_are_closed() -> None:
    from patent_analysis.analyses.lifecycle import analyze_lifecycle, required_roles

    parameters = {"date_role": "year", "category_role": "category", "top_n": 20}
    assert required_roles(parameters) == ("year", "category")

    with pytest.raises(ValueError, match="must differ"):
        analyze_lifecycle(
            _population(),
            {"date_role": "year", "category_role": "year", "top_n": 20},
        )
    with pytest.raises(ValueError, match="top_n"):
        analyze_lifecycle(
            _population(),
            {**parameters, "top_n": 21},
        )
    with pytest.raises(ValueError, match="unsupported"):
        analyze_lifecycle(
            _population(),
            {**parameters, "window_years": 10},
        )


def test_lifecycle_contribution_guard_fails_before_limit_plus_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import patent_analysis.analyses.lifecycle as lifecycle

    monkeypatch.setattr(lifecycle, "MAX_EXPANDED_CONTRIBUTIONS", 2)
    population = _population(
        _row(1, year=("2024",), category=("A", "B")),
        _row(2, year=("2024",), category=("C",)),
    )

    with pytest.raises(lifecycle.LifecycleBudgetError, match="contributions"):
        lifecycle.analyze_lifecycle(
            population,
            {"date_role": "year", "category_role": "category", "top_n": 20},
        )


def test_lifecycle_distinct_bucket_guard_fails_before_limit_plus_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import patent_analysis.analyses.lifecycle as lifecycle

    monkeypatch.setattr(lifecycle, "MAX_DISTINCT_BUCKETS", 1)
    population = _population(
        _row(1, year=("2024",), category=("A", "B")),
    )

    with pytest.raises(lifecycle.LifecycleBudgetError, match="distinct buckets"):
        lifecycle.analyze_lifecycle(
            population,
            {"date_role": "year", "category_role": "category", "top_n": 20},
        )
