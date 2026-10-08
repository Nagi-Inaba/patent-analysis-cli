from __future__ import annotations

from advanced_inventory import ANALYSIS_IDS, MCP_IDS, expected_advanced_capabilities


def test_capabilities_exactly_project_the_implemented_registry() -> None:
    from patent_analysis.capabilities import describe_capabilities

    assert describe_capabilities() == {
        "capabilities_contract_version": "1.0.0",
        "analyses": [
            {
                "analysis_id": "ranking.v1",
                "algorithm_version": "1.0.0",
                "description": "Deterministic v1 ranking analysis for CSV datasets.",
                "required_roles": ["dimension"],
                "optional_roles": ["measure"],
                "resolution_profiles": [],
                "normalization_profiles": [],
                "result_variant": "ranking",
                "render_marks": ["ranking-svg.v1"],
                "limits": {
                    "max_dimension_tokens_per_cell": 1_000,
                    "max_expanded_contributions": 500_000,
                    "max_distinct_buckets": 100_000,
                },
                "mcp_public": True,
                "spec_schema": "schemas/analysis-spec.schema.json",
                "result_schema": "schemas/analysis-result.schema.json",
            },
            {
                "analysis_id": "matrix.v1",
                "algorithm_version": "1.0.0",
                "description": (
                    "Deterministic count-only matrix analysis over canonical normalized "
                    "patent records."
                ),
                "required_roles": [],
                "optional_roles": [],
                "resolution_profiles": ["column-alias.v2"],
                "normalization_profiles": [],
                "result_variant": "matrix",
                "render_marks": [
                    "matrix-bubble-svg.v1",
                    "matrix-heatmap-svg.v1",
                ],
                "limits": {
                    "max_visible_cells": 400,
                    "max_expanded_contributions": 2_000_000,
                },
                "mcp_public": True,
                "spec_schema": "schemas/matrix-parameters-v1.schema.json",
                "result_schema": "schemas/matrix-result-v1.schema.json",
            },
            {
                "analysis_id": "timeline.v1",
                "algorithm_version": "1.0.0",
                "description": (
                    "Deterministic yearly series analysis with closed measures and "
                    "top-N projection."
                ),
                "required_roles": [],
                "optional_roles": [],
                "resolution_profiles": ["column-alias.v2"],
                "normalization_profiles": [],
                "result_variant": "series",
                "render_marks": [
                    "series-line-svg.v1",
                    "series-stacked-bar-svg.v1",
                ],
                "limits": {
                    "max_top_n": 100,
                    "max_expanded_contributions": 1_000_000,
                },
                "mcp_public": True,
                "spec_schema": "schemas/timeline-parameters-v1.schema.json",
                "result_schema": "schemas/timeline-result-v1.schema.json",
            },
            {
                "analysis_id": "composition.v1",
                "algorithm_version": "1.0.0",
                "description": (
                    "Deterministic categorical composition analysis with closed "
                    "measures and shares."
                ),
                "required_roles": [],
                "optional_roles": [],
                "resolution_profiles": ["column-alias.v2"],
                "normalization_profiles": [],
                "result_variant": "composition",
                "render_marks": [
                    "composition-bar-svg.v1",
                    "composition-pie-svg.v1",
                ],
                "limits": {
                    "max_top_n": 100,
                    "max_expanded_contributions": 500_000,
                },
                "mcp_public": True,
                "spec_schema": "schemas/composition-parameters-v1.schema.json",
                "result_schema": "schemas/composition-result-v1.schema.json",
            },
            {
                "analysis_id": "growth.v1",
                "algorithm_version": "1.0.0",
                "description": (
                    "Deterministic count-based growth between two explicit endpoint years."
                ),
                "required_roles": [],
                "optional_roles": [],
                "resolution_profiles": ["column-alias.v2"],
                "normalization_profiles": [],
                "result_variant": "series",
                "render_marks": ["series-line-svg.v1"],
                "limits": {
                    "max_top_n": 20,
                    "max_label_json_bytes": 4096,
                    "max_expanded_contributions": 1_000_000,
                    "max_distinct_buckets": 100_000,
                },
                "mcp_public": True,
                "spec_schema": "schemas/growth-parameters-v1.schema.json",
                "result_schema": "schemas/growth-result-v1.schema.json",
            },
            {
                "analysis_id": "concentration.v1",
                "algorithm_version": "1.0.0",
                "description": (
                    "Deterministic yearly HHI concentration over all category contributions."
                ),
                "required_roles": [],
                "optional_roles": [],
                "resolution_profiles": ["column-alias.v2"],
                "normalization_profiles": [],
                "result_variant": "series",
                "render_marks": ["series-line-svg.v1"],
                "limits": {
                    "max_year_buckets": 400,
                    "max_expanded_contributions": 1_000_000,
                    "max_distinct_buckets": 100_000,
                },
                "mcp_public": True,
                "spec_schema": "schemas/concentration-parameters-v1.schema.json",
                "result_schema": "schemas/concentration-result-v1.schema.json",
            },
            {
                "analysis_id": "lifecycle.v1",
                "algorithm_version": "1.0.0",
                "description": (
                    "Deterministic peak-year and fixed five-year CAGR lifecycle analysis."
                ),
                "required_roles": [],
                "optional_roles": [],
                "resolution_profiles": ["column-alias.v2"],
                "normalization_profiles": [],
                "result_variant": "points",
                "render_marks": ["points-bubble-svg.v1"],
                "limits": {
                    "max_top_n": 20,
                    "max_label_json_bytes": 4096,
                    "max_output_points": 20,
                    "max_expanded_contributions": 1_000_000,
                    "max_distinct_buckets": 100_000,
                },
                "mcp_public": True,
                "spec_schema": "schemas/lifecycle-parameters-v1.schema.json",
                "result_schema": "schemas/lifecycle-result-v1.schema.json",
            },
            *expected_advanced_capabilities(),
        ],
    }


def test_capabilities_do_not_advertise_future_or_source_product_modes() -> None:
    from patent_analysis.capabilities import describe_capabilities

    analyses = describe_capabilities()["analyses"]
    analysis_ids = [item["analysis_id"] for item in analyses]

    assert tuple(analysis_ids) == ANALYSIS_IDS
    assert "future-analysis.v1" not in analysis_ids
    assert all("workbench" not in str(item).lower() for item in analyses)
    by_id = {item["analysis_id"]: item for item in analyses}
    assert all(
        by_id[analysis_id]["mcp_public"] is True
        for analysis_id in ("matrix.v1", "timeline.v1", "composition.v1")
    )
    assert all(
        by_id[analysis_id]["mcp_public"] is True
        for analysis_id in MCP_IDS
    )
