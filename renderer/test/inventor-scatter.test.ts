import assert from "node:assert/strict";
import { describe, test } from "vitest";
import { renderAdvancedModelToRawSvg } from "../src/advanced-index.js";
import type { AdvancedModel } from "../src/advanced-types.js";
import { validateAdvancedModel } from "../src/advanced-validation.js";
import { SPEC, inventorModel, scatterProjection } from "./inventor-models.js";

type ScatterProjection = ReturnType<typeof scatterProjection>;
const valid = {
  "inventor-similarity.v1": () => inventorModel("inventor-similarity.v1", scatterProjection()),
  "inventor-impact.v1": () => inventorModel("inventor-impact.v1", scatterProjection())
} as const;
const base = valid["inventor-impact.v1"];
function mutate(id: keyof typeof valid, change: (p: ScatterProjection) => void): AdvancedModel {
  const model = valid[id]();
  change(model.projection as ScatterProjection);
  return model;
}
const texts = (svg: string) => [...svg.matchAll(/<text\b[^>]*>([^<]*)<\/text>/gu)].map(match => match[1]!);
const tags = (svg: string, name: string) => svg.match(new RegExp(`<${name}\\b[^>]*>`, "gu")) ?? [];
const attribute = (tag: string, name: string) => new RegExp(`\\b${name}="([^"]*)"`, "u").exec(tag)?.[1];
const edit = (change: (p: ScatterProjection) => void) => mutate("inventor-impact.v1", change);

describe("inventor-scatter validation", () => {
  for (const id of Object.keys(valid) as (keyof typeof valid)[]) {
    test(`${id} accepts a complete synthetic model without mutation`, () => {
      const model = valid[id]();
      const before = JSON.stringify(model);
      assert.equal(validateAdvancedModel(model), true);
      assert.equal(JSON.stringify(model), before);
    });
  }
  const corruptions: [string, (p: ScatterProjection) => void][] = [
    ["a duplicate point id", p => { p.points[1]!.id = p.points[0]!.id; }],
    ["an id shared by a plotted and an unplottable entry", p => { p.unplottable[0]!.id = p.points[0]!.id; }],
    ["a duplicate unplottable id", p => { p.unplottable.push({ ...p.unplottable[0]! }); }],
    ["an edge source out of range", p => { p.edges[0]!.source = 3; }],
    ["an edge target out of range", p => { p.edges[0]!.target = 3; }],
    ["a negative edge index", p => { p.edges[0]!.source = -1; }],
    ["a self loop", p => { p.edges[0]!.target = p.edges[0]!.source; }],
    ["a duplicate edge", p => { p.edges.push({ ...p.edges[0]! }); }],
    ["a reversed duplicate edge", p => { p.edges.push({ ...p.edges[0]!, source: p.edges[0]!.target, target: p.edges[0]!.source }); }],
    ["a negative edge value", p => { p.edges[0]!.value = -1; }],
    ["a negative size", p => { p.points[0]!.size = -1; }],
    ["a non finite x", p => { p.points[0]!.x = Number.NaN; }],
    ["an infinite y", p => { p.points[0]!.y = Number.NEGATIVE_INFINITY; }],
    ["a missing coordinate", p => { delete (p.points[0] as { x?: number }).x; }],
    ["a null coordinate", p => { (p.points[0] as { y: unknown }).y = null; }],
    ["an empty category", p => { p.points[0]!.category = ""; }],
    ["an over long category", p => { p.points[0]!.category = "c".repeat(65); }],
    ["an unknown point key", p => { (p.points[0] as Record<string, unknown>).url = "x"; }],
    ["an unknown edge key", p => { (p.edges[0] as Record<string, unknown>).directed = true; }],
    ["an unknown unplottable key", p => { (p.unplottable[0] as Record<string, unknown>).value = 0; }],
    ["an unknown projection key", p => { (p as Record<string, unknown>).options = {}; }],
    ["an unplottable entry without a reason", p => { delete (p.unplottable[0] as { reason?: string }).reason; }],
    ["41 points", p => {
      p.points = Array.from({ length: 41 }, (_, i) => ({ ...p.points[0]!, id: `p${i}`, label: `P${i}` })); p.edges = [];
    }],
    ["301 edges", p => {
      p.points = Array.from({ length: 40 }, (_, i) => ({ ...p.points[0]!, id: `p${i}`, label: `P${i}` }));
      p.edges = Array.from({ length: 301 }, (_, i) => ({ source: i % 39, target: 39, value: 1 }));
    }],
    ["201 unplottable entries", p => {
      p.unplottable = Array.from({ length: 201 }, (_, i) => ({ id: `u${i}`, label: `U${i}`, reason: "r" }));
    }]
  ];
  for (const [name, change] of corruptions) {
    test(`rejects ${name} before rendering`, () => {
      const model = edit(change);
      const before = JSON.stringify(model);
      assert.equal(validateAdvancedModel(model), false);
      assert.equal(JSON.stringify(model), before);
    });
  }
  test("accepts the maxima, a disabled overlay and an empty projection", () => {
    assert.equal(validateAdvancedModel(edit(p => {
      p.points = Array.from({ length: 40 }, (_, i) => ({ ...p.points[0]!, id: `p${i}`, label: `P${i}`, x: i, y: i % 7 }));
      p.edges = Array.from({ length: 300 }, (_, i) => ({ source: i % 20, target: 20 + Math.floor(i / 20), value: 1 }));
      p.unplottable = Array.from({ length: 200 }, (_, i) => ({ id: `u${i}`, label: `U${i}`, reason: "r" }));
    })), true);
    assert.equal(validateAdvancedModel(edit(p => { p.edges = []; })), true);
    assert.equal(validateAdvancedModel(edit(p => { p.points = []; p.edges = []; p.unplottable = []; })), true);
  });
  test("keeps a missing impact out of the plotted points", () => {
    assert.equal(validateAdvancedModel(edit(p => { p.points = []; p.edges = []; })), true);
  });
  test("rejects an incorrect mark, title, analysis or kind for both analyses", () => {
    for (const id of Object.keys(valid) as (keyof typeof valid)[]) {
      const wrongMark = valid[id](); wrongMark.mark = "inventor-technology-svg.v1";
      const wrongTitle = valid[id](); wrongTitle.title = "共発明ネットワーク";
      const wrongAnalysis = valid[id](); wrongAnalysis.analysis_id = "inventor-technology.v1";
      const swapped = valid[id](); swapped.mark = id === "inventor-impact.v1" ? "inventor-similarity-svg.v1" : "inventor-impact-svg.v1";
      const swappedTitle = valid[id](); swappedTitle.title = id === "inventor-impact.v1" ? "発明者の技術類似度" : "発明者の活動量と引用指標";
      const wrongKind = valid[id](); wrongKind.projection = {
        kind: "inventor-heatmap", x: [], y: [], x_label: "x", y_label: "y", value_label: "v", cells: [], context: ""
      };
      for (const model of [wrongMark, wrongTitle, wrongAnalysis, swapped, swappedTitle, wrongKind]) {
        assert.equal(validateAdvancedModel(model), false, id);
      }
    }
  });
});

describe("inventor-scatter rendering", () => {
  test("is deterministic, closed, and shows axis names, labels and the unplottable captions", () => {
    const model = base();
    const before = JSON.stringify(model);
    const first = renderAdvancedModelToRawSvg(model, SPEC);
    assert.equal(first, renderAdvancedModelToRawSvg(model, SPEC));
    assert.equal(JSON.stringify(model), before);
    assert.doesNotMatch(first, /<script\b|<foreignObject\b|<image\b|<a\b|href=|onload=/iu);
    const shown = texts(first);
    for (const label of ["第1軸", "第2軸", "Alpha Person", "Beta Person", "Gamma Person"]) assert.ok(shown.includes(label), label);
    assert.ok(shown.some(text => text.includes("活動量")), "size label is explained");
  });
  test("area scaling is fixed: radius follows the square root of size", () => {
    const svg = renderAdvancedModelToRawSvg(base(), SPEC);
    // Sizes 9, 4, 0: r = 20 * sqrt(size / 9). The zero point is a cross, so the third circle is a legend swatch (r=5).
    assert.deepEqual(tags(svg, "circle").slice(0, 3).map(tag => attribute(tag, "r")), ["20", "13.3", "5"]);
  });
  test("a missing value is counted in a caption and never plotted as zero", () => {
    const withMissing = renderAdvancedModelToRawSvg(base(), SPEC);
    const without = renderAdvancedModelToRawSvg(edit(p => { p.unplottable = []; }), SPEC);
    assert.equal(tags(withMissing, "circle").length, tags(without, "circle").length, "no point is drawn for it");
    const shown = texts(withMissing);
    assert.ok(shown.some(text => /未定義.*1件/u.test(text)), "the count is captioned");
    assert.ok(shown.some(text => text.includes("Delta Person") && text.includes("引用指標が未定義")));
    assert.ok(texts(without).some(text => /未定義.*0件/u.test(text)), "zero is captioned too");
  });
  test("many unplottable entries are summarised without growing past the page", () => {
    const model = edit(p => {
      p.unplottable = Array.from({ length: 200 }, (_, i) => ({ id: `u${i}`, label: `Person ${i}`, reason: "r" }));
    });
    const shown = texts(renderAdvancedModelToRawSvg(model, SPEC));
    assert.ok(shown.some(text => /未定義.*200件/u.test(text)));
    assert.ok(shown.some(text => text.includes("ほか")));
    assert.ok(!shown.includes("Person 199: r"));
  });
  test("the co-invention overlay is drawn only when supplied", () => {
    const withEdges = renderAdvancedModelToRawSvg(base(), SPEC);
    const without = renderAdvancedModelToRawSvg(edit(p => { p.edges = []; }), SPEC);
    const edgePaths = (svg: string) => tags(svg, "path").filter(tag => attribute(tag, "stroke") === "#94a3b8" && attribute(tag, "fill") === "none");
    // Two overlay lines plus the legend key line.
    assert.equal(edgePaths(withEdges).length - edgePaths(without).length, 3);
    assert.ok(texts(withEdges).some(text => text.includes("共発明")));
    assert.ok(!texts(without).some(text => text.includes("共発明")));
  });
  test("a fixed palette colours categories and the legend names them", () => {
    const svg = renderAdvancedModelToRawSvg(base(), SPEC);
    // Two plotted disks (the zero point is a cross), then the legend swatch of the first category, cluster-a.
    const fills = tags(svg, "circle").slice(0, 3).map(tag => attribute(tag, "fill"));
    assert.equal(fills[0], fills[2], "same category, same colour");
    assert.notEqual(fills[0], fills[1]);
    const shown = texts(svg);
    assert.ok(shown.includes("cluster-a") && shown.includes("cluster-b"));
  });
  test("makes no interactive promise and keeps the display offset caveat", () => {
    const shown = texts(renderAdvancedModelToRawSvg(base(), SPEC));
    assert.ok(shown.some(text => text.includes("表示上のずれ")), "overlap offsets are disclosed");
    assert.ok(!shown.some(text => /クリック|ホバー|ツールチップ|拡大/u.test(text)));
  });
  test("a single point and identical coordinates render without a degenerate scale", () => {
    for (const change of [
      (p: ScatterProjection) => { p.points = p.points.slice(0, 1); p.edges = []; },
      (p: ScatterProjection) => { p.points.forEach(point => { point.x = 1; point.y = 1; }); }
    ]) {
      assert.doesNotMatch(renderAdvancedModelToRawSvg(edit(change), SPEC), /NaN|Infinity/u);
    }
  });
  test("labels render as inert text", () => {
    const model = edit(p => {
      p.points[0]!.label = '{a}<i>"&'; p.points[0]!.category = "<b>c</b>"; p.unplottable[0]!.reason = "<u>r</u>";
    });
    assert.equal(validateAdvancedModel(model), true);
    const svg = renderAdvancedModelToRawSvg(model, SPEC);
    for (const escaped of ["{a}&lt;i&gt;", "&lt;b&gt;c&lt;/b&gt;", "&lt;u&gt;r&lt;/u&gt;"]) assert.ok(svg.includes(escaped), escaped);
    assert.doesNotMatch(svg, /<script\b|<b>|<i>|<u>/iu);
  });
  test("empty scatter renders a bounded notice", () => {
    const svg = renderAdvancedModelToRawSvg(edit(p => { p.points = []; p.edges = []; p.unplottable = []; }), SPEC);
    assert.ok(svg.includes("対象データなし"));
  });
  test("the 40 point, 300 edge, 200 unplottable maximum stays inside the SVG budgets", () => {
    const model = edit(p => {
      p.points = Array.from({ length: 40 }, (_, i) => ({ id: `p${i}`, label: `Person ${i}`, x: i * 1.5, y: (i * 7) % 11, size: i, category: `c${i % 12}` }));
      p.edges = Array.from({ length: 300 }, (_, i) => ({ source: i % 20, target: 20 + Math.floor(i / 20), value: 1 + (i % 5) }));
      p.unplottable = Array.from({ length: 200 }, (_, i) => ({ id: `u${i}`, label: `Missing ${i}`, reason: "undefined" }));
    });
    assert.equal(validateAdvancedModel(model), true);
    assert.ok(renderAdvancedModelToRawSvg(model, SPEC).length > 0);
  });
});
