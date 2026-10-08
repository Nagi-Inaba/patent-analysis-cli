"""Literal release inventory, independent of the implementation registry."""
from __future__ import annotations

ADVANCED_IDS = (
    "growth-quadrant.v1", "entry-exit.v1", "citation.v1", "matrix-composition.v1",
    "new-entrants.v1", "compara.v1", "cooccurrence.v1", "collaboration-network.v1",
    "uniqueness.v1", "shared-involvement.v1", "inventor-tracking.v1",
)
ADVANCED_MARKS = tuple(name.removesuffix(".v1") + "-svg.v1" for name in ADVANCED_IDS)
ANALYSIS_IDS = (
    "ranking.v1", "matrix.v1", "timeline.v1", "composition.v1", "growth.v1",
    "concentration.v1", "lifecycle.v1", *ADVANCED_IDS,
)
MCP_IDS = ANALYSIS_IDS
MCP_MARKS = (
    "ranking-svg.v1", "matrix-bubble-svg.v1", "matrix-heatmap-svg.v1",
    "series-line-svg.v1", "series-stacked-bar-svg.v1",
    "composition-bar-svg.v1", "composition-pie-svg.v1", "points-bubble-svg.v1", *ADVANCED_MARKS,
)
_ADVANCED_METADATA = (
    ("quadrant", "Long- and short-span half-period count changes."),
    ("points", "First and last observed years and recent activity."),
    ("points", "Top record-level citation counts, not applicant totals."),
    ("composition", "Category membership composition of an explicit matrix cell."),
    ("matrix", "New-to-population applicants and classification membership shares."),
    ("matrix", "Explicit group A minus group B count matrix."),
    ("matrix", "Symmetric, zero-diagonal unordered cooccurrence counts."),
    ("network", "Bounded collaboration nodes and unordered links."),
    ("grouped-metrics", "Distinct exclusive items using full-population ownership."),
    ("grouped-metrics", "Shared items and once-per-record involvement counts."),
    ("network", "Annual co-invention clusters and observed applicant changes."),
)


def expected_advanced_capabilities() -> list[dict[str, object]]:
    return [
        {
            "analysis_id": analysis_id, "algorithm_version": "1.0.0",
            "description": description, "required_roles": [], "optional_roles": [],
            "resolution_profiles": ["column-alias.v2"], "normalization_profiles": [],
            "result_variant": variant, "render_marks": [mark], "mcp_public": True,
            "spec_schema": f"schemas/{analysis_id[:-3]}-parameters-v1.schema.json",
            "result_schema": f"schemas/{analysis_id[:-3]}-result-v1.schema.json",
            "limits": {
                "max_rows": 100_000, "max_normalized_tokens": 2_000_000,
                "max_values_per_role": 100, "max_label_json_bytes": 4096,
                "max_expanded_contributions": 1_000_000,
                "max_distinct_tracking_keys": 100_000,
                "max_result_bytes": 196_608 if analysis_id == "inventor-tracking.v1" else 98_304,
                **({"max_inventors": 20, "max_year_span": 12}
                   if analysis_id == "inventor-tracking.v1" else {}),
            },
        }
        for analysis_id, mark, (variant, description) in zip(
            ADVANCED_IDS, ADVANCED_MARKS, _ADVANCED_METADATA, strict=True,
        )
    ]
