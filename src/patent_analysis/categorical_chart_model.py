"""Closed facade for categorical chart-model and render-spec builders."""

from __future__ import annotations

from collections.abc import Mapping

from patent_analysis.chart_models.composition import (
    build_composition_chart_model,
    build_composition_render_spec,
)
from patent_analysis.chart_models.series import (
    build_series_chart_model,
    build_series_render_spec,
)

SERIES_MARKS = frozenset({"series-line-svg.v1", "series-stacked-bar-svg.v1"})
COMPOSITION_MARKS = frozenset({"composition-bar-svg.v1", "composition-pie-svg.v1"})
CATEGORICAL_MARKS = SERIES_MARKS | COMPOSITION_MARKS


def build_categorical_chart_model(
    analysis_document: bytes | Mapping[str, object],
    *,
    mark: str,
) -> tuple[dict[str, object], dict[str, object]]:
    """Build one mark-closed model from a validated neutral result."""

    if mark in SERIES_MARKS:
        return build_series_chart_model(analysis_document, mark=mark)
    if mark in COMPOSITION_MARKS:
        return build_composition_chart_model(analysis_document, mark=mark)
    raise ValueError("unknown categorical renderer mark")


def build_categorical_render_spec(
    *,
    mark: str,
    chart_model: Mapping[str, object] | None = None,
    palette: str | None = None,
) -> dict[str, object]:
    """Build the fixed family render spec without caller chart configuration."""

    if mark in SERIES_MARKS:
        x_count = None
        series_count = None
        if chart_model is not None:
            x = chart_model.get("x")
            series = chart_model.get("series")
            x_count = len(x) if isinstance(x, list) else None
            series_count = len(series) if isinstance(series, list) else None
        return build_series_render_spec(
            mark=mark,
            x_count=x_count,
            series_count=series_count,
            palette=palette,
        )
    if mark in COMPOSITION_MARKS:
        item_count = None
        if chart_model is not None:
            items = chart_model.get("items")
            item_count = len(items) if isinstance(items, list) else None
        return build_composition_render_spec(mark=mark, item_count=item_count, palette=palette)
    raise ValueError("unknown categorical renderer mark")


__all__ = (
    "CATEGORICAL_MARKS",
    "COMPOSITION_MARKS",
    "SERIES_MARKS",
    "build_categorical_chart_model",
    "build_categorical_render_spec",
)
