import { describe, expect, it } from "vitest";
import { buildPointsOption } from "../src/points-index.js";
import type { PointsChartModel, PointsRenderSpec } from "../src/points-payload.js";

const spec: PointsRenderSpec = {
  render_spec_contract_version: "1.0.0",
  renderer_kind: "points.bubble.svg",
  locale: "ja-JP",
  timezone: "UTC",
  width: 1200,
  height: 675,
  font_family: "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif",
  animation: false,
  axis_label_max_graphemes: 28,
  echarts_version: "6.1.0",
  render_profile_id: "points-svg-ja-jp-node22-echarts6.v1"
};

const model: PointsChartModel = {
  chart_model_contract_version: "1.0.0",
  chart_type: "points.bubble",
  mark: "points-bubble-svg.v1",
  analysis_result_sha256: "a".repeat(64),
  title: "技術ライフサイクル",
  x_axis: { label: "ピーク年", value_kind: "year" },
  y_axis: { label: "CAGR（%）", value_kind: "number" },
  size_axis: { label: "総件数", value_kind: "count" },
  points: [
    { label: "X分類", x: 2022, y: 18.9, size: 6, stage: "growth" },
    { label: "Y分類", x: 2018, y: -100, size: 3, stage: "decline" }
  ],
  population: { input_rows: 6, analyzed_rows: 6, excluded_rows: 0 },
  warnings: []
};

describe("points renderer", () => {
  it("builds a fixed scatter option with bounded bubble diameters", () => {
    const option = buildPointsOption(model, spec);
    const series = (option.series as Array<Record<string, unknown>>)[0]!;
    const data = series.data as Array<Record<string, unknown>>;
    expect(series.type).toBe("scatter");
    expect(data[0]!.symbolSize).toBe(24);
    expect(data[1]!.symbolSize).toBe(18);
  });
});

it("uses a local year domain rather than compressing all years against year zero", () => {
  const option = buildPointsOption(model, spec);
  expect((option.xAxis as Record<string, unknown>).scale).toBe(true);
});

it("treats source labels as literal text, not ECharts formatter templates", () => {
  const input = { ...model, points: [{ ...model.points[0]!, label: '{a}<script>"&' }] };
  const option = buildPointsOption(input, spec);
  const data = (option.series as Array<{data: Array<{label:{formatter: unknown}}>}>)[0]!.data;
  expect(typeof data[0]!.label.formatter).toBe("function");
  expect((data[0]!.label.formatter as () => string)()).toBe('{a}<script>"&');
});

it("includes the ellipsis within the 28-grapheme bound", () => {
  const input = { ...model, points: [{ ...model.points[0]!, label: "長".repeat(100) }] };
  const option = buildPointsOption(input, spec);
  const data = (option.series as Array<{data: Array<{label:{formatter: unknown}}>}>)[0]!.data;
  const formatter = data[0]!.label.formatter;
  const text = typeof formatter === "function" ? formatter() as string : formatter as string;
  expect([...new Intl.Segmenter("ja-JP", {granularity:"grapheme"}).segment(text)]).toHaveLength(28);
  expect(text.endsWith("…")).toBe(true);
});
