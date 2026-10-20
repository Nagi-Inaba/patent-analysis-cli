"""Closed dispatch across the approved categorical chart-model family."""

from __future__ import annotations

from patent_analysis.chart_models.composition import (
    build_composition_chart_model,
    build_composition_render_spec,
)
from patent_analysis.chart_models.series import (
    build_series_chart_model,
    build_series_render_spec,
)

_SERIES_MARKS = frozenset({"series-line-svg.v1", "series-stacked-bar-svg.v1"})
_COMPOSITION_MARKS = frozenset({"composition-bar-svg.v1", "composition-pie-svg.v1"})


def build_categorical_chart_model(
    analysis_result: object,
    *,
    mark: str,
) -> tuple[dict[str, object], dict[str, object]]:
    """Dispatch one validated result to its exact mark-compatible model builder."""

    if mark in _SERIES_MARKS:
        return build_series_chart_model(analysis_result, mark=mark)
    if mark in _COMPOSITION_MARKS:
        return build_composition_chart_model(analysis_result, mark=mark)
    raise ValueError("unknown categorical render mark")


def build_categorical_render_spec(*, mark: str, palette: str | None = None) -> dict[str, object]:
    """Return the fixed RenderSpec for one exact categorical mark."""

    if mark in _SERIES_MARKS:
        return build_series_render_spec(mark=mark, palette=palette)
    if mark in _COMPOSITION_MARKS:
        return build_composition_render_spec(mark=mark, palette=palette)
    raise ValueError("unknown categorical render mark")
