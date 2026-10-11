import assert from "node:assert/strict";
import { describe, test } from "vitest";
import { renderAdvancedModelToRawSvg } from "../src/advanced-index.js";
import type { AdvancedModel } from "../src/advanced-types.js";
import { validateAdvancedModel } from "../src/advanced-validation.js";
import { SPEC, heatmapProjection, inventorModel } from "./inventor-models.js";

type HeatmapProjection = ReturnType<typeof heatmapProjection>;
const base = () => inventorModel("inventor-technology.v1", heatmapProjection());
function mutate(change: (p: HeatmapProjection) => void): AdvancedModel {
  const model = base();
  change(model.projection as HeatmapProjection);
  return model;
}
const texts = (svg: string) => [...svg.matchAll(/<text\b[^>]*>([^<]*)<\/text>/gu)].map(match => match[1]!);
// A dashed stroked box (ECharts emits a dashed rectangle as a closed <path>) is the missing-cell mark.
const dashedRects = (svg: string) => (svg.match(/<path\b[^>]*stroke-dasharray="3 2"/gu) ?? []).length;

describe("inventor-heatmap validation", () => {
  test("accepts a complete grid containing an unknown cell without mutating it", () => {
    const model = base();
    const before = JSON.stringify(model);
    assert.equal(validateAdvancedModel(model), true);
    assert.equal(JSON.stringify(model), before);
  });
  const corruptions: [string, (p: HeatmapProjection) => void][] = [
    ["a missing cell", p => { p.cells.pop(); }],
    ["all cells missing", p => { p.cells = []; }],
    ["a duplicated cell", p => { p.cells[1] = { ...p.cells[0]! }; }],
    ["an extra cell", p => { p.cells.push({ ...p.cells[0]! }); }],
    ["a column index outside the axis", p => { p.cells[0]!.x = 3; }],
    ["a row index outside the axis", p => { p.cells[0]!.y = 2; }],
    ["a negative index", p => { p.cells[0]!.x = -1; }],
    ["a negative value", p => { p.cells[0]!.value = -0.5; }],
    ["a non finite value", p => { p.cells[0]!.value = Number.NaN; }],
    ["an infinite value", p => { p.cells[0]!.value = Number.POSITIVE_INFINITY; }],
    ["a string value", p => { (p.cells[0] as { value: unknown }).value = "1"; }],
    ["an undefined value", p => { delete (p.cells[0] as { value?: unknown }).value; }],
    ["an unknown cell key", p => { (p.cells[0] as Record<string, unknown>).share = 1; }],
    ["an unknown projection key", p => { (p as Record<string, unknown>).options = {}; }],
    ["a missing value label", p => { delete (p as Partial<HeatmapProjection>).value_label; }],
    ["21 columns", p => { p.x = Array.from({ length: 21 }, (_, i) => `F${i}`); p.cells = []; }],
    ["21 rows", p => { p.y = Array.from({ length: 21 }, (_, i) => `P${i}`); p.cells = []; }],
    ["cells without any axis", p => { p.x = []; p.y = []; }],
    ["an empty axis label", p => { p.x[0] = ""; }]
  ];
  for (const [name, change] of corruptions) {
    test(`rejects ${name} before rendering`, () => {
      const model = mutate(change);
      const before = JSON.stringify(model);
      assert.equal(validateAdvancedModel(model), false);
      assert.equal(JSON.stringify(model), before);
    });
  }
  test("accepts the 20 x 20 maximum and an empty population", () => {
    const full = mutate(p => {
      p.x = Array.from({ length: 20 }, (_, i) => `F${i}`);
      p.y = Array.from({ length: 20 }, (_, i) => `P${i}`);
      p.cells = p.y.flatMap((_, y) => p.x.map((__, x) => ({ x, y, value: x === y ? null : x + y })));
    });
    assert.equal(validateAdvancedModel(full), true);
    assert.equal(validateAdvancedModel(mutate(p => { p.x = []; p.y = []; p.cells = []; })), true);
  });
  test("rejects an incorrect mark, title, analysis or kind", () => {
    const wrongMark = base(); wrongMark.mark = "inventor-network-svg.v1";
    const wrongTitle = base(); wrongTitle.title = "共発明ネットワーク";
    const wrongAnalysis = base(); wrongAnalysis.analysis_id = "inventor-network.v1";
    const wrongKind = base(); wrongKind.projection = {
      kind: "inventor-scatter", x_label: "x", y_label: "y", size_label: "s", points: [], edges: [], unplottable: [], context: ""
    };
    for (const model of [wrongMark, wrongTitle, wrongAnalysis, wrongKind]) assert.equal(validateAdvancedModel(model), false);
  });
});

describe("inventor-heatmap rendering", () => {
  test("is deterministic, closed and keeps every label and raw value", () => {
    const model = base();
    const before = JSON.stringify(model);
    const first = renderAdvancedModelToRawSvg(model, SPEC);
    assert.equal(first, renderAdvancedModelToRawSvg(model, SPEC));
    assert.equal(JSON.stringify(model), before);
    assert.doesNotMatch(first, /<script\b|<foreignObject\b|<image\b|<a\b|href=|onload=/iu);
    const shown = texts(first);
    for (const label of ["Field A", "Field B", "Field C", "Alpha Person", "Beta Person", "技術分野", "発明者"]) {
      assert.ok(shown.includes(label), label);
    }
    // Values are shown as supplied (fractional, not rounded to integers or re-normalized).
    for (const value of ["12.5", "0.25", "0", "50", "37.25"]) assert.ok(shown.includes(value), value);
  });
  test("unknown is a distinct missing mark with its own legend, never zero", () => {
    const withUnknown = renderAdvancedModelToRawSvg(base(), SPEC);
    const allKnown = renderAdvancedModelToRawSvg(mutate(p => { p.cells[2]!.value = 0; }), SPEC);
    // One dashed missing cell plus one legend swatch; zero is an ordinary scale cell.
    assert.equal(dashedRects(withUnknown), 2);
    assert.equal(dashedRects(allKnown), 1);
    assert.ok(texts(withUnknown).some(text => text.includes("不明")));
    assert.equal(texts(withUnknown).filter(text => text === "0").length, texts(allKnown).filter(text => text === "0").length - 1);
  });
  test("numeric legend states the supplied value label and the real scale endpoints", () => {
    const shown = texts(renderAdvancedModelToRawSvg(base(), SPEC));
    assert.ok(shown.some(text => text.includes("構成比 (%)")));
    assert.ok(shown.includes("50"), "legend maximum is the data maximum, not a generic integer bucket");
    const small = texts(renderAdvancedModelToRawSvg(mutate(p => {
      p.cells.forEach(cell => { if (cell.value !== null) cell.value = cell.value / 100; });
    }), SPEC));
    assert.ok(small.includes("0.5"), "fractional maxima keep fractional precision");
  });
  test("an all-zero or all-unknown grid still renders without a divide by zero", () => {
    for (const change of [
      (p: HeatmapProjection) => p.cells.forEach(cell => { cell.value = 0; }),
      (p: HeatmapProjection) => p.cells.forEach(cell => { cell.value = null; })
    ]) {
      const svg = renderAdvancedModelToRawSvg(mutate(change), SPEC);
      assert.doesNotMatch(svg, /NaN|Infinity/u);
    }
  });
  test("labels render as inert text", () => {
    const model = mutate(p => { p.x[0] = '{a}<i>"&'; p.y[0] = "<b>x</b>"; });
    assert.equal(validateAdvancedModel(model), true);
    const svg = renderAdvancedModelToRawSvg(model, SPEC);
    assert.ok(svg.includes("{a}&lt;i&gt;"));
    assert.ok(svg.includes("&lt;b&gt;x&lt;/b&gt;"));
    assert.doesNotMatch(svg, /<script\b|<b>|<i>/iu);
  });
  test("empty grid renders a bounded notice", () => {
    const svg = renderAdvancedModelToRawSvg(mutate(p => { p.x = []; p.y = []; p.cells = []; }), SPEC);
    assert.ok(svg.includes("対象データなし"));
  });
  test("full 20 x 20 grid renders within the text budget", () => {
    const model = mutate(p => {
      p.x = Array.from({ length: 20 }, (_, i) => `Field ${i}`);
      p.y = Array.from({ length: 20 }, (_, i) => `Person ${i}`);
      p.cells = p.y.flatMap((_, y) => p.x.map((__, x) => ({ x, y, value: (x * 7 + y) % 5 === 0 ? null : x * 0.5 + y })));
    });
    assert.equal(validateAdvancedModel(model), true);
    assert.ok(renderAdvancedModelToRawSvg(model, SPEC).length > 0);
  });
});
