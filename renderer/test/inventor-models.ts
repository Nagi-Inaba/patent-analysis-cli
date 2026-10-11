import type { AdvancedModel, AdvancedProjection, AdvancedSpec } from "../src/advanced-types.js";

// Synthetic, neutral data only. Names are placeholders and carry no real identity.
export const SPEC: AdvancedSpec = {
  render_spec_contract_version: "1.0.0", renderer_kind: "advanced.svg", locale: "ja-JP", timezone: "UTC",
  width: 1200, height: 675, font_family: "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif",
  animation: false, axis_label_max_graphemes: 28, echarts_version: "6.1.0",
  render_profile_id: "advanced-svg-ja-jp-node22-echarts6.v1"
};
export const ANALYSES = [
  { analysis_id: "inventor-network.v1", title: "共発明ネットワーク", kind: "inventor-network" },
  { analysis_id: "inventor-ego-network.v1", title: "発明者中心の関係マップ", kind: "inventor-network" },
  { analysis_id: "inventor-technology.v1", title: "発明者×技術分野", kind: "inventor-heatmap" },
  { analysis_id: "inventor-activity.v1", title: "発明者の活動履歴", kind: "inventor-timeline" },
  { analysis_id: "inventor-cluster-flow.v1", title: "協働グループの変遷", kind: "inventor-alluvial" },
  { analysis_id: "inventor-similarity.v1", title: "発明者の技術類似度", kind: "inventor-scatter" },
  { analysis_id: "inventor-impact.v1", title: "発明者の活動量と引用指標", kind: "inventor-scatter" },
  { analysis_id: "inventor-mobility.v1", title: "発明者と企業の関係変化", kind: "inventor-timeline" },
  { analysis_id: "inventor-mobility-flow.v1", title: "企業間の観測・移動フロー", kind: "inventor-network" }
] as const;
export type InventorAnalysisId = (typeof ANALYSES)[number]["analysis_id"];

export function markOf(analysisId: string): string {
  return analysisId.replace(/\.v1$/u, "-svg.v1");
}
export function inventorModel(analysisId: InventorAnalysisId, projection: AdvancedProjection): AdvancedModel {
  const entry = ANALYSES.find(item => item.analysis_id === analysisId)!;
  return {
    chart_model_contract_version: "1.0.0", chart_type: "advanced.svg", analysis_id: analysisId,
    mark: markOf(analysisId), title: entry.title, analysis_result_sha256: "0".repeat(63) + "1",
    projection, population: { input_rows: 12, analyzed_rows: 10, excluded_rows: 2 }, warnings: []
  };
}

type Projection<K extends AdvancedProjection["kind"]> = Extract<AdvancedProjection, { kind: K }>;

export function heatmapProjection(): Projection<"inventor-heatmap"> {
  return {
    kind: "inventor-heatmap", x: ["Field A", "Field B", "Field C"], y: ["Alpha Person", "Beta Person"],
    x_label: "技術分野", y_label: "発明者", value_label: "構成比 (%)",
    cells: [
      { x: 0, y: 0, value: 12.5 }, { x: 1, y: 0, value: 0.25 }, { x: 2, y: 0, value: null },
      { x: 0, y: 1, value: 0 }, { x: 1, y: 1, value: 50 }, { x: 2, y: 1, value: 37.25 }
    ],
    context: "synthetic technology context"
  };
}

export function timelineProjection(withBands: boolean): Projection<"inventor-timeline"> {
  return {
    kind: "inventor-timeline", lanes: ["Alpha Person", "Beta Person"], years: [2019, 2020, 2021, 2022, 2023],
    nodes: [
      { id: "t-1", x: 2019, y: 0, size: 4, category: 0, label: "Company X 2019", state: "observed" },
      { id: "t-2", x: 2021.5, y: 0, size: 1, category: 1, label: "Company Y 2021-06", state: "inferred" },
      { id: "t-3", x: 2022.25, y: 0, size: 0, category: 1, label: "Company Y", state: "confirmed" },
      { id: "t-4", x: 2020, y: 1, size: 4, category: 2, label: "Company Z", state: "unknown" }
    ],
    links: [
      { source: 0, target: 1, gap: true, state: "observed" },
      { source: 1, target: 2, gap: false, state: "inferred" }
    ],
    bands: withBands ? [
      { id: "b-1", start: 2020.5, end: 2022, label: "Event One", kind: "acquisition", status: "completed" },
      { id: "b-2", start: 2021, end: 2023, label: "Event Two", kind: "name_change", status: "announced" }
    ] : [],
    context: "synthetic timeline context"
  };
}

export function alluvialProjection(): Projection<"inventor-alluvial"> {
  return {
    kind: "inventor-alluvial", years: [2019, 2020, 2021, 2022],
    nodes: [
      { id: "a-1", label: "Group A 2019", year: 2019, members: 6, kind: "cluster" },
      { id: "a-2", label: "Group B 2019", year: 2019, members: 3, kind: "cluster" },
      { id: "a-3", label: "Group A 2020", year: 2020, members: 6, kind: "cluster" },
      { id: "a-4", label: "Group C 2020", year: 2020, members: 2, kind: "cluster" },
      { id: "a-5", label: "New 2019", year: 2019, members: 1, kind: "newly_observed" },
      { id: "a-6", label: "Group D 2022", year: 2022, members: 4, kind: "cluster" },
      { id: "a-7", label: "Unseen 2021", year: 2021, members: 2, kind: "not_observed" }
    ],
    links: [
      { source: 0, target: 2, value: 4, kind: "continuation" },
      { source: 0, target: 3, value: 2, kind: "split" },
      { source: 1, target: 2, value: 1, kind: "merge" },
      { source: 3, target: 5, value: 2, kind: "gap" },
      { source: 4, target: 2, value: 1, kind: "newly_observed" },
      { source: 2, target: 6, value: 2, kind: "not_observed" }
    ],
    context: "synthetic cluster flow"
  };
}

export function scatterProjection(): Projection<"inventor-scatter"> {
  return {
    kind: "inventor-scatter", x_label: "第1軸", y_label: "第2軸", size_label: "活動量",
    points: [
      { id: "p-1", label: "Alpha Person", x: -1.5, y: 0.5, size: 9, category: "cluster-a" },
      { id: "p-2", label: "Beta Person", x: 2, y: 1.25, size: 4, category: "cluster-b" },
      { id: "p-3", label: "Gamma Person", x: 0, y: -2, size: 0, category: "cluster-a" }
    ],
    edges: [{ source: 0, target: 1, value: 2 }, { source: 1, target: 2, value: 1 }],
    unplottable: [{ id: "u-1", label: "Delta Person", reason: "引用指標が未定義" }],
    context: "synthetic scatter context"
  };
}

export function networkProjection(): Projection<"inventor-network"> {
  return {
    kind: "inventor-network",
    nodes: [
      { id: "n-a", label: "Alpha Person", x: -10, y: 4, value: 9, group: 0, hop: 0 },
      { id: "n-b", label: "Beta Person", x: 3, y: 8, value: 4, group: 0, hop: 1 },
      { id: "n-c", label: "Gamma Person", x: 12, y: -6, value: 1, group: 1, hop: 1 },
      { id: "n-d", label: "Delta Isolated", x: 0, y: -12, value: 0, group: 2, hop: null }
    ],
    edges: [
      { source: 0, target: 1, value: 3, directed: false, state: "observed" },
      { source: 1, target: 2, value: 1, directed: false, state: "inferred" },
      { source: 0, target: 2, value: 2, directed: false, state: "confirmed" }
    ],
    focus: null, context: "synthetic co-invention context"
  };
}
export function egoProjection(): Projection<"inventor-network"> {
  return { ...networkProjection(), focus: "n-a" };
}
export function flowProjection(): Projection<"inventor-network"> {
  return {
    kind: "inventor-network",
    nodes: [
      { id: "c-1", label: "Company One", x: -8, y: 0, value: 6, group: 0, hop: null },
      { id: "c-2", label: "Company Two", x: 8, y: 0, value: 2, group: 1, hop: null },
      { id: "c-3", label: "Company Three", x: 0, y: 9, value: 5, group: 2, hop: null }
    ],
    edges: [
      { source: 0, target: 1, value: 4, directed: true, state: "corporate" },
      { source: 1, target: 0, value: 1, directed: true, state: "observed" },
      { source: 1, target: 2, value: 2, directed: true, state: "inferred" }
    ],
    focus: null, context: "synthetic company flow"
  };
}
