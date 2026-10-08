export const RENDER_PROFILE_ID = "ranking-svg-ja-jp-node22-echarts6.v1";

const height = Object.freeze({
  minimum: 675,
  base: 160,
  per_row: 36,
  row_count: Object.freeze({ minimum: 0, maximum: 101 })
});

const colors = Object.freeze({
  background: "#FFFFFF",
  positive: "#2563EB",
  negative: "#DC2626",
  remainder: "#94A3B8",
  text: "#0F172A",
  grid: "#E2E8F0"
});

export const VISUAL_PROFILE = Object.freeze({
  width: 1200,
  height,
  font_family: "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif",
  colors,
  remainder_border: "dashed",
  animation: false,
  ssr: true,
  axis_label_max_graphemes: 28,
  echarts_version: "6.1.0",
  source_order: "preserved",
  empty_state_text: "表示できるランキングデータがありません"
});
