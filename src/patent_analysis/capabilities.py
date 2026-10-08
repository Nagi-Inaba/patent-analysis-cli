"""Stable public projection of implemented analysis capabilities."""

from __future__ import annotations

from typing import Any

from patent_analysis.analysis_registry import list_analysis_definitions

CAPABILITIES_CONTRACT_VERSION = "1.0.0"


def describe_capabilities() -> dict[str, Any]:
    """Return only definitions backed by the closed implementation registry."""

    analyses = []
    for definition in list_analysis_definitions():
        analyses.append(
            {
                "analysis_id": definition.analysis_id,
                "algorithm_version": definition.algorithm_version,
                "description": definition.public_description,
                "required_roles": list(definition.required_roles),
                "optional_roles": list(definition.optional_roles),
                "resolution_profiles": list(definition.allowed_resolution_profiles),
                "normalization_profiles": list(definition.allowed_normalization_profiles),
                "result_variant": definition.result_variant,
                "render_marks": list(definition.compatible_render_marks),
                "limits": dict(definition.operation_budget),
                "mcp_public": definition.mcp_public,
                "spec_schema": definition.spec_schema,
                "result_schema": definition.result_schema,
            }
        )
    return {
        "capabilities_contract_version": CAPABILITIES_CONTRACT_VERSION,
        "analyses": analyses,
    }
