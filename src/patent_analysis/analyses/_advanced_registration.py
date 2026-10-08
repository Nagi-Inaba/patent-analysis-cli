"""Closed registrations for the registered advanced analysis slices.

No dynamic imports or user-supplied functions. SVG registration is enabled only
after the explicit pinned build creates its activation record.
"""

from __future__ import annotations

from types import MappingProxyType

from patent_analysis.advanced_presentation import advanced_marks_for

from . import _advanced_common as c
from . import (
    citation,
    compara,
    cooccurrence,
    entry_exit,
    growth_quadrant,
    inventor_tracking,
    matrix_composition,
    network,
    new_entrants,
    shared_involvement,
    uniqueness,
)

MODULES = (
    growth_quadrant,
    entry_exit,
    citation,
    matrix_composition,
    new_entrants,
    compara,
    cooccurrence,
    network,
    uniqueness,
    shared_involvement,
    inventor_tracking,
)
MODULE_BY_ID = MappingProxyType({m.ANALYSIS_ID: m for m in MODULES})

# Never expose a future registration merely because it was added to MODULES.
# An empty compatible_render_marks tuple means analysis-only MCP access.
MCP_JSON_ANALYSIS_IDS = frozenset(
    {
        "growth-quadrant.v1",
        "entry-exit.v1",
        "citation.v1",
        "matrix-composition.v1",
        "new-entrants.v1",
        "compara.v1",
        "cooccurrence.v1",
        "collaboration-network.v1",
        "uniqueness.v1",
        "shared-involvement.v1",
        "inventor-tracking.v1",
    }
)
PUBLIC_SCHEMA_NAMES = frozenset(
    f"{m.ANALYSIS_ID[:-3]}-{kind}-v1.schema.json"
    for m in MODULES
    for kind in ("parameters", "result")
)
_SYMBOLS = (
    "frontend/src/charts/echartsOptions.ts::buildGrowthQuadrantChart",
    "frontend/src/charts/echartsOptions.ts::buildEntryExitChart",
    "frontend/src/charts/echartsOptions.ts::buildCitationChart",
    "frontend/src/charts/plugins/matrixComposition.ts::buildMatrixComposition",
    "frontend/src/charts/plugins/newEntrantsMatrix.ts::buildNewEntrantsMatrix",
    "frontend/src/charts/echartsOptions.ts::buildComparaChart",
    "frontend/src/charts/echartsOptions.ts::buildCooccurrenceChart",
    "frontend/src/charts/echartsOptions.ts::buildNetworkChart",
    "frontend/src/domain/uniqueness.ts::analyzeUniqueness",
    "frontend/src/domain/sharedInvolvement.ts::analyzeSharedInvolvement",
    "src/patent_analysis/analyses/_advanced_common.py::run_csv",
)
_DESCRIPTIONS = (
    "Long- and short-span half-period count changes.",
    "First and last observed years and recent activity.",
    "Top record-level citation counts, not applicant totals.",
    "Category membership composition of an explicit matrix cell.",
    "New-to-population applicants and classification membership shares.",
    "Explicit group A minus group B count matrix.",
    "Symmetric, zero-diagonal unordered cooccurrence counts.",
    "Bounded collaboration nodes and unordered links.",
    "Distinct exclusive items using full-population ownership.",
    "Shared items and once-per-record involvement counts.",
    "Annual co-invention clusters and observed applicant changes.",
)


def validate_parameters(analysis_id, parameters):
    module = MODULE_BY_ID.get(analysis_id)
    if module is not None:
        module.validate_parameters(parameters)


def definitions(definition_type, provenance_type, alias_profile):
    result = []
    for module, symbol, description in zip(MODULES, _SYMBOLS, _DESCRIPTIONS, strict=True):
        slug = module.ANALYSIS_ID[:-3]
        implementation = getattr(module, "analyze_" + module.__name__.rsplit(".", 1)[-1] + "_csv")
        result.append(
            definition_type(
                analysis_id=module.ANALYSIS_ID,
                algorithm_version="1.0.0",
                public_description=description,
                spec_schema=f"schemas/{slug}-parameters-v1.schema.json",
                result_schema=f"schemas/{slug}-result-v1.schema.json",
                required_roles=(),
                optional_roles=(),
                allowed_resolution_profiles=(alias_profile,),
                allowed_normalization_profiles=(),
                required_profile_families=(),
                result_variant=module.VARIANT,
                compatible_render_marks=advanced_marks_for(module.ANALYSIS_ID),
                implementation=implementation,
                fixture_set=(),
                source_provenance=(
                    provenance_type(
                        ref="patent-analysis-cli" if module is inventor_tracking else "workbench",
                        repository=("patent-analysis-cli" if module is inventor_tracking
                                    else "patent-analysis-workbench"),
                        commit=("1921cd26f7200f5471e8668ebeb1a586b9876cbf"
                                if module is inventor_tracking
                                else "1ef857105a005c932907e67b27ae2da7a86678e6"),
                        pipeline_symbols=(symbol,),
                    ),
                ),
                operation_budget=MappingProxyType(
                    {
                        "max_rows": c.MAX_ROWS,
                        "max_normalized_tokens": c.MAX_INPUT_TOKENS,
                        "max_values_per_role": c.MAX_VALUES_PER_ROLE,
                        "max_label_json_bytes": c.MAX_LABEL_BYTES,
                        "max_expanded_contributions": c.MAX_CONTRIBUTIONS,
                        "max_distinct_tracking_keys": c.MAX_BUCKETS,
                        "max_result_bytes": (
                            inventor_tracking.MAX_RESULT_BYTES
                            if module is inventor_tracking else c.MAX_RESULT_BYTES
                        ),
                        **({"max_inventors": inventor_tracking.MAX_INVENTORS,
                            "max_year_span": inventor_tracking.MAX_YEAR_SPAN}
                           if module is inventor_tracking else {}),
                    }
                ),
                incremental_budget_guard=c.guard_budget,
                preflight_estimator_if_superlinear=(
                    c.preflight_pair_size
                    if module in (cooccurrence, network, inventor_tracking)
                    else c.preflight_cartesian_size
                    if module in (new_entrants, compara, uniqueness, shared_involvement)
                    else None
                ),
                mcp_public=module.ANALYSIS_ID in MCP_JSON_ANALYSIS_IDS,
            )
        )
    return tuple(result)
