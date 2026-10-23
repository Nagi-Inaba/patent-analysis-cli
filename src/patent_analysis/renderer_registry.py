"""Closed registry of implemented SVG renderer marks."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from patent_analysis.advanced_presentation import (
    ADVANCED_PRESENTATIONS,
    ADVANCED_RENDER_PROFILE_ID,
    advanced_marks_for,
)


@dataclass(frozen=True, slots=True)
class RendererDefinition:
    mark: str
    result_variant: str
    render_profile_id: str
    resource_family: str


_CATEGORICAL_PROFILE = "categorical-svg-ja-jp-node24-echarts6.v1"
_DEFINITIONS = (
    RendererDefinition(
        mark="ranking-svg.v1",
        result_variant="ranking",
        render_profile_id="ranking-svg-ja-jp-node24-echarts6.v1",
        resource_family="ranking",
    ),
    RendererDefinition(
        mark="matrix-bubble-svg.v1",
        result_variant="matrix",
        render_profile_id="matrix-svg-ja-jp-node24-echarts6.v1",
        resource_family="matrix",
    ),
    RendererDefinition(
        mark="matrix-heatmap-svg.v1",
        result_variant="matrix",
        render_profile_id="matrix-svg-ja-jp-node24-echarts6.v1",
        resource_family="matrix",
    ),
    RendererDefinition(
        mark="series-line-svg.v1",
        result_variant="series",
        render_profile_id=_CATEGORICAL_PROFILE,
        resource_family="categorical",
    ),
    RendererDefinition(
        mark="series-stacked-bar-svg.v1",
        result_variant="series",
        render_profile_id=_CATEGORICAL_PROFILE,
        resource_family="categorical",
    ),
    RendererDefinition(
        mark="composition-bar-svg.v1",
        result_variant="composition",
        render_profile_id=_CATEGORICAL_PROFILE,
        resource_family="categorical",
    ),
    RendererDefinition(
        mark="composition-pie-svg.v1",
        result_variant="composition",
        render_profile_id=_CATEGORICAL_PROFILE,
        resource_family="categorical",
    ),
    RendererDefinition(
        mark="points-bubble-svg.v1",
        result_variant="points",
        render_profile_id="points-svg-ja-jp-node24-echarts6.v1",
        resource_family="points",
    ),
)
_DEFINITIONS += tuple(
    RendererDefinition(
        mark=presentation.mark,
        result_variant=presentation.result_variant,
        render_profile_id=ADVANCED_RENDER_PROFILE_ID,
        resource_family="advanced",
    )
    for presentation in ADVANCED_PRESENTATIONS.values()
    if advanced_marks_for(presentation.analysis_id)
)
_REGISTRY = MappingProxyType({definition.mark: definition for definition in _DEFINITIONS})


def list_renderer_definitions() -> tuple[RendererDefinition, ...]:
    return _DEFINITIONS


def get_renderer_definition(mark: str) -> RendererDefinition:
    try:
        return _REGISTRY[mark]
    except (KeyError, TypeError):
        raise ValueError("unknown renderer mark") from None


__all__ = (
    "RendererDefinition",
    "get_renderer_definition",
    "list_renderer_definitions",
)
