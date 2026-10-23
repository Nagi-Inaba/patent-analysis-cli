import { describe, expect, it } from "vitest";
import { estimateLabelSize, type Rect } from "../src/label-layout.js";
import { buildPointsOption, renderPointsModelToRawSvg } from "../src/points-index.js";
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
  render_profile_id: "points-svg-ja-jp-node24-echarts6.v1"
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

type SeriesView = { type: string; name: string; itemStyle: { color: string }; data: Array<Record<string, unknown>> };

function seriesOf(option: Record<string, unknown>): SeriesView[] {
  return option.series as SeriesView[];
}

describe("points renderer", () => {
  it("builds a fixed scatter option with bounded bubble diameters", () => {
    const series = seriesOf(buildPointsOption(model, spec));
    const growth = series.find((item) => item.name === "成長")!;
    const decline = series.find((item) => item.name === "衰退")!;
    expect(growth.type).toBe("scatter");
    expect(growth.data[0]!.symbolSize).toBe(24);
    expect(decline.data[0]!.symbolSize).toBe(18);
  });

  it("splits points into one series per stage with the fixed stage colors", () => {
    const series = seriesOf(buildPointsOption(model, spec));
    expect(series.map((item) => [item.name, item.itemStyle.color, item.data.length])).toEqual([
      ["成長", "#0f766e", 1],
      ["安定", "#2563eb", 0],
      ["減速", "#a16207", 0],
      ["衰退", "#b45309", 1]
    ]);
  });

  it("shows a legend for all four stages unless there is nothing to plot", () => {
    const legend = buildPointsOption(model, spec).legend as { show: boolean; data: string[] };
    expect(legend.show).toBe(true);
    expect(legend.data).toEqual(["成長", "安定", "減速", "衰退"]);
    const empty = buildPointsOption({ ...model, points: [] }, spec).legend as { show: boolean };
    expect(empty.show).toBe(false);
  });

  it("draws no grid lines and formats years without a thousands separator", () => {
    const option = buildPointsOption(model, spec);
    for (const axis of [option.xAxis, option.yAxis] as Array<Record<string, unknown>>) {
      expect(axis.splitLine).toEqual({ show: false });
    }
    const label = (option.xAxis as { axisLabel: { formatter: (value: number) => string } }).axisLabel;
    expect(label.formatter(2018)).toBe("2018");
  });

  it("uses the palette's stage colours and opacity, and keeps the standard ones by default", () => {
    const standard = seriesOf(buildPointsOption(model, spec));
    const mono = seriesOf(buildPointsOption(model, { ...spec, palette: "monochrome" }));

    expect(standard.find((item) => item.name === "成長")!.itemStyle.color).toBe("#0f766e");
    expect(mono.map((item) => item.itemStyle.color)).toEqual(["#8c8c8c", "#666666", "#404040", "#1a1a1a"]);
  });

  it.each(["colorblind", "monochrome", "high-contrast"] as const)(
    "renders the %s palette inside the SVG policy",
    (palette) => {
      expect(() => renderPointsModelToRawSvg(model, { ...spec, palette })).not.toThrow();
    }
  );

  it("puts the y-axis name beside the tick labels so it never overlaps a point label", () => {
    const option = buildPointsOption(model, spec);
    const grid = option.grid as { left: number; containLabel: boolean };
    const yAxis = option.yAxis as { nameLocation: string; nameGap: number };

    expect(yAxis.nameLocation).toBe("middle");
    // The name is centred left of the plot edge, inside the left margin, at a fixed offset.
    expect(grid.containLabel).toBe(false);
    expect(grid.left - yAxis.nameGap).toBeGreaterThan(0);
    expect(grid.left - yAxis.nameGap).toBeLessThan(grid.left / 2);
  });
});

describe("point label placement", () => {
  const coincident: PointsChartModel = {
    ...model,
    points: [
      { label: "New", x: 2024, y: 100, size: 5, stage: "growth" },
      { label: "C", x: 2024, y: 100, size: 3, stage: "growth" },
      { label: "Old", x: 2018, y: 100, size: 4, stage: "growth" },
      { label: "A", x: 2020, y: -100, size: 9, stage: "decline" }
    ]
  };

  /** Rectangles of the point labels in the rendered SVG, sized with the module's own estimate. */
  function labelRects(svg: string, texts: readonly string[]): Map<string, Rect> {
    const found = new Map<string, Rect>();
    for (const match of svg.matchAll(/<text\b([^>]*)>([^<]*)<\/text>/gu)) {
      const text = match[2]!;
      if (!texts.includes(text)) continue;
      const at = /transform="translate\((-?[\d.]+),(-?[\d.]+)\)"/u.exec(match[1]!)!;
      const offset = Number(/(?<![\w-])y="(-?[\d.]+)"/u.exec(match[1]!)?.[1] ?? 0);
      const { width, height } = estimateLabelSize(text, 12);
      const anchor = /text-anchor="(\w+)"/u.exec(match[1]!)?.[1];
      const x = Number(at[1]);
      const left = anchor === "middle" ? x - width / 2 : anchor === "end" ? x - width : x;
      const centre = Number(at[2]) + offset;
      found.set(text, { left, top: centre - height / 2, right: left + width, bottom: centre + height / 2 });
    }
    return found;
  }
  const crosses = (a: Rect, b: Rect): boolean =>
    a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;

  it("keeps the labels of points at the same coordinates from overlapping", () => {
    const rects = labelRects(renderPointsModelToRawSvg(coincident, spec), ["New", "C", "Old", "A"]);

    expect([...rects.keys()].sort()).toEqual(["A", "C", "New", "Old"]);
    for (const [a, first] of rects) {
      for (const [b, second] of rects) {
        if (a < b) expect(crosses(first, second), `${a} over ${b}`).toBe(false);
      }
    }
  });

  it("leaves labels that collide with nothing above their points", () => {
    const alone = { ...model, points: coincident.points.filter((point) => point.label !== "C") };
    const option = buildPointsOption(alone, spec) as { series: Array<{ data: Array<{ label: { position: string } }> }> };

    expect(option.series.flatMap((series) => series.data.map((item) => item.label.position))).toEqual(
      ["top", "top", "top"]
    );
    // A label above its point is centred on it; one moved to a side would be start- or end-anchored.
    const svg = renderPointsModelToRawSvg(alone, spec);
    for (const text of ["New", "Old", "A"]) {
      expect(svg).toMatch(new RegExp(`text-anchor="middle"[^>]*>${text}</text>`, "u"));
    }
  });

  it("draws no labels while the fixed text is being measured", () => {
    const option = buildPointsOption(coincident, spec, "hidden") as {
      series: Array<{ data: Array<{ label: { show: boolean } }> }>;
    };
    const labels = option.series.flatMap((series) => series.data.map((item) => item.label.show));

    expect(labels).toEqual([false, false, false, false]);
  });

  it("renders every palette with the placement applied", () => {
    for (const palette of ["standard", "colorblind", "monochrome", "high-contrast"] as const) {
      expect(() => renderPointsModelToRawSvg(coincident, { ...spec, palette })).not.toThrow();
    }
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
