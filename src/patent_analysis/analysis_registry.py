"""Closed registry for analysis implementations available to public adapters."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from patent_analysis.analyses._advanced_registration import definitions as _advanced_definitions
from patent_analysis.analyses.composition import (
    MAX_EXPANDED_CONTRIBUTIONS as MAX_COMPOSITION_EXPANDED_CONTRIBUTIONS,
)
from patent_analysis.analyses.composition import (
    MAX_TOP_N as MAX_COMPOSITION_TOP_N,
)
from patent_analysis.analyses.composition import analyze_composition_csv
from patent_analysis.analyses.concentration import (
    MAX_DISTINCT_BUCKETS as MAX_CONCENTRATION_DISTINCT_BUCKETS,
)
from patent_analysis.analyses.concentration import (
    MAX_EXPANDED_CONTRIBUTIONS as MAX_CONCENTRATION_EXPANDED_CONTRIBUTIONS,
)
from patent_analysis.analyses.concentration import MAX_YEAR_BUCKETS, analyze_concentration_csv
from patent_analysis.analyses.growth import (
    MAX_DISTINCT_BUCKETS as MAX_GROWTH_DISTINCT_BUCKETS,
)
from patent_analysis.analyses.growth import (
    MAX_EXPANDED_CONTRIBUTIONS as MAX_GROWTH_EXPANDED_CONTRIBUTIONS,
)
from patent_analysis.analyses.growth import MAX_LABEL_JSON_BYTES as MAX_GROWTH_LABEL_JSON_BYTES
from patent_analysis.analyses.growth import MAX_TOP_N as MAX_GROWTH_TOP_N
from patent_analysis.analyses.growth import analyze_growth_csv
from patent_analysis.analyses.lifecycle import (
    MAX_DISTINCT_BUCKETS as MAX_LIFECYCLE_DISTINCT_BUCKETS,
)
from patent_analysis.analyses.lifecycle import (
    MAX_EXPANDED_CONTRIBUTIONS as MAX_LIFECYCLE_EXPANDED_CONTRIBUTIONS,
)
from patent_analysis.analyses.lifecycle import (
    MAX_LABEL_JSON_BYTES as MAX_LIFECYCLE_LABEL_JSON_BYTES,
)
from patent_analysis.analyses.lifecycle import MAX_OUTPUT_POINTS, analyze_lifecycle_csv
from patent_analysis.analyses.lifecycle import MAX_TOP_N as MAX_LIFECYCLE_TOP_N
from patent_analysis.analyses.matrix import (
    MAX_EXPANDED_CONTRIBUTIONS as MAX_MATRIX_EXPANDED_CONTRIBUTIONS,
)
from patent_analysis.analyses.matrix import MAX_VISIBLE_CELLS, analyze_matrix_csv
from patent_analysis.analyses.timeline import (
    MAX_EXPANDED_CONTRIBUTIONS as MAX_TIMELINE_EXPANDED_CONTRIBUTIONS,
)
from patent_analysis.analyses.timeline import MAX_TOP_N as MAX_TIMELINE_TOP_N
from patent_analysis.analyses.timeline import analyze_timeline_csv
from patent_analysis.analysis import (
    MAX_DIMENSION_TOKENS_PER_CELL,
    MAX_DISTINCT_BUCKETS,
    MAX_EXPANDED_CONTRIBUTIONS,
    analyze_csv,
)
from patent_analysis.column_resolution import COLUMN_ALIAS_PROFILE


class RegistryError(ValueError):
    """Raised when an analysis registry is not closed and internally consistent."""


@dataclass(frozen=True, slots=True)
class SourceProvenance:
    ref: str
    repository: str
    commit: str
    pipeline_symbols: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AnalysisDefinition:
    analysis_id: str
    algorithm_version: str
    public_description: str
    spec_schema: str
    result_schema: str
    required_roles: tuple[str, ...]
    optional_roles: tuple[str, ...]
    allowed_resolution_profiles: tuple[str, ...]
    allowed_normalization_profiles: tuple[str, ...]
    required_profile_families: tuple[str, ...]
    result_variant: str
    compatible_render_marks: tuple[str, ...]
    implementation: Callable[..., Mapping[str, object]]
    fixture_set: tuple[str, ...]
    source_provenance: tuple[SourceProvenance, ...]
    operation_budget: Mapping[str, int]
    incremental_budget_guard: Callable[..., None]
    preflight_estimator_if_superlinear: Callable[..., int] | None
    mcp_public: bool


def _guard_ranking_budget(*_args: object, **_kwargs: object) -> None:
    """The v1 implementation owns its established hard limits internally."""


def _guard_matrix_budget(*_args: object, **_kwargs: object) -> None:
    """The matrix implementation applies its pair and visible-cell limits incrementally."""


def _guard_timeline_budget(*_args: object, **_kwargs: object) -> None:
    """The timeline implementation applies its contribution limit incrementally."""


def _guard_composition_budget(*_args: object, **_kwargs: object) -> None:
    """The composition implementation applies its contribution limit incrementally."""


def _guard_growth_budget(*_args: object, **_kwargs: object) -> None:
    """Growth applies contribution and bucket limits incrementally."""


def _guard_concentration_budget(*_args: object, **_kwargs: object) -> None:
    """Concentration applies year, contribution, and bucket limits incrementally."""


def _guard_lifecycle_budget(*_args: object, **_kwargs: object) -> None:
    """Lifecycle applies contribution and bucket limits incrementally."""


_RANKING_V1 = AnalysisDefinition(
    analysis_id="ranking.v1",
    algorithm_version="1.0.0",
    public_description="Deterministic v1 ranking analysis for CSV datasets.",
    spec_schema="schemas/analysis-spec.schema.json",
    result_schema="schemas/analysis-result.schema.json",
    required_roles=("dimension",),
    optional_roles=("measure",),
    allowed_resolution_profiles=(),
    allowed_normalization_profiles=(),
    required_profile_families=(),
    result_variant="ranking",
    compatible_render_marks=("ranking-svg.v1",),
    implementation=analyze_csv,
    fixture_set=("schemas/ranking-cases.json",),
    source_provenance=(
        SourceProvenance(
            ref="patent-analysis-cli",
            repository="patent-analysis-cli",
            commit="f1165f5eb7a5cb1ef550bc1cd9c8e55148c38384",
            pipeline_symbols=("src/patent_analysis/analysis.py::analyze_csv",),
        ),
    ),
    operation_budget=MappingProxyType(
        {
            "max_dimension_tokens_per_cell": MAX_DIMENSION_TOKENS_PER_CELL,
            "max_expanded_contributions": MAX_EXPANDED_CONTRIBUTIONS,
            "max_distinct_buckets": MAX_DISTINCT_BUCKETS,
        }
    ),
    incremental_budget_guard=_guard_ranking_budget,
    preflight_estimator_if_superlinear=None,
    mcp_public=True,
)

_MATRIX_V1 = AnalysisDefinition(
    analysis_id="matrix.v1",
    algorithm_version="1.0.0",
    public_description=(
        "Deterministic count-only matrix analysis over canonical normalized patent records."
    ),
    spec_schema="schemas/matrix-parameters-v1.schema.json",
    result_schema="schemas/matrix-result-v1.schema.json",
    required_roles=(),
    optional_roles=(),
    allowed_resolution_profiles=(COLUMN_ALIAS_PROFILE,),
    allowed_normalization_profiles=(),
    required_profile_families=(),
    result_variant="matrix",
    compatible_render_marks=("matrix-bubble-svg.v1", "matrix-heatmap-svg.v1"),
    implementation=analyze_matrix_csv,
    fixture_set=("schemas/matrix-cases.json",),
    source_provenance=(
        SourceProvenance(
            ref="bubble",
            repository="bubble-matrix-map",
            commit="e32703d81bfcb6f89e912f3dfa56f21fc7430aad",
            pipeline_symbols=("axis ranking", "Cartesian pair counting", "Other projection"),
        ),
    ),
    operation_budget=MappingProxyType(
        {
            "max_visible_cells": MAX_VISIBLE_CELLS,
            "max_expanded_contributions": MAX_MATRIX_EXPANDED_CONTRIBUTIONS,
        }
    ),
    incremental_budget_guard=_guard_matrix_budget,
    preflight_estimator_if_superlinear=None,
    mcp_public=True,
)

_TIMELINE_V1 = AnalysisDefinition(
    analysis_id="timeline.v1",
    algorithm_version="1.0.0",
    public_description=(
        "Deterministic yearly series analysis with closed measures and top-N projection."
    ),
    spec_schema="schemas/timeline-parameters-v1.schema.json",
    result_schema="schemas/timeline-result-v1.schema.json",
    required_roles=(),
    optional_roles=(),
    allowed_resolution_profiles=(COLUMN_ALIAS_PROFILE,),
    allowed_normalization_profiles=(),
    required_profile_families=(),
    result_variant="series",
    compatible_render_marks=("series-line-svg.v1", "series-stacked-bar-svg.v1"),
    implementation=analyze_timeline_csv,
    fixture_set=(),
    source_provenance=(
        SourceProvenance(
            ref="workbench",
            repository="patent-analysis-workbench",
            commit="1ef857105a005c932907e67b27ae2da7a86678e6",
            pipeline_symbols=(
                "frontend/src/domain/aggregation.ts::getYear",
                "frontend/src/domain/aggregation.ts::measureValue",
                "frontend/src/domain/aggregation.ts::aggregateBy",
            ),
        ),
    ),
    operation_budget=MappingProxyType(
        {
            "max_top_n": MAX_TIMELINE_TOP_N,
            "max_expanded_contributions": MAX_TIMELINE_EXPANDED_CONTRIBUTIONS,
        }
    ),
    incremental_budget_guard=_guard_timeline_budget,
    preflight_estimator_if_superlinear=None,
    mcp_public=True,
)

_COMPOSITION_V1 = AnalysisDefinition(
    analysis_id="composition.v1",
    algorithm_version="1.0.0",
    public_description=(
        "Deterministic categorical composition analysis with closed measures and shares."
    ),
    spec_schema="schemas/composition-parameters-v1.schema.json",
    result_schema="schemas/composition-result-v1.schema.json",
    required_roles=(),
    optional_roles=(),
    allowed_resolution_profiles=(COLUMN_ALIAS_PROFILE,),
    allowed_normalization_profiles=(),
    required_profile_families=(),
    result_variant="composition",
    compatible_render_marks=("composition-bar-svg.v1", "composition-pie-svg.v1"),
    implementation=analyze_composition_csv,
    fixture_set=(),
    source_provenance=(
        SourceProvenance(
            ref="workbench",
            repository="patent-analysis-workbench",
            commit="1ef857105a005c932907e67b27ae2da7a86678e6",
            pipeline_symbols=(
                "frontend/src/domain/aggregation.ts::measureValue",
                "frontend/src/domain/aggregation.ts::aggregateBy",
            ),
        ),
    ),
    operation_budget=MappingProxyType(
        {
            "max_top_n": MAX_COMPOSITION_TOP_N,
            "max_expanded_contributions": MAX_COMPOSITION_EXPANDED_CONTRIBUTIONS,
        }
    ),
    incremental_budget_guard=_guard_composition_budget,
    preflight_estimator_if_superlinear=None,
    mcp_public=True,
)


_GROWTH_V1 = AnalysisDefinition(
    analysis_id="growth.v1",
    algorithm_version="1.0.0",
    public_description="Deterministic count-based growth between two explicit endpoint years.",
    spec_schema="schemas/growth-parameters-v1.schema.json",
    result_schema="schemas/growth-result-v1.schema.json",
    required_roles=(),
    optional_roles=(),
    allowed_resolution_profiles=(COLUMN_ALIAS_PROFILE,),
    allowed_normalization_profiles=(),
    required_profile_families=(),
    result_variant="series",
    compatible_render_marks=("series-line-svg.v1",),
    implementation=analyze_growth_csv,
    fixture_set=(),
    source_provenance=(
        SourceProvenance(
            ref="workbench",
            repository="patent-analysis-workbench",
            commit="1ef857105a005c932907e67b27ae2da7a86678e6",
            pipeline_symbols=(
                "frontend/src/charts/echartsOptions.ts::buildGrowthChart",
                "frontend/src/charts/echartsOptions.test.ts::growth cases",
            ),
        ),
    ),
    operation_budget=MappingProxyType(
        {
            "max_top_n": MAX_GROWTH_TOP_N,
            "max_label_json_bytes": MAX_GROWTH_LABEL_JSON_BYTES,
            "max_expanded_contributions": MAX_GROWTH_EXPANDED_CONTRIBUTIONS,
            "max_distinct_buckets": MAX_GROWTH_DISTINCT_BUCKETS,
        }
    ),
    incremental_budget_guard=_guard_growth_budget,
    preflight_estimator_if_superlinear=None,
    mcp_public=True,
)

_CONCENTRATION_V1 = AnalysisDefinition(
    analysis_id="concentration.v1",
    algorithm_version="1.0.0",
    public_description="Deterministic yearly HHI concentration over all category contributions.",
    spec_schema="schemas/concentration-parameters-v1.schema.json",
    result_schema="schemas/concentration-result-v1.schema.json",
    required_roles=(),
    optional_roles=(),
    allowed_resolution_profiles=(COLUMN_ALIAS_PROFILE,),
    allowed_normalization_profiles=(),
    required_profile_families=(),
    result_variant="series",
    compatible_render_marks=("series-line-svg.v1",),
    implementation=analyze_concentration_csv,
    fixture_set=(),
    source_provenance=(
        SourceProvenance(
            ref="workbench",
            repository="patent-analysis-workbench",
            commit="1ef857105a005c932907e67b27ae2da7a86678e6",
            pipeline_symbols=(
                "frontend/src/charts/echartsOptions.ts::buildConcentrationChart",
                "frontend/src/charts/echartsOptions.test.ts::concentration cases",
            ),
        ),
    ),
    operation_budget=MappingProxyType(
        {
            "max_year_buckets": MAX_YEAR_BUCKETS,
            "max_expanded_contributions": MAX_CONCENTRATION_EXPANDED_CONTRIBUTIONS,
            "max_distinct_buckets": MAX_CONCENTRATION_DISTINCT_BUCKETS,
        }
    ),
    incremental_budget_guard=_guard_concentration_budget,
    preflight_estimator_if_superlinear=None,
    mcp_public=True,
)

_LIFECYCLE_V1 = AnalysisDefinition(
    analysis_id="lifecycle.v1",
    algorithm_version="1.0.0",
    public_description="Deterministic peak-year and fixed five-year CAGR lifecycle analysis.",
    spec_schema="schemas/lifecycle-parameters-v1.schema.json",
    result_schema="schemas/lifecycle-result-v1.schema.json",
    required_roles=(),
    optional_roles=(),
    allowed_resolution_profiles=(COLUMN_ALIAS_PROFILE,),
    allowed_normalization_profiles=(),
    required_profile_families=(),
    result_variant="points",
    compatible_render_marks=("points-bubble-svg.v1",),
    implementation=analyze_lifecycle_csv,
    fixture_set=(),
    source_provenance=(
        SourceProvenance(
            ref="workbench",
            repository="patent-analysis-workbench",
            commit="1ef857105a005c932907e67b27ae2da7a86678e6",
            pipeline_symbols=(
                "frontend/src/charts/echartsOptions.ts::buildLifecycleChart",
                "frontend/src/charts/echartsOptions.test.ts::lifecycle cases",
            ),
        ),
    ),
    operation_budget=MappingProxyType(
        {
            "max_top_n": MAX_LIFECYCLE_TOP_N,
            "max_label_json_bytes": MAX_LIFECYCLE_LABEL_JSON_BYTES,
            "max_output_points": MAX_OUTPUT_POINTS,
            "max_expanded_contributions": MAX_LIFECYCLE_EXPANDED_CONTRIBUTIONS,
            "max_distinct_buckets": MAX_LIFECYCLE_DISTINCT_BUCKETS,
        }
    ),
    incremental_budget_guard=_guard_lifecycle_budget,
    preflight_estimator_if_superlinear=None,
    mcp_public=True,
)


_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_RESULT_VARIANTS = frozenset(
    {
        "ranking",
        "series",
        "composition",
        "matrix",
        "points",
        "quadrant",
        "network",
        "grouped-metrics",
    }
)


def _is_relative_schema_path(value: object) -> bool:
    return (
        isinstance(value, str)
        and value.startswith("schemas/")
        and ".." not in value
        and ":" not in value
    )


def _is_nonempty_string_tuple(value: object) -> bool:
    return isinstance(value, tuple) and all(isinstance(item, str) and item for item in value)


def _validate_definition(definition: AnalysisDefinition) -> None:
    if not isinstance(definition.analysis_id, str) or not definition.analysis_id:
        raise RegistryError("analysis definition is invalid")
    if not isinstance(definition.algorithm_version, str) or not definition.algorithm_version:
        raise RegistryError("analysis definition is invalid")
    if (
        not isinstance(definition.public_description, str)
        or not definition.public_description.strip()
        or len(definition.public_description.encode("utf-8")) > 512
    ):
        raise RegistryError("analysis definition is invalid")
    if not _is_relative_schema_path(definition.spec_schema) or not _is_relative_schema_path(
        definition.result_schema
    ):
        raise RegistryError("analysis definition is invalid")
    if definition.result_variant not in _RESULT_VARIANTS:
        raise RegistryError("analysis definition is invalid")
    if not all(
        _is_nonempty_string_tuple(value)
        for value in (
            definition.required_roles,
            definition.optional_roles,
            definition.allowed_resolution_profiles,
            definition.allowed_normalization_profiles,
            definition.required_profile_families,
            definition.compatible_render_marks,
            definition.fixture_set,
        )
    ):
        raise RegistryError("analysis definition is invalid")
    if not all(_is_relative_schema_path(path) for path in definition.fixture_set):
        raise RegistryError("analysis definition is invalid")
    if not callable(definition.implementation) or not callable(definition.incremental_budget_guard):
        raise RegistryError("analysis definition is invalid")
    if definition.preflight_estimator_if_superlinear is not None and not callable(
        definition.preflight_estimator_if_superlinear
    ):
        raise RegistryError("analysis definition is invalid")
    if not isinstance(definition.mcp_public, bool):
        raise RegistryError("analysis definition is invalid")
    if not definition.operation_budget or any(
        not isinstance(key, str) or not key or type(value) is not int or value <= 0
        for key, value in definition.operation_budget.items()
    ):
        raise RegistryError("analysis definition is invalid")
    if not isinstance(definition.source_provenance, tuple) or not definition.source_provenance:
        raise RegistryError("analysis definition is invalid")
    source_refs: set[str] = set()
    for source in definition.source_provenance:
        if not isinstance(source, SourceProvenance):
            raise RegistryError("analysis definition is invalid")
        if (
            not isinstance(source.ref, str)
            or not source.ref
            or not isinstance(source.repository, str)
            or not source.repository
            or not isinstance(source.commit, str)
            or not _COMMIT.fullmatch(source.commit)
            or not isinstance(source.pipeline_symbols, tuple)
            or not source.pipeline_symbols
            or not all(isinstance(symbol, str) and symbol for symbol in source.pipeline_symbols)
        ):
            raise RegistryError("analysis definition is invalid")
        if source.ref in source_refs:
            raise RegistryError("analysis definition is invalid")
        source_refs.add(source.ref)


def build_registry(
    definitions: tuple[AnalysisDefinition, ...] | list[AnalysisDefinition],
) -> Mapping[str, AnalysisDefinition]:
    """Build an immutable registry, rejecting duplicate or malformed definitions."""

    registry: dict[str, AnalysisDefinition] = {}
    for definition in definitions:
        if not isinstance(definition, AnalysisDefinition):
            raise RegistryError("analysis definition is invalid")
        _validate_definition(definition)
        if definition.analysis_id in registry:
            raise RegistryError("duplicate analysis_id")
        registry[definition.analysis_id] = definition
    return MappingProxyType(registry)


_REGISTRY = build_registry(
    (
        _RANKING_V1,
        _MATRIX_V1,
        _TIMELINE_V1,
        _COMPOSITION_V1,
        _GROWTH_V1,
        _CONCENTRATION_V1,
        _LIFECYCLE_V1,
        *_advanced_definitions(AnalysisDefinition, SourceProvenance, COLUMN_ALIAS_PROFILE),
    )
)


def get_analysis_definition(analysis_id: str) -> AnalysisDefinition:
    """Return one registered definition without allowing fallback dispatch."""

    try:
        return _REGISTRY[analysis_id]
    except (KeyError, TypeError):
        raise RegistryError("unknown analysis_id") from None


def list_analysis_definitions() -> tuple[AnalysisDefinition, ...]:
    """Return the deterministic registry order used by public adapters."""

    return tuple(_REGISTRY.values())
