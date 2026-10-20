import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "vitest";
import { buildAdvancedOption, truncateAdvancedLabel } from "../src/advanced-options.js";
import type { AdvancedModel, AdvancedSpec } from "../src/advanced-types.js";

// These views specify the shapes exercised below; runtime assertions remain authoritative.
type PointView = {
  value: number[];
  symbolSize: number;
  label: { formatter: () => string; textBorderWidth?: number };
};
type OptionView<T = PointView> = {
  title: { subtext: string };
  visualMap: { type: string; splitNumber: number; min: number; max: number };
  series: {
    type: string; force?: unknown; data: T[];
    markLine: {
      data: { coord: number[] }[][];
      lineStyle: { width: number }; symbol: string;
    };
  }[];
};
// A heatmap cell carries its own label colour, so it is an item object rather than a bare triple.
type HeatmapDatum = { value: number[]; label: { color: string } };
function optionView<T = PointView>(model: AdvancedModel, spec: AdvancedSpec): OptionView<T> {
  const option = buildAdvancedOption(model, spec);
  assert.ok(Array.isArray(option.series));
  assert.ok(option.title && typeof option.title === "object");
  return option as unknown as OptionView<T>;
}

const fixtures = JSON.parse(readFileSync(new URL("./fixtures/advanced-models.json", import.meta.url), "utf8")) as {
  spec: AdvancedSpec; models: AdvancedModel[];
};
for (const model of fixtures.models) {
  test(`${model.analysis_id}: stable fixed option, no source mutation`, () => {
    const before = JSON.stringify(model);
    const first = buildAdvancedOption(model, fixtures.spec);
    const second = buildAdvancedOption(model, fixtures.spec);
    assert.equal(JSON.stringify(first), JSON.stringify(second));
    assert.equal(JSON.stringify(model), before);
    assert.equal(first.animation, false);
    assert.equal(first.tooltip, undefined);
    assert.ok(Array.isArray(first.series));
  });
}

test("quadrant retains unknown-rate warning without inventing a point", () => {
  const model = fixtures.models.find(m => m.analysis_id === "growth-quadrant.v1")!;
  assert.equal(model.projection.kind, "quadrant");
  if (model.projection.kind !== "quadrant") throw new Error("fixture");
  const p = model.projection;
  p.unplottable = [{ label: "New", long_state: "new", short_state: "new", count: 2 }];
  const option = optionView(model, fixtures.spec);
  assert.equal(option.series[0].data.length, p.points.length);
  assert.match(option.title.subtext, /座標表示対象外 1/);
});

test("signed Compara has equal positive and negative scale endpoints", () => {
  const model = fixtures.models.find(m => m.analysis_id === "compara.v1")!;
  const option = optionView<HeatmapDatum>(model, fixtures.spec);
  assert.equal(option.visualMap.min, -option.visualMap.max);
  assert.ok(option.series[0].data.some((p) => p.value[2]! < 0));
});

test("network uses fixed numeric positions, no force physics", () => {
  const model = fixtures.models.find(m => m.analysis_id === "collaboration-network.v1")!;
  if (model.projection.kind !== "network") throw new Error("fixture");
  const option = optionView(model, fixtures.spec);
  const scatter = option.series[0];
  assert.equal(scatter.type, "scatter");
  assert.equal(scatter.force, undefined);
  assert.ok(scatter.data.every((n) =>
    Number.isFinite(n.value[0]) && Number.isFinite(n.value[1])));
  assert.equal(option.series.length - 1, model.projection.edges.length);
});

test("source labels are literal functions, not ECharts templates", () => {
  const model = structuredClone(fixtures.models.find(m => m.analysis_id === "citation.v1")!);
  if (model.projection.kind !== "scatter") throw new Error("fixture");
  model.projection.points[0]!.label = "{a}<script>";
  const option = optionView(model, fixtures.spec);
  assert.equal(option.series[0].data[0].label.formatter(), "{a}<script>");
  assert.equal(truncateAdvancedLabel("👩‍🔬AB", 2), "👩‍🔬…");
});

test("zero citations remain zero data with a visible minimum symbol", () => {
  const model = structuredClone(fixtures.models.find(m => m.analysis_id === "citation.v1")!);
  if (model.projection.kind !== "scatter") throw new Error("fixture");
  const point = model.projection.points[0]!;
  point.y = 0; point.size = 0;
  const option = optionView(model, fixtures.spec);
  assert.equal(option.series[0].data[0].value[1], 0);
  assert.ok(option.series[0].data[0].symbolSize > 0);
});

test("all empty projections still produce a bounded view", () => {
  for (const source of fixtures.models) {
    const model = structuredClone(source);
    const p = model.projection;
    if (p.kind === "scatter" || p.kind === "quadrant") p.points = [];
    if (p.kind === "quadrant") p.unplottable = [];
    if (p.kind === "bars") p.items = [];
    if (p.kind === "heatmap") { p.x = []; p.y = []; p.cells = []; }
    if (p.kind === "network") { p.nodes = []; p.edges = []; }
    if (p.kind === "tracking") { p.nodes = []; p.links = []; p.years = []; p.inventors = []; }
    const option = optionView(model, fixtures.spec);
    assert.match(option.title.subtext, /対象データなし/);
  }
});

test("heatmaps keep their values with bounded non-gradient legends", () => {
  for (const source of fixtures.models.filter(m => m.projection.kind === "heatmap")) {
    const model = structuredClone(source);
    if (model.projection.kind !== "heatmap") throw new Error("fixture");
    const p = model.projection;
    const before = JSON.stringify(model);
    const option = optionView<HeatmapDatum>(model, fixtures.spec);
    assert.equal(option.visualMap.type, "piecewise");
    assert.equal(option.visualMap.splitNumber, 5);
    assert.equal(option.visualMap.min, p.signed ? -option.visualMap.max : 0);
    for (const cell of p.cells) {
      assert.ok(option.series[0].data.some(({ value: v }) =>
        v[0] === cell.x && v[1] === cell.y && v[2] === cell.value));
    }
    assert.equal(JSON.stringify(model), before);
  }
});

test("network links preserve endpoints and bound stroke precision", () => {
  const model = structuredClone(fixtures.models.find(m => m.analysis_id === "collaboration-network.v1")!);
  if (model.projection.kind !== "network") throw new Error("fixture");
  model.projection.nodes = [{ label: "A", value: 7 }, { label: "B", value: 5 }, { label: "C", value: 3 }];
  model.projection.edges = [{ source: 0, target: 1, value: 3 }, { source: 1, target: 2, value: 1 }];
  const before = JSON.stringify(model);
  const option = optionView(model, fixtures.spec);
  const nodes = option.series[0].data;
  assert.deepEqual(nodes.map((n) => n.value[2]), [7, 5, 3]);
  model.projection.edges.forEach((edge, index) => {
    const line = option.series[index + 1].markLine;
    assert.deepEqual(line.data, [[
      { coord: nodes[edge.source].value.slice(0, 2) },
      { coord: nodes[edge.target].value.slice(0, 2) }
    ]]);
    assert.match(String(line.lineStyle.width), /^\d+(\.\d{1,6})?$/);
    assert.equal(line.symbol, "none");
  });
  assert.ok(nodes.every((n) => n.label.textBorderWidth === 0));
  assert.equal(JSON.stringify(model), before);
});

type AxisView = {
  minInterval?: number;
  axisLine?: { onZero?: boolean };
  axisLabel?: { rotate?: number; formatter?: (value: number) => string };
};
const axesView = (id: string) => {
  const model = fixtures.models.find(m => m.analysis_id === id)!;
  return buildAdvancedOption(model, fixtures.spec) as unknown as { xAxis: AxisView; yAxis: AxisView };
};

test("year axes label ticks as plain years, never grouped quantities", () => {
  const entryExit = axesView("entry-exit.v1");
  for (const axis of [entryExit.xAxis, entryExit.yAxis]) {
    assert.equal(axis.axisLabel?.formatter?.(2018), "2018");
    assert.equal(axis.minInterval, 1);
  }
  const citation = axesView("citation.v1");
  assert.equal(citation.xAxis.axisLabel?.formatter?.(2024), "2024");
  assert.equal(citation.yAxis.axisLabel?.formatter, undefined, "a count axis keeps the default number label");
});

test("value axes keep their line at the plot edge instead of the zero crossing", () => {
  for (const id of ["growth-quadrant.v1", "citation.v1"]) {
    const option = axesView(id);
    assert.equal(option.xAxis.axisLine?.onZero, false, id);
    assert.equal(option.yAxis.axisLine?.onZero, false, id);
  }
  for (const model of fixtures.models.filter(m => m.projection.kind === "bars")) {
    assert.equal(axesView(model.analysis_id).xAxis.axisLine?.onZero, false, model.analysis_id);
  }
});

test("record-count bar axes keep integer ticks", () => {
  for (const model of fixtures.models.filter(m => m.projection.kind === "bars")) {
    assert.equal(axesView(model.analysis_id).xAxis.minInterval, 1, model.analysis_id);
  }
});

test("heatmap x labels stay upright unless a displayed category is long", () => {
  for (const source of fixtures.models.filter(m => m.projection.kind === "heatmap")) {
    assert.equal(axesView(source.analysis_id).xAxis.axisLabel?.rotate, 0, source.analysis_id);
  }
  const model = structuredClone(fixtures.models.find(m => m.analysis_id === "cooccurrence.v1")!);
  if (model.projection.kind !== "heatmap") throw new Error("fixture");
  model.projection.x[0] = "長すぎる分類カテゴリ名";
  const tilted = buildAdvancedOption(model, fixtures.spec) as unknown as { xAxis: AxisView };
  assert.equal(tilted.xAxis.axisLabel?.rotate, 25);
});
