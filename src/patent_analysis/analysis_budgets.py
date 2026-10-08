"""Shared v2 hard ceilings and immutable per-analysis operation budgets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields

MAX_CSV_BYTES = 300 * 1024 * 1024
MAX_ROWS = 100_000
MAX_COLUMNS = 1_000
MAX_PARSED_CELLS = 2_000_000
MAX_DECODED_CELL_CODE_POINTS = 1_000_000
MAX_ANALYSIS_SPEC_BYTES = 2 * 1024 * 1024
MAX_ANALYSIS_SPEC_DEPTH = 64
MAX_ANALYSIS_SPEC_NODES = 250_000
MAX_ANALYSIS_SPEC_STRING_CODE_POINTS = 2_000_000
MAX_EXPANDED_MEMBERSHIPS = 2_000_000
MAX_DISTINCT_LABELS = 100_000
MAX_PAIR_OPERATIONS = 2_000_000
MAX_NEUTRAL_RESULT_ROWS = 50_000
MAX_CANONICAL_NEUTRAL_RESULT_BYTES = 8 * 1024 * 1024
MAX_NORMALIZATION_MAPPING_ARTIFACT_BYTES = 16 * 1024 * 1024
MAX_MCP_AGGREGATE_ITEMS = 200
MAX_MCP_SERIALIZED_RESPONSE_BYTES = 256 * 1024
MAX_OUTPUT_GROUPS = 50_000
MAX_YEAR_BUCKETS = 500
MAX_NEUTRAL_CELLS = 50_000
MAX_RENDER_AXIS_LABELS = 20
MAX_RENDER_VISIBLE_CELLS = 400
MAX_OUTPUT_POINTS = 50_000
MAX_NETWORK_DISPLAY_NODES = 500
MAX_NETWORK_EDGES = 20_000


@dataclass(frozen=True, slots=True)
class OperationBudget:
    """Serializable analysis-specific ceilings that may only tighten shared limits."""

    max_expanded_memberships: int = MAX_EXPANDED_MEMBERSHIPS
    max_distinct_labels: int = MAX_DISTINCT_LABELS
    max_pair_operations: int = MAX_PAIR_OPERATIONS
    max_neutral_result_rows: int = MAX_NEUTRAL_RESULT_ROWS
    max_canonical_neutral_result_bytes: int = MAX_CANONICAL_NEUTRAL_RESULT_BYTES
    max_output_groups: int = MAX_OUTPUT_GROUPS
    max_year_buckets: int = MAX_YEAR_BUCKETS
    max_neutral_cells: int = MAX_NEUTRAL_CELLS
    max_render_axis_labels: int = MAX_RENDER_AXIS_LABELS
    max_render_visible_cells: int = MAX_RENDER_VISIBLE_CELLS
    max_output_points: int = MAX_OUTPUT_POINTS
    max_network_display_nodes: int = MAX_NETWORK_DISPLAY_NODES
    max_network_edges: int = MAX_NETWORK_EDGES

    def __post_init__(self) -> None:
        shared_limits = {
            "max_expanded_memberships": MAX_EXPANDED_MEMBERSHIPS,
            "max_distinct_labels": MAX_DISTINCT_LABELS,
            "max_pair_operations": MAX_PAIR_OPERATIONS,
            "max_neutral_result_rows": MAX_NEUTRAL_RESULT_ROWS,
            "max_canonical_neutral_result_bytes": MAX_CANONICAL_NEUTRAL_RESULT_BYTES,
            "max_output_groups": MAX_OUTPUT_GROUPS,
            "max_year_buckets": MAX_YEAR_BUCKETS,
            "max_neutral_cells": MAX_NEUTRAL_CELLS,
            "max_render_axis_labels": MAX_RENDER_AXIS_LABELS,
            "max_render_visible_cells": MAX_RENDER_VISIBLE_CELLS,
            "max_output_points": MAX_OUTPUT_POINTS,
            "max_network_display_nodes": MAX_NETWORK_DISPLAY_NODES,
            "max_network_edges": MAX_NETWORK_EDGES,
        }
        for field in fields(self):
            value = getattr(self, field.name)
            if type(value) is not int or value <= 0 or value > shared_limits[field.name]:
                raise ValueError(f"{field.name} must be within the shared limit")

    def to_dict(self) -> dict[str, int]:
        return asdict(self)
