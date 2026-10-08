from __future__ import annotations

import json
from importlib.resources import files

import pytest

from patent_analysis.analysis_contracts import StrictDraft202012Validator

TIMELINE_RESULT = {
    "analysis_id": "timeline.v1",
    "algorithm_version": "1.0.0",
    "result_variant": "series",
    "population": {"input_rows": 3, "analyzed_rows": 3, "excluded_rows": 0},
    "data": {
        "schema_version": "1.0.0",
        "analysis_id": "timeline.v1",
        "algorithm_version": "1.0.0",
        "measure": {"mode": "count", "role": None},
        "x": ["2020", "2021"],
        "series": [
            {
                "label": "A社",
                "values": [1, 2],
                "row_counts": [1, 2],
                "is_other": False,
            }
        ],
        "population": {
            "input_rows": 3,
            "visible_rows": 3,
            "invalid_year_rows": 0,
            "outside_year_range_rows": 0,
            "blank_series_rows": 0,
            "excluded_rows": 0,
        },
        "contributions": 3,
        "limits": {"max_top_n": 100, "max_expanded_contributions": 1_000_000},
    },
    "warnings": [],
}

COMPOSITION_RESULT = {
    "analysis_id": "composition.v1",
    "algorithm_version": "1.0.0",
    "result_variant": "composition",
    "population": {"input_rows": 3, "analyzed_rows": 3, "excluded_rows": 0},
    "data": {
        "schema_version": "1.0.0",
        "analysis_id": "composition.v1",
        "algorithm_version": "1.0.0",
        "measure": {"mode": "sum", "role": "score"},
        "items": [
            {
                "label": "A社",
                "value": 20,
                "row_count": 2,
                "share": 2 / 3,
                "share_basis": "row_count",
                "is_other": False,
            },
            {
                "label": "B社",
                "value": -2,
                "row_count": 1,
                "share": 1 / 3,
                "share_basis": "row_count",
                "is_other": False,
            },
        ],
        "population": {
            "input_rows": 3,
            "visible_rows": 3,
            "blank_role_rows": 0,
            "excluded_rows": 0,
        },
        "contributions": 3,
        "limits": {"max_top_n": 100, "max_expanded_contributions": 500_000},
    },
    "warnings": [],
}


def _schema(name: str) -> dict[str, object]:
    value = json.loads(
        files("patent_analysis").joinpath("schemas", name).read_text(encoding="utf-8")
    )
    assert isinstance(value, dict)
    StrictDraft202012Validator.check_schema(value)
    return value


def _valid(schema: dict[str, object], value: object) -> bool:
    return next(StrictDraft202012Validator(schema).iter_errors(value), None) is None


def test_series_chart_models_share_one_categorical_profile() -> None:
    from patent_analysis.chart_models.series import (
        build_series_chart_model,
        build_series_render_spec,
    )

    line, _ = build_series_chart_model(TIMELINE_RESULT, mark="series-line-svg.v1")
    stacked, _ = build_series_chart_model(
        TIMELINE_RESULT,
        mark="series-stacked-bar-svg.v1",
    )

    assert line["chart_type"] == "series.line"
    assert stacked["chart_type"] == "series.stacked-bar"
    assert line["x"] == ["2020", "2021"]
    assert line["series"] == TIMELINE_RESULT["data"]["series"]

    line_spec = build_series_render_spec(mark="series-line-svg.v1", x_count=2, series_count=1)
    bar_spec = build_series_render_spec(
        mark="series-stacked-bar-svg.v1", x_count=2, series_count=1
    )
    assert line_spec["render_profile_id"] == "categorical-svg-ja-jp-node22-echarts6.v1"
    assert bar_spec["render_profile_id"] == line_spec["render_profile_id"]


def test_composition_chart_models_preserve_declared_share_contract() -> None:
    from patent_analysis.chart_models.composition import (
        build_composition_chart_model,
        build_composition_render_spec,
    )

    pie, _ = build_composition_chart_model(
        COMPOSITION_RESULT,
        mark="composition-pie-svg.v1",
    )
    bar, _ = build_composition_chart_model(
        COMPOSITION_RESULT,
        mark="composition-bar-svg.v1",
    )

    assert pie["chart_type"] == "composition.pie"
    assert bar["chart_type"] == "composition.bar"
    assert pie["items"] == COMPOSITION_RESULT["data"]["items"]
    assert pie["items"][0]["share_basis"] == "row_count"
    assert pie["items"][0]["share"] == pytest.approx(2 / 3)

    pie_spec = build_composition_render_spec(mark="composition-pie-svg.v1", item_count=2)
    bar_spec = build_composition_render_spec(mark="composition-bar-svg.v1", item_count=2)
    assert pie_spec["render_profile_id"] == "categorical-svg-ja-jp-node22-echarts6.v1"
    assert bar_spec["render_profile_id"] == pie_spec["render_profile_id"]


def test_categorical_chart_model_schema_closes_exact_mark_type_pairs() -> None:
    schema = _schema("categorical-chart-model-v1.schema.json")

    base = {
        "chart_model_contract_version": "1.0.0",
        "analysis_result_sha256": "a" * 64,
        "title": "年次推移",
        "measure": {"mode": "count", "role": None},
        "x": ["2020"],
        "series": [
            {"label": "A社", "values": [1], "row_counts": [1], "is_other": False}
        ],
        "population": {"input_rows": 1, "analyzed_rows": 1, "excluded_rows": 0},
        "warnings": [],
    }
    valid_line = {**base, "chart_type": "series.line", "mark": "series-line-svg.v1"}
    assert _valid(schema, valid_line)

    invalid_line = {
        **base,
        "chart_type": "series.line",
        "mark": "series-stacked-bar-svg.v1",
    }
    assert not _valid(schema, invalid_line)

    composition = {
        "chart_model_contract_version": "1.0.0",
        "chart_type": "composition.pie",
        "mark": "composition-pie-svg.v1",
        "analysis_result_sha256": "b" * 64,
        "title": "構成比",
        "measure": {"mode": "sum", "role": "score"},
        "items": COMPOSITION_RESULT["data"]["items"],
        "population": {"input_rows": 3, "analyzed_rows": 3, "excluded_rows": 0},
        "warnings": [],
    }
    assert _valid(schema, composition)
    composition["mark"] = "composition-bar-svg.v1"
    assert not _valid(schema, composition)


def test_categorical_render_spec_is_family_bound_and_closed() -> None:
    schema = _schema("categorical-render-spec-v1.schema.json")
    from patent_analysis.chart_models.series import build_series_render_spec

    spec = build_series_render_spec(mark="series-line-svg.v1", x_count=2, series_count=1)
    assert _valid(schema, spec)
    mutated = dict(spec)
    mutated["render_profile_id"] = "series-svg-ja-jp-node22-echarts6.v1"
    assert not _valid(schema, mutated)


def test_chart_model_builders_reject_cross_family_or_unknown_marks() -> None:
    from patent_analysis.chart_models.composition import build_composition_chart_model
    from patent_analysis.chart_models.series import build_series_chart_model

    with pytest.raises(ValueError):
        build_series_chart_model(TIMELINE_RESULT, mark="composition-bar-svg.v1")
    with pytest.raises(ValueError):
        build_composition_chart_model(COMPOSITION_RESULT, mark="series-line-svg.v1")
    with pytest.raises(ValueError):
        build_series_chart_model(TIMELINE_RESULT, mark="caller-echarts-option")
