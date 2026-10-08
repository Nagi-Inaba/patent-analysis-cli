from __future__ import annotations

import hashlib

import pytest

from patent_analysis._render_canonical import canonical_json_bytes

MATRIX_RESULT = {
    "analysis_id": "matrix.v1",
    "algorithm_version": "1.0.0",
    "result_variant": "matrix",
    "population": {
        "input_rows": 3,
        "analyzed_rows": 2,
        "excluded_rows": 1,
    },
    "data": {
        "schema_version": "1.0.0",
        "analysis_id": "matrix.v1",
        "algorithm_version": "1.0.0",
        "measure": "count",
        "x_axis": {
            "role": "applicant",
            "categories": [
                {"label": "A社", "count": 2, "is_other": False},
                {"label": "B社", "count": 1, "is_other": False},
            ],
        },
        "y_axis": {
            "role": "classification",
            "categories": [
                {"label": "G06F", "count": 2, "is_other": False},
                {"label": "H04L", "count": 1, "is_other": False},
            ],
        },
        "cells": [
            {
                "x_index": 0,
                "y_index": 0,
                "x_label": "A社",
                "y_label": "G06F",
                "value": 2,
                "row_count": 2,
            },
            {
                "x_index": 1,
                "y_index": 0,
                "x_label": "B社",
                "y_label": "G06F",
                "value": 1,
                "row_count": 1,
            },
            {
                "x_index": 0,
                "y_index": 1,
                "x_label": "A社",
                "y_label": "H04L",
                "value": 1,
                "row_count": 1,
            },
        ],
        "population": {
            "input_rows": 3,
            "visible_rows": 2,
            "blank_axis_rows": 1,
            "axis_other_rows": 0,
            "excluded_rows": 1,
        },
        "contributions": 4,
        "limits": {
            "max_visible_cells": 400,
            "max_expanded_contributions": 2_000_000,
        },
    },
    "warnings": [],
}


def test_matrix_bubble_chart_model_preserves_axis_and_cell_order() -> None:
    from patent_analysis.chart_models.matrix import build_matrix_chart_model

    model, receipt = build_matrix_chart_model(
        MATRIX_RESULT,
        mark="matrix-bubble-svg.v1",
    )

    assert model["chart_model_contract_version"] == "1.0.0"
    assert model["chart_type"] == "matrix.bubble"
    assert model["mark"] == "matrix-bubble-svg.v1"
    assert [item["id"] for item in model["x_axis"]["categories"]] == ["x:0", "x:1"]
    assert [item["id"] for item in model["y_axis"]["categories"]] == ["y:0", "y:1"]
    assert [
        (cell["x_index"], cell["y_index"], cell["value"])
        for cell in model["cells"]
    ] == [(0, 0, 2), (1, 0, 1), (0, 1, 1)]
    assert receipt["chart_model_sha256"] == hashlib.sha256(
        canonical_json_bytes(model)
    ).hexdigest()


def test_matrix_heatmap_chart_model_uses_the_same_neutral_data() -> None:
    from patent_analysis.chart_models.matrix import build_matrix_chart_model

    model, _receipt = build_matrix_chart_model(
        MATRIX_RESULT,
        mark="matrix-heatmap-svg.v1",
    )

    assert model["chart_type"] == "matrix.heatmap"
    assert model["mark"] == "matrix-heatmap-svg.v1"
    assert [cell["value"] for cell in model["cells"]] == [2, 1, 1]


def test_matrix_chart_model_rejects_unknown_or_caller_defined_marks() -> None:
    from patent_analysis.chart_models.matrix import build_matrix_chart_model

    with pytest.raises(ValueError):
        build_matrix_chart_model(MATRIX_RESULT, mark="caller-echarts-option")


def test_matrix_render_specs_are_closed_and_profile_bound() -> None:
    from patent_analysis.chart_models.matrix import build_matrix_render_spec

    bubble = build_matrix_render_spec(
        mark="matrix-bubble-svg.v1",
        x_count=2,
        y_count=2,
    )
    heatmap = build_matrix_render_spec(
        mark="matrix-heatmap-svg.v1",
        x_count=2,
        y_count=2,
    )

    assert bubble["renderer_kind"] == "matrix.bubble.svg"
    assert heatmap["renderer_kind"] == "matrix.heatmap.svg"
    assert bubble["render_profile_id"] == heatmap["render_profile_id"]
    assert bubble["render_profile_id"] == "matrix-svg-ja-jp-node22-echarts6.v1"
    assert set(bubble) == set(heatmap)

    with pytest.raises(TypeError):
        build_matrix_render_spec(  # type: ignore[call-arg]
            mark="matrix-bubble-svg.v1",
            x_count=2,
            y_count=2,
            echarts_options={"formatter": "caller code"},
        )
