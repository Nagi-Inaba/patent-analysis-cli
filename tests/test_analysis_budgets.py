from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from patent_analysis.analysis_budgets import (
    MAX_ANALYSIS_SPEC_BYTES,
    MAX_ANALYSIS_SPEC_DEPTH,
    MAX_ANALYSIS_SPEC_NODES,
    MAX_ANALYSIS_SPEC_STRING_CODE_POINTS,
    MAX_CANONICAL_NEUTRAL_RESULT_BYTES,
    MAX_COLUMNS,
    MAX_CSV_BYTES,
    MAX_DECODED_CELL_CODE_POINTS,
    MAX_DISTINCT_LABELS,
    MAX_EXPANDED_MEMBERSHIPS,
    MAX_MCP_AGGREGATE_ITEMS,
    MAX_MCP_SERIALIZED_RESPONSE_BYTES,
    MAX_NETWORK_DISPLAY_NODES,
    MAX_NETWORK_EDGES,
    MAX_NEUTRAL_CELLS,
    MAX_NEUTRAL_RESULT_ROWS,
    MAX_NORMALIZATION_MAPPING_ARTIFACT_BYTES,
    MAX_OUTPUT_GROUPS,
    MAX_OUTPUT_POINTS,
    MAX_PAIR_OPERATIONS,
    MAX_PARSED_CELLS,
    MAX_RENDER_AXIS_LABELS,
    MAX_RENDER_VISIBLE_CELLS,
    MAX_ROWS,
    MAX_YEAR_BUCKETS,
    OperationBudget,
)


def test_shared_v2_limits_match_the_approved_contract() -> None:
    assert (
        MAX_CSV_BYTES,
        MAX_ROWS,
        MAX_COLUMNS,
        MAX_PARSED_CELLS,
        MAX_DECODED_CELL_CODE_POINTS,
    ) == (300 * 1024 * 1024, 100_000, 1_000, 2_000_000, 1_000_000)
    assert (
        MAX_ANALYSIS_SPEC_BYTES,
        MAX_ANALYSIS_SPEC_DEPTH,
        MAX_ANALYSIS_SPEC_NODES,
        MAX_ANALYSIS_SPEC_STRING_CODE_POINTS,
    ) == (2 * 1024 * 1024, 64, 250_000, 2_000_000)
    assert (
        MAX_EXPANDED_MEMBERSHIPS,
        MAX_DISTINCT_LABELS,
        MAX_PAIR_OPERATIONS,
        MAX_NEUTRAL_RESULT_ROWS,
        MAX_CANONICAL_NEUTRAL_RESULT_BYTES,
        MAX_NORMALIZATION_MAPPING_ARTIFACT_BYTES,
        MAX_MCP_AGGREGATE_ITEMS,
        MAX_MCP_SERIALIZED_RESPONSE_BYTES,
    ) == (
        2_000_000,
        100_000,
        2_000_000,
        50_000,
        8 * 1024 * 1024,
        16 * 1024 * 1024,
        200,
        256 * 1024,
    )
    assert (
        MAX_OUTPUT_GROUPS,
        MAX_YEAR_BUCKETS,
        MAX_NEUTRAL_CELLS,
        MAX_RENDER_AXIS_LABELS,
        MAX_RENDER_VISIBLE_CELLS,
        MAX_OUTPUT_POINTS,
        MAX_NETWORK_DISPLAY_NODES,
        MAX_NETWORK_EDGES,
    ) == (50_000, 500, 50_000, 20, 400, 50_000, 500, 20_000)


def test_operation_budget_is_immutable_json_and_can_only_tighten_shared_limits() -> None:
    budget = OperationBudget(
        max_expanded_memberships=1_000_000,
        max_distinct_labels=50_000,
        max_pair_operations=1_000_000,
        max_neutral_result_rows=25_000,
        max_canonical_neutral_result_bytes=4 * 1024 * 1024,
        max_output_groups=10_000,
        max_year_buckets=100,
        max_neutral_cells=10_000,
        max_render_axis_labels=10,
        max_render_visible_cells=100,
        max_output_points=10_000,
        max_network_display_nodes=100,
        max_network_edges=1_000,
    )
    assert json.loads(json.dumps(budget.to_dict())) == budget.to_dict()
    with pytest.raises(FrozenInstanceError):
        budget.max_pair_operations = 1  # type: ignore[misc]
    with pytest.raises(ValueError, match="shared limit"):
        OperationBudget(max_pair_operations=MAX_PAIR_OPERATIONS + 1)


def test_matrix_budget_is_advertised_as_literal_closed_limits() -> None:
    from patent_analysis import describe_capabilities

    matrix = next(
        item for item in describe_capabilities()["analyses"] if item["analysis_id"] == "matrix.v1"
    )

    assert matrix["limits"] == {
        "max_visible_cells": 400,
        "max_expanded_contributions": 2_000_000,
    }
