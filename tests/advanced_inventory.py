"""Literal release inventory, independent of the implementation registry."""

from __future__ import annotations

ADVANCED_IDS = (
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
)
ADVANCED_MARKS = tuple(name.removesuffix(".v1") + "-svg.v1" for name in ADVANCED_IDS)
# Native inventor IDs require explicit raw bindings; never add to legacy fixture loops.
INVENTOR_IDS = (
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
)
# Finite release expectation, not derived from the implementation presentation table.
# M10 mobility evidence is deliberately JSON-only.
INVENTOR_MARKS = (
    "inventor-network-svg.v1",
    "inventor-ego-network-svg.v1",
    "inventor-technology-svg.v1",
    "inventor-activity-svg.v1",
    "inventor-cluster-flow-svg.v1",
    "inventor-similarity-svg.v1",
    "inventor-impact-svg.v1",
    "inventor-mobility-svg.v1",
    "inventor-mobility-flow-svg.v1",
)
ANALYSIS_IDS = (
    "ranking.v1",
    "matrix.v1",
    "timeline.v1",
    "composition.v1",
    "growth.v1",
    "concentration.v1",
    "lifecycle.v1",
    *ADVANCED_IDS,
    *INVENTOR_IDS,
)
MCP_IDS = ANALYSIS_IDS
MCP_MARKS = (
    "ranking-svg.v1",
    "matrix-bubble-svg.v1",
    "matrix-heatmap-svg.v1",
    "series-line-svg.v1",
    "series-stacked-bar-svg.v1",
    "composition-bar-svg.v1",
    "composition-pie-svg.v1",
    "points-bubble-svg.v1",
    *ADVANCED_MARKS,
    *INVENTOR_MARKS,
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


def expected_inventor_capabilities():
    metadata = (
        ("network", "Full observed co-invention graph; not employment evidence."),
        ("network", "Literal-focus ego view retaining full-graph metrics."),
        ("matrix", "Witnessed technology profiles with full-population references."),
        ("network", "Annual patent activity; absence is not inactivity or retirement."),
        ("network", "Adjacent-calendar observed community membership flows."),
        ("points", "Neutral full-pool technology features and cosine similarities."),
        ("points", "Explicit-snapshot patent citation metrics; not personal ability."),
        ("network", "Patent-applicant episodes and separately reviewed move candidates."),
        ("network", "Conservative directed legal or historical-group candidate flows."),
        ("grouped-metrics", "Stable candidate evidence and review audit tables; no SVG."),
    )
    output = []
    for i, (aid, (variant, description)) in enumerate(zip(INVENTOR_IDS, metadata, strict=True)):
        limits = {
            "max_rows": 5000,
            "max_units": 5000,
            "max_people": 200,
            "max_pair_expansions": 50000,
            "max_columns": 128,
            "max_sidecar_bytes": 1048576,
            "max_sidecar_rows": 5000,
            "max_statistics_bytes": 204800,
            "max_result_bytes": 262144,
        }
        if i in (0, 1, 3, 4):
            limits["max_edges"] = 5000
        if i in (3, 4, 6, 7, 8, 9):
            limits["max_year_span"] = 30
        if i >= 7:
            limits.update(
                max_association_rows=5000, max_candidate_rows=5000, max_comparisons=200000
            )
        if i < 7 or i == 8:
            limits.update(precision_decimal_places=12, max_fraction_bits=128)
        if i == 8:
            limits["max_flow_contributions"] = 5000
        output.append(
            dict(
                analysis_id=aid,
                algorithm_version="1.0.0",
                description=description,
                required_roles=[],
                optional_roles=[],
                resolution_profiles=[],
                normalization_profiles=[],
                result_variant=variant,
                render_marks=[INVENTOR_MARKS[i]] if i < len(INVENTOR_MARKS) else [],
                mcp_public=True,
                spec_schema=f"schemas/{aid[:-3]}-parameters-v1.schema.json",
                result_schema=f"schemas/{aid[:-3]}-result-v1.schema.json",
                limits=limits,
            )
        )
    return output


def expected_advanced_capabilities() -> list[dict[str, object]]:
    return [
        {
            "analysis_id": analysis_id,
            "algorithm_version": "1.0.0",
            "description": description,
            "required_roles": [],
            "optional_roles": [],
            "resolution_profiles": ["column-alias.v2"],
            "normalization_profiles": [],
            "result_variant": variant,
            "render_marks": [mark],
            "mcp_public": True,
            "spec_schema": f"schemas/{analysis_id[:-3]}-parameters-v1.schema.json",
            "result_schema": f"schemas/{analysis_id[:-3]}-result-v1.schema.json",
            "limits": {
                "max_rows": 100_000,
                "max_normalized_tokens": 2_000_000,
                "max_values_per_role": 100,
                "max_label_json_bytes": 4096,
                "max_expanded_contributions": 1_000_000,
                "max_distinct_tracking_keys": 100_000,
                "max_result_bytes": 196_608 if analysis_id == "inventor-tracking.v1" else 98_304,
                **(
                    {"max_inventors": 20, "max_year_span": 12}
                    if analysis_id == "inventor-tracking.v1"
                    else {}
                ),
            },
        }
        for analysis_id, mark, (variant, description) in zip(
            ADVANCED_IDS,
            ADVANCED_MARKS,
            _ADVANCED_METADATA,
            strict=True,
        )
    ]
