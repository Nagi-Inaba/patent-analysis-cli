from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

import pytest
from advanced_inventory import ANALYSIS_IDS


def _definition(analysis_id: str):
    from patent_analysis.analysis_registry import AnalysisDefinition, SourceProvenance

    return AnalysisDefinition(
        analysis_id=analysis_id,
        algorithm_version="1.0.0",
        public_description="test definition",
        spec_schema="schemas/test-spec.json",
        result_schema="schemas/test-result.json",
        required_roles=(),
        optional_roles=(),
        allowed_resolution_profiles=(),
        allowed_normalization_profiles=(),
        required_profile_families=(),
        result_variant="series",
        compatible_render_marks=(),
        implementation=lambda: {},
        fixture_set=(),
        source_provenance=(
            SourceProvenance(
                ref="current",
                repository="patent-analysis-cli",
                commit="0" * 40,
                pipeline_symbols=("test",),
            ),
        ),
        operation_budget={"rows": 1},
        incremental_budget_guard=lambda *_args: None,
        preflight_estimator_if_superlinear=None,
        mcp_public=False,
    )


def test_registry_rejects_duplicate_analysis_id() -> None:
    from patent_analysis.analysis_registry import RegistryError, build_registry

    with pytest.raises(RegistryError, match="duplicate analysis_id"):
        build_registry([_definition("timeline.v1"), _definition("timeline.v1")])


def test_closed_registry_exposes_only_implemented_analyses() -> None:
    from patent_analysis.analysis_registry import (
        RegistryError,
        get_analysis_definition,
        list_analysis_definitions,
    )

    definitions = list_analysis_definitions()
    assert tuple(definition.analysis_id for definition in definitions) == ANALYSIS_IDS
    assert get_analysis_definition("ranking.v1") is definitions[0]
    assert get_analysis_definition("matrix.v1") is definitions[1]
    assert get_analysis_definition("timeline.v1") is definitions[2]
    assert get_analysis_definition("composition.v1") is definitions[3]
    assert get_analysis_definition("growth.v1") is definitions[4]
    assert get_analysis_definition("concentration.v1") is definitions[5]
    assert get_analysis_definition("lifecycle.v1") is definitions[6]
    assert all(isinstance(definition.operation_budget, Mapping) for definition in definitions)
    with pytest.raises(RegistryError, match="unknown analysis_id"):
        get_analysis_definition("future-analysis.v1")


@pytest.mark.parametrize(
    "mutate",
    [
        lambda definition: replace(definition, public_description=""),
        lambda definition: replace(definition, public_description="x" * 513),
        lambda definition: replace(definition, required_roles=("role", "")),
        lambda definition: replace(
            definition,
            source_provenance=(definition.source_provenance[0], definition.source_provenance[0]),
        ),
        lambda definition: replace(
            definition,
            source_provenance=(
                definition.source_provenance[0].__class__(
                    ref="source",
                    repository="patent-analysis-cli",
                    commit="0" * 40,
                    pipeline_symbols="not-a-tuple",
                ),
            ),
        ),
        lambda definition: replace(definition, source_provenance=(object(),)),
    ],
)
def test_registry_rejects_malformed_definitions(mutate) -> None:
    from patent_analysis.analysis_registry import RegistryError, build_registry

    with pytest.raises(RegistryError, match="analysis definition is invalid"):
        build_registry([mutate(_definition("timeline.v1"))])


def test_ranking_registry_provenance_matches_the_approved_inventory() -> None:
    from patent_analysis.analysis_registry import get_analysis_definition

    definition = get_analysis_definition("ranking.v1")
    assert definition.mcp_public is True
    assert definition.source_provenance == (
        definition.source_provenance[0].__class__(
            ref="patent-analysis-cli",
            repository="patent-analysis-cli",
            commit="f1165f5eb7a5cb1ef550bc1cd9c8e55148c38384",
            pipeline_symbols=("src/patent_analysis/analysis.py::analyze_csv",),
        ),
    )


def test_matrix_registry_provenance_is_not_a_runtime_mode() -> None:
    from patent_analysis.analysis_registry import get_analysis_definition

    definition = get_analysis_definition("matrix.v1")
    assert definition.mcp_public is True
    assert definition.compatible_render_marks == (
        "matrix-bubble-svg.v1",
        "matrix-heatmap-svg.v1",
    )
    assert definition.source_provenance == (
        definition.source_provenance[0].__class__(
            ref="bubble",
            repository="bubble-matrix-map",
            commit="e32703d81bfcb6f89e912f3dfa56f21fc7430aad",
            pipeline_symbols=(
                "axis ranking",
                "Cartesian pair counting",
                "Other projection",
            ),
        ),
    )


def test_task6_registry_provenance_is_read_only_reference_metadata() -> None:
    from patent_analysis.analysis_registry import get_analysis_definition

    for analysis_id in ("timeline.v1", "composition.v1"):
        definition = get_analysis_definition(analysis_id)
        assert definition.mcp_public is True
        assert definition.source_provenance[0].repository == "patent-analysis-workbench"
        assert definition.source_provenance[0].commit == (
            "1ef857105a005c932907e67b27ae2da7a86678e6"
        )


def test_registry_accepts_the_approved_quadrant_result_variant() -> None:
    from patent_analysis.analysis_registry import build_registry

    definition = replace(_definition("quadrant.v1"), result_variant="quadrant")

    assert tuple(build_registry([definition])) == ("quadrant.v1",)
