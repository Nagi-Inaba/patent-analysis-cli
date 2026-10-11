"""Explicit native inventor catalog; never dynamically import a user algorithm."""

from __future__ import annotations

from types import MappingProxyType

from patent_analysis.advanced_presentation import advanced_marks_for

from . import _inventor_common as c
from . import (
    inventor_activity,
    inventor_cluster_flow,
    inventor_ego_network,
    inventor_impact,
    inventor_mobility,
    inventor_mobility_evidence,
    inventor_mobility_flow,
    inventor_network,
    inventor_similarity,
    inventor_technology,
)

MODULES = (
    inventor_network,
    inventor_ego_network,
    inventor_technology,
    inventor_activity,
    inventor_cluster_flow,
    inventor_similarity,
    inventor_impact,
    inventor_mobility,
    inventor_mobility_flow,
    inventor_mobility_evidence,
)
MODULE_BY_ID = MappingProxyType({module.ANALYSIS_ID: module for module in MODULES})
MCP_JSON_ANALYSIS_IDS = frozenset(
    {
        "inventor-network.v1",
        "inventor-ego-network.v1",
        "inventor-technology.v1",
        "inventor-activity.v1",
        "inventor-cluster-flow.v1",
        "inventor-similarity.v1",
        "inventor-impact.v1",
        "inventor-mobility.v1",
        "inventor-mobility-flow.v1",
        "inventor-mobility-evidence.v1",
    }
)
PUBLIC_SCHEMA_NAMES = frozenset(
    f"{module.ANALYSIS_ID[:-3]}-{kind}-v1.schema.json"
    for module in MODULES
    for kind in ("parameters", "result")
)


DESCRIPTIONS = {
    "inventor-network.v1": "Full observed co-invention graph; not employment evidence.",
    "inventor-ego-network.v1": "Literal-focus ego view retaining full-graph metrics.",
    "inventor-technology.v1": "Witnessed technology profiles with full-population references.",
    "inventor-activity.v1": "Annual patent activity; absence is not inactivity or retirement.",
    "inventor-cluster-flow.v1": "Adjacent-calendar observed community membership flows.",
    "inventor-similarity.v1": "Neutral full-pool technology features and cosine similarities.",
    "inventor-impact.v1": "Explicit-snapshot patent citation metrics; not personal ability.",
    "inventor-mobility.v1": "Patent-applicant episodes and separately reviewed move candidates.",
    "inventor-mobility-flow.v1": "Conservative directed legal or historical-group candidate flows.",
    "inventor-mobility-evidence.v1": "Stable candidate evidence and review audit tables; no SVG.",
}


def budgets(analysis_id):
    result = {
        "max_rows": 5000,
        "max_units": 5000,
        "max_people": 200,
        "max_pair_expansions": 50000,
        "max_columns": 128,
        "max_sidecar_bytes": 1048576,
        "max_sidecar_rows": 5000,
        "max_statistics_bytes": c.MAX_STATISTICS_BYTES,
        "max_result_bytes": c.MAX_RESULT_BYTES,
    }
    if analysis_id in {
        "inventor-network.v1",
        "inventor-ego-network.v1",
        "inventor-activity.v1",
        "inventor-cluster-flow.v1",
    }:
        result["max_edges"] = 5000
    if analysis_id not in {
        "inventor-network.v1",
        "inventor-ego-network.v1",
        "inventor-technology.v1",
        "inventor-similarity.v1",
    }:
        result["max_year_span"] = 30
    if analysis_id.startswith("inventor-mobility"):
        result.update(max_association_rows=5000, max_candidate_rows=5000, max_comparisons=200000)
    if (
        not analysis_id.startswith("inventor-mobility")
        or analysis_id == "inventor-mobility-flow.v1"
    ):
        result.update(precision_decimal_places=12, max_fraction_bits=128)
    if analysis_id == "inventor-mobility-flow.v1":
        result["max_flow_contributions"] = 5000
    return result


def definitions(definition_type, provenance_type):
    result = []
    for module in MODULES:
        slug = module.ANALYSIS_ID[:-3]
        implementation = getattr(module, "analyze_" + module.__name__.rsplit(".", 1)[-1] + "_csv")
        result.append(
            definition_type(
                analysis_id=module.ANALYSIS_ID,
                algorithm_version="1.0.0",
                public_description=DESCRIPTIONS[module.ANALYSIS_ID],
                spec_schema=f"schemas/{slug}-parameters-v1.schema.json",
                result_schema=f"schemas/{slug}-result-v1.schema.json",
                required_roles=(),
                optional_roles=(),
                allowed_resolution_profiles=(),
                allowed_normalization_profiles=(),
                required_profile_families=(),
                result_variant=module.VARIANT,
                compatible_render_marks=(
                    ()
                    if module is inventor_mobility_evidence
                    else advanced_marks_for(module.ANALYSIS_ID)
                ),
                implementation=implementation,
                fixture_set=(),
                source_provenance=(
                    provenance_type(
                        # This is the integration CONTRACT base, not a commit containing
                        # the uncommitted native inventor kernels. Keep that distinction.
                        ref="patent-analysis-cli-contract-base",
                        repository="patent-analysis-cli",
                        commit="48315708be6d91ff022c4daef4861dfb26b5858e",
                        pipeline_symbols=(
                            "src/patent_analysis/analysis_registry.py::AnalysisDefinition",
                            "src/patent_analysis/analysis_runner.py::run_analysis",
                        ),
                    ),
                ),
                operation_budget=MappingProxyType(budgets(module.ANALYSIS_ID)),
                incremental_budget_guard=c.guard_budget,
                preflight_estimator_if_superlinear=c.preflight_pair_size,
                mcp_public=module.ANALYSIS_ID in MCP_JSON_ANALYSIS_IDS,
            )
        )
    return tuple(result)
