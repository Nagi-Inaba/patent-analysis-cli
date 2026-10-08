from __future__ import annotations

import pytest

from patent_analysis.chart_models.series import build_series_chart_model


def _envelope(analysis_id: str, data: dict[str, object]) -> dict[str, object]:
    return {
        "analysis_id": analysis_id,
        "algorithm_version": "1.0.0",
        "result_variant": "series",
        "population": {"input_rows": 2, "analyzed_rows": 2, "excluded_rows": 0},
        "data": data,
        "warnings": [],
    }


GROWTH = _envelope(
    "growth.v1",
    {
        "schema_version": "1.0.0",
        "analysis_id": "growth.v1",
        "algorithm_version": "1.0.0",
        "measure": {"mode": "count", "role": None},
        "start_year": 2018,
        "end_year": 2022,
        "x": ["2018", "2022"],
        "series": [
            {
                "label": "A",
                "values": [1, 2],
                "row_counts": [1, 2],
                "is_other": False,
                "growth_rate": 1.0,
                "growth_state": "measured",
            }
        ],
        "population": {
            "input_rows": 2,
            "visible_rows": 2,
            "invalid_year_rows": 0,
            "outside_endpoint_rows": 0,
            "blank_series_rows": 0,
            "excluded_rows": 0,
        },
        "contributions": 3,
        "limits": {
            "max_top_n": 20,
            "max_expanded_contributions": 1000000,
            "max_distinct_buckets": 100000,
        },
    },
)

CONCENTRATION = _envelope(
    "concentration.v1",
    {
        "schema_version": "1.0.0",
        "analysis_id": "concentration.v1",
        "algorithm_version": "1.0.0",
        "measure": {"mode": "count", "role": None},
        "x": ["2020"],
        "series": [
            {
                "label": "HHI",
                "values": [0.5],
                "row_counts": [2],
                "contribution_counts": [2],
                "classifications": ["concentrated"],
                "is_other": False,
            }
        ],
        "population": {
            "input_rows": 2,
            "visible_rows": 2,
            "invalid_year_rows": 0,
            "blank_category_rows": 0,
            "excluded_rows": 0,
        },
        "contributions": 2,
        "limits": {
            "max_year_buckets": 400,
            "max_expanded_contributions": 1000000,
            "max_distinct_buckets": 100000,
        },
    },
)


def test_growth_projects_common_series_fields_and_rejects_stacked_bar() -> None:
    model, _ = build_series_chart_model(GROWTH, mark="series-line-svg.v1")
    assert model["title"] == "増減率"
    assert model["series"] == [
        {"label": "A", "values": [1, 2], "row_counts": [1, 2], "is_other": False}
    ]
    with pytest.raises(ValueError):
        build_series_chart_model(GROWTH, mark="series-stacked-bar-svg.v1")


def test_concentration_projects_common_series_fields_only() -> None:
    model, _ = build_series_chart_model(CONCENTRATION, mark="series-line-svg.v1")
    assert model["title"] == "HHI集中度推移"
    assert model["series"] == [
        {"label": "HHI", "values": [0.5], "row_counts": [2], "is_other": False}
    ]
