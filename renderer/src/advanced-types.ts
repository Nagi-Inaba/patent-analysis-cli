/** Closed renderer input types. No option objects or executable input are accepted. */
export type AdvancedPoint = {
  id: string; label: string; x: number; y: number; size: number; category: string;
};
export type AdvancedProjection =
  | { kind: "tracking"; years: number[]; inventors: string[];
      nodes: { x: number; y: number; cluster: number; count: number; applicants: string;
        changed: boolean; unknown: boolean }[];
      links: { source: number; target: number; gap: boolean }[]; context: string }
  | { kind: "scatter"; x_label: string; y_label: string; size_label: string;
      x_year: boolean; y_year: boolean; points: AdvancedPoint[]; context: string }
  | { kind: "quadrant"; x_label: string; y_label: string; size_label: string;
      points: AdvancedPoint[]; unplottable: { label: string; long_state: string; short_state: string; count: number }[]; context: string }
  | { kind: "heatmap"; x: string[]; y: string[]; x_label: string; y_label: string;
      signed: boolean; cells: { x: number; y: number; value: number; share: number | null }[]; context: string }
  | { kind: "bars"; value_label: string;
      items: { label: string; value: number; denominator: number; share: number;
        record_count: number; involvement_count: number | null }[]; context: string }
  | { kind: "network"; nodes: { label: string; value: number }[];
      edges: { source: number; target: number; value: number }[]; context: string };
export type AdvancedModel = {
  chart_model_contract_version: "1.0.0";
  chart_type: "advanced.svg";
  analysis_id: string; mark: string; title: string; analysis_result_sha256: string;
  projection: AdvancedProjection;
  population: { input_rows: number; analyzed_rows: number; excluded_rows: number };
  warnings: string[];
};
export type AdvancedSpec = {
  render_spec_contract_version: "1.0.0";
  renderer_kind: "advanced.svg";
  locale: "ja-JP"; timezone: "UTC"; width: 1200; height: 675;
  font_family: "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif";
  animation: false; axis_label_max_graphemes: 28; echarts_version: "6.1.0";
  render_profile_id: "advanced-svg-ja-jp-node22-echarts6.v1";
};
export type AdvancedRuntime = {
  node_version: "22.19.0"; echarts_version: "6.1.0";
  renderer_build_digest: string;
  render_profile_id: "advanced-svg-ja-jp-node22-echarts6.v1";
};
