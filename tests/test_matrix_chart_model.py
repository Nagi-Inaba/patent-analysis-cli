from __future__ import annotations

import copy
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


def _pie_result() -> dict:
    result = copy.deepcopy(MATRIX_RESULT)
    data = result["data"]
    data["pie"] = {
        "role": "year",
        "categories": [
            {"label": "2020", "count": 2, "is_other": False},
            {"label": "その他（上位外）", "count": 1, "is_other": True},
        ],
    }
    data["cells"][0]["slices"] = [
        {"label": "2020", "count": 1},
        {"label": "その他（上位外）", "count": 1},
    ]
    data["cells"][1]["slices"] = [{"label": "2020", "count": 1}]
    data["cells"][2]["slices"] = [{"label": "その他（上位外）", "count": 1}]
    return result


def test_matrix_chart_model_without_a_pie_has_no_pie_fields() -> None:
    from patent_analysis.chart_models.matrix import build_matrix_chart_model

    model, _receipt = build_matrix_chart_model(MATRIX_RESULT, mark="matrix-bubble-svg.v1")

    assert "pie" not in model
    assert all("slices" not in cell for cell in model["cells"])


@pytest.mark.parametrize("mark", ["matrix-bubble-svg.v1", "matrix-heatmap-svg.v1"])
def test_matrix_chart_model_carries_the_pie_by_category_index(mark: str) -> None:
    from patent_analysis.chart_models.matrix import build_matrix_chart_model

    model, receipt = build_matrix_chart_model(_pie_result(), mark=mark)

    assert model["pie"] == {
        "role": "year",
        "categories": [
            {"id": "p:0", "index": 0, "label": "2020", "count": 2, "is_other": False},
            {"id": "p:1", "index": 1, "label": "その他（上位外）", "count": 1, "is_other": True},
        ],
    }
    assert model["cells"][0]["slices"] == [
        {"index": 0, "label": "2020", "count": 1},
        {"index": 1, "label": "その他（上位外）", "count": 1},
    ]
    assert receipt["chart_model_sha256"] == hashlib.sha256(canonical_json_bytes(model)).hexdigest()


@pytest.mark.parametrize(
    "damage",
    [
        lambda data: data["cells"][0].pop("slices"),
        lambda data: data.pop("pie"),
        lambda data: data["cells"][0]["slices"][0].update(label="unknown"),
        lambda data: data["cells"][0]["slices"].append({"label": "2020", "count": 1}),
    ],
    ids=["missing-slices", "missing-pie", "unknown-label", "duplicate-label"],
)
def test_matrix_chart_model_rejects_inconsistent_pie_documents(damage) -> None:
    from patent_analysis.chart_models.matrix import build_matrix_chart_model

    result = _pie_result()
    damage(result["data"])

    with pytest.raises(ValueError):
        build_matrix_chart_model(result, mark="matrix-bubble-svg.v1")
