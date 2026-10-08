"""Compatibility facade for the native matrix chart-model package."""

from patent_analysis.chart_models.matrix import (
    MATRIX_BUBBLE_MARK,
    MATRIX_HEATMAP_MARK,
    MATRIX_RENDER_MARKS,
    MATRIX_RENDER_PROFILE_ID,
    build_matrix_chart_model,
    build_matrix_render_spec,
)

__all__ = (
    "MATRIX_BUBBLE_MARK",
    "MATRIX_HEATMAP_MARK",
    "MATRIX_RENDER_MARKS",
    "MATRIX_RENDER_PROFILE_ID",
    "build_matrix_chart_model",
    "build_matrix_render_spec",
)
