"""Finite presentation inventory for the approved native analyses.

This describes fixed presentation semantics, never a user-programmable chart API.
Legacy Ranking, Matrix, categorical and Lifecycle marks are unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from patent_analysis.advanced_renderer_build import ADVANCED_BUILD

ADVANCED_RENDER_PROFILE_ID = "advanced-svg-ja-jp-node24-echarts6.v1"
MAX_ADVANCED_MODEL_BYTES = 256 * 1024

# Older verified activation records predate a per-mark inventory. This frozen
# compatibility set must never be derived from the expanding presentation table.
_LEGACY_BUILT_MARKS = (
    "growth-quadrant-svg.v1",
    "entry-exit-svg.v1",
    "citation-svg.v1",
    "matrix-composition-svg.v1",
    "new-entrants-svg.v1",
    "compara-svg.v1",
    "cooccurrence-svg.v1",
    "collaboration-network-svg.v1",
    "uniqueness-svg.v1",
    "shared-involvement-svg.v1",
    "inventor-tracking-svg.v1",
)


@dataclass(frozen=True, slots=True)
class AdvancedPresentation:
    analysis_id: str
    mark: str
    result_variant: str
    title: str
    kind: str


_PRESENTATIONS = (
    AdvancedPresentation(
        "growth-quadrant.v1",
        "growth-quadrant-svg.v1",
        "quadrant",
        "長期・短期成長四象限",
        "quadrant",
    ),
    AdvancedPresentation(
        "entry-exit.v1", "entry-exit-svg.v1", "points", "初回・最終観測年", "scatter"
    ),
    AdvancedPresentation(
        "citation.v1", "citation-svg.v1", "points", "レコード別被引用マップ", "scatter"
    ),
    AdvancedPresentation(
        "matrix-composition.v1",
        "matrix-composition-svg.v1",
        "composition",
        "選択セルの構成内訳",
        "bars",
    ),
    AdvancedPresentation(
        "new-entrants.v1", "new-entrants-svg.v1", "matrix", "母集団内の新規参入者と分類", "heatmap"
    ),
    AdvancedPresentation(
        "compara.v1", "compara-svg.v1", "matrix", "グループ間の件数差分", "heatmap"
    ),
    AdvancedPresentation(
        "cooccurrence.v1", "cooccurrence-svg.v1", "matrix", "分類の共起件数", "heatmap"
    ),
    AdvancedPresentation(
        "collaboration-network.v1",
        "collaboration-network-svg.v1",
        "network",
        "共同関係ネットワーク",
        "network",
    ),
    AdvancedPresentation(
        "uniqueness.v1", "uniqueness-svg.v1", "grouped-metrics", "グループ別の固有項目", "bars"
    ),
    AdvancedPresentation(
        "shared-involvement.v1",
        "shared-involvement-svg.v1",
        "grouped-metrics",
        "グループ別の共有項目と関与",
        "bars",
    ),
)
_PRESENTATIONS += (
    AdvancedPresentation(
        "inventor-tracking.v1",
        "inventor-tracking-svg.v1",
        "network",
        "発明者・共発明クラスタの年次追跡",
        "tracking",
    ),
    AdvancedPresentation(
        "inventor-network.v1",
        "inventor-network-svg.v1",
        "network",
        "共発明ネットワーク",
        "inventor-network",
    ),
    AdvancedPresentation(
        "inventor-ego-network.v1",
        "inventor-ego-network-svg.v1",
        "network",
        "発明者中心の関係マップ",
        "inventor-network",
    ),
    AdvancedPresentation(
        "inventor-technology.v1",
        "inventor-technology-svg.v1",
        "matrix",
        "発明者×技術分野",
        "inventor-heatmap",
    ),
)
_PRESENTATIONS += (
    AdvancedPresentation(
        "inventor-activity.v1",
        "inventor-activity-svg.v1",
        "network",
        "発明者の活動履歴",
        "inventor-timeline",
    ),
)
_PRESENTATIONS += (
    AdvancedPresentation(
        "inventor-cluster-flow.v1",
        "inventor-cluster-flow-svg.v1",
        "network",
        "協働グループの変遷",
        "inventor-alluvial",
    ),
)
_PRESENTATIONS += (
    AdvancedPresentation(
        "inventor-similarity.v1",
        "inventor-similarity-svg.v1",
        "points",
        "発明者の技術類似度",
        "inventor-scatter",
    ),
)
_PRESENTATIONS += (
    AdvancedPresentation(
        "inventor-impact.v1",
        "inventor-impact-svg.v1",
        "points",
        "発明者の活動量と引用指標",
        "inventor-scatter",
    ),
)
_PRESENTATIONS += (
    AdvancedPresentation(
        "inventor-mobility.v1",
        "inventor-mobility-svg.v1",
        "network",
        "発明者と企業の関係変化",
        "inventor-timeline",
    ),
)
_PRESENTATIONS += (
    AdvancedPresentation(
        "inventor-mobility-flow.v1",
        "inventor-mobility-flow-svg.v1",
        "network",
        "企業間の観測・移動フロー",
        "inventor-network",
    ),
)
ADVANCED_PRESENTATIONS = MappingProxyType({p.analysis_id: p for p in _PRESENTATIONS})
ADVANCED_MARK_TO_ID = MappingProxyType({p.mark: p.analysis_id for p in _PRESENTATIONS})
ADVANCED_RENDER_MARKS = tuple(ADVANCED_MARK_TO_ID)


def get_advanced_presentation(analysis_id: str, mark: str | None = None) -> AdvancedPresentation:
    try:
        definition = ADVANCED_PRESENTATIONS[analysis_id]
    except (KeyError, TypeError):
        raise ValueError("unknown advanced presentation") from None
    if mark is not None and mark != definition.mark:
        raise ValueError("advanced result and render mark are incompatible")
    return definition


def advanced_marks_for(analysis_id: str) -> tuple[str, ...]:
    """An unbuilt source distribution must not advertise an unavailable renderer."""
    if ADVANCED_BUILD is None or analysis_id not in ADVANCED_PRESENTATIONS:
        return ()
    mark = ADVANCED_PRESENTATIONS[analysis_id].mark
    built = ADVANCED_BUILD.get("built_marks", _LEGACY_BUILT_MARKS)
    if not isinstance(built, (list, tuple)) or not all(isinstance(item, str) for item in built):
        return ()
    return (mark,) if mark in built else ()
