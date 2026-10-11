import assert from "node:assert/strict";
import { describe, test } from "vitest";
import { renderAdvancedModelToRawSvg } from "../src/advanced-index.js";
import type { AdvancedModel } from "../src/advanced-types.js";
import { validateAdvancedModel } from "../src/advanced-validation.js";
import { SPEC, egoProjection, flowProjection, inventorModel, networkProjection } from "./inventor-models.js";

type NetworkProjection = ReturnType<typeof networkProjection>;
const valid = {
  "inventor-network.v1": () => inventorModel("inventor-network.v1", networkProjection()),
  "inventor-ego-network.v1": () => inventorModel("inventor-ego-network.v1", egoProjection()),
  "inventor-mobility-flow.v1": () => inventorModel("inventor-mobility-flow.v1", flowProjection())
} as const;
function mutate(id: keyof typeof valid, change: (p: NetworkProjection) => void): AdvancedModel {
  const model = valid[id]();
  change(model.projection as NetworkProjection);
  return model;
}
const circles = (svg: string) => [...svg.matchAll(/<circle\b[^>]*>/gu)].map(match => match[0]);
// ECharts paints graphic lines as <path>; a stroke-only path with fill="none" is an edge or legend line.
const edgePaths = (svg: string) => [...svg.matchAll(/<path\b[^>]*fill="none"[^>]*stroke="#[0-9a-f]{6}"[^>]*>/gu)]
  .map(match => match[0]);
const attribute = (tag: string, name: string) => new RegExp(`\\b${name}="([^"]*)"`, "u").exec(tag)?.[1];
const count = (svg: string, tag: string) => svg.match(new RegExp(`<${tag}\\b`, "gu"))?.length ?? 0;

describe("inventor-network validation", () => {
  for (const id of Object.keys(valid) as (keyof typeof valid)[]) {
    test(`${id} accepts a complete synthetic model without mutation`, () => {
      const model = valid[id]();
      const before = JSON.stringify(model);
      assert.equal(validateAdvancedModel(model), true);
      assert.equal(JSON.stringify(model), before);
    });
  }
  const corruptions: [string, keyof typeof valid, (p: NetworkProjection) => void][] = [
    ["duplicate node id", "inventor-network.v1", p => { p.nodes[1]!.id = p.nodes[0]!.id; }],
    ["edge index out of range", "inventor-network.v1", p => { p.edges[0]!.target = 4; }],
    ["negative edge index", "inventor-network.v1", p => { p.edges[0]!.source = -1; }],
    ["self loop", "inventor-network.v1", p => { p.edges[0]!.target = p.edges[0]!.source; }],
    ["reversed duplicate undirected edge", "inventor-network.v1", p => {
      p.edges.push({ ...p.edges[0]!, source: p.edges[0]!.target, target: p.edges[0]!.source });
    }],
    ["undirected edge colliding with a directed edge", "inventor-network.v1", p => {
      p.edges.push({ ...p.edges[0]!, directed: true });
    }],
    ["exact duplicate directed edge", "inventor-mobility-flow.v1", p => { p.edges.push({ ...p.edges[0]! }); }],
    ["focus that is not a node id", "inventor-ego-network.v1", p => { p.focus = "missing"; }],
    ["ego map without focus", "inventor-ego-network.v1", p => { p.focus = null; }],
    ["undirected company flow", "inventor-mobility-flow.v1", p => { p.edges[1]!.directed = false; }],
    ["hop above three", "inventor-network.v1", p => { p.nodes[0]!.hop = 4; }],
    ["fractional hop", "inventor-network.v1", p => { p.nodes[0]!.hop = 1.5; }],
    ["group above 199", "inventor-network.v1", p => { p.nodes[0]!.group = 200; }],
    ["negative node value", "inventor-network.v1", p => { p.nodes[0]!.value = -1; }],
    ["negative edge value", "inventor-network.v1", p => { p.edges[0]!.value = -1; }],
    ["non finite coordinate", "inventor-network.v1", p => { p.nodes[0]!.x = Number.NaN; }],
    ["infinite coordinate", "inventor-network.v1", p => { p.nodes[0]!.y = Number.POSITIVE_INFINITY; }],
    ["unknown edge state", "inventor-network.v1", p => { (p.edges[0] as { state: string }).state = "guessed"; }],
    ["unknown node key", "inventor-network.v1", p => { (p.nodes[0] as Record<string, unknown>).options = {}; }],
    ["unknown edge key", "inventor-network.v1", p => { (p.edges[0] as Record<string, unknown>).url = "x"; }],
    ["unknown projection key", "inventor-network.v1", p => { (p as Record<string, unknown>).options = {}; }],
    ["missing context", "inventor-network.v1", p => { delete (p as Partial<NetworkProjection>).context; }],
    ["41 display nodes", "inventor-network.v1", p => {
      p.nodes = Array.from({ length: 41 }, (_, i) => ({ ...p.nodes[0]!, id: `n${i}`, label: `Person ${i}` }));
      p.edges = [];
    }],
    ["301 display edges", "inventor-mobility-flow.v1", p => {
      p.edges = Array.from({ length: 301 }, () => ({ ...p.edges[0]! }));
    }],
    ["unsafe bidirectional label", "inventor-network.v1", p => { p.nodes[0]!.label = "A‮B"; }]
  ];
  for (const [name, id, change] of corruptions) {
    test(`rejects ${name} before rendering`, () => {
      const model = mutate(id, change);
      const before = JSON.stringify(model);
      assert.equal(validateAdvancedModel(model), false);
      assert.equal(JSON.stringify(model), before);
    });
  }
  test("accepts the maximum 40 nodes and an isolated node set", () => {
    const model = mutate("inventor-network.v1", p => {
      p.nodes = Array.from({ length: 40 }, (_, i) => ({ ...p.nodes[0]!, id: `n${i}`, label: `Person ${i}` }));
      p.edges = [];
    });
    assert.equal(validateAdvancedModel(model), true);
  });
  test("accepts an opposite pair of directed edges as two distinct relations", () => {
    assert.equal(validateAdvancedModel(valid["inventor-mobility-flow.v1"]()), true);
  });
});

describe("inventor-network mark, title and kind mapping", () => {
  test("rejects an incorrect mark, title or kind for each network analysis", () => {
    for (const id of Object.keys(valid) as (keyof typeof valid)[]) {
      const wrongMark = valid[id](); wrongMark.mark = "inventor-tracking-svg.v1";
      const wrongTitle = valid[id](); wrongTitle.title = "発明者の活動履歴";
      const wrongKind = valid[id](); wrongKind.projection = {
        kind: "inventor-heatmap", x: [], y: [], x_label: "x", y_label: "y", value_label: "v", cells: [], context: ""
      };
      const wrongAnalysis = valid[id](); wrongAnalysis.analysis_id = "inventor-activity.v1";
      for (const model of [wrongMark, wrongTitle, wrongKind, wrongAnalysis]) {
        assert.equal(validateAdvancedModel(model), false, `${id} ${JSON.stringify(model.mark)}`);
      }
    }
  });
});

describe("inventor-network rendering", () => {
  test("is deterministic, closed and shows every node including the isolated one", () => {
    const model = valid["inventor-network.v1"]();
    const before = JSON.stringify(model);
    const first = renderAdvancedModelToRawSvg(model, SPEC);
    assert.equal(first, renderAdvancedModelToRawSvg(model, SPEC));
    assert.equal(JSON.stringify(model), before);
    assert.match(first, /^<svg\b/u);
    assert.doesNotMatch(first, /<script\b|<foreignObject\b|<image\b|<a\b|href=|onload=/iu);
    for (const node of model.projection.kind === "inventor-network" ? model.projection.nodes : []) {
      assert.ok(first.includes(`>${node.label}<`), node.label);
    }
  });
  test("uses a fixed node area scale: radius grows with the square root of value", () => {
    const svg = renderAdvancedModelToRawSvg(valid["inventor-network.v1"](), SPEC);
    const radii = circles(svg).map(tag => Number(/\br="([0-9.]+)"/u.exec(tag)?.[1]));
    // Nodes are drawn first, in input order: 9, 4, 1; the known zero (0) is a cross, not a disk. r = 20 * sqrt(v / 9).
    assert.deepEqual(radii.slice(0, 3), [20, 13.3, 6.7]);
    assert.equal(radii[3], 5, "the next circle is the first community legend swatch");
  });
  test("edge line width follows value on a fixed 1..5 px scale", () => {
    const svg = renderAdvancedModelToRawSvg(valid["inventor-network.v1"](), SPEC);
    // Edges are the first paths, in input order, before any node is painted: values 3, 1, 2 of max 3.
    assert.deepEqual(edgePaths(svg).slice(0, 3).map(tag => attribute(tag, "stroke-width")), ["5", "2.33", "3.67"]);
  });
  test("directed edges draw arrowheads; undirected ones do not", () => {
    const directed = valid["inventor-mobility-flow.v1"]();
    const undirected = valid["inventor-mobility-flow.v1"]();
    (undirected.projection as NetworkProjection).edges.forEach(edge => { edge.directed = false; });
    const withArrows = count(renderAdvancedModelToRawSvg(directed, SPEC), "polygon");
    // The undirected rendition is not a valid M09 model, but the renderer must still not invent arrows.
    const withoutArrows = count(renderAdvancedModelToRawSvg(undirected, SPEC), "polygon");
    assert.equal(withArrows - withoutArrows, 3);
  });
  test("focus is distinguished by a border and still draws the same nodes", () => {
    const plain = renderAdvancedModelToRawSvg(valid["inventor-network.v1"](), SPEC);
    const ego = renderAdvancedModelToRawSvg(valid["inventor-ego-network.v1"](), SPEC);
    assert.notEqual(plain, ego);
    assert.equal(circles(plain).length, circles(ego).length);
    const borders = (svg: string) => circles(svg).map(tag => /stroke-width="([0-9.]+)"/u.exec(tag)?.[1]);
    // Three disks: the zero-valued fourth node is a cross glyph and no longer a circle.
    assert.equal(new Set(borders(plain).slice(0, 3)).size, 1);
    assert.equal(new Set(borders(ego).slice(0, 3)).size, 2);
  });
  test("edge status uses distinct dash patterns and a legend explains them", () => {
    const svg = renderAdvancedModelToRawSvg(valid["inventor-network.v1"](), SPEC);
    const [observed, inferred, confirmed] = edgePaths(svg).slice(0, 3);
    assert.equal(attribute(observed!, "stroke-dasharray"), undefined);
    assert.equal(attribute(inferred!, "stroke-dasharray"), "6 4", "inferred edges must be dashed");
    assert.equal(attribute(confirmed!, "stroke-dasharray"), undefined);
    assert.notEqual(attribute(confirmed!, "stroke"), attribute(observed!, "stroke"));
    assert.ok(count(svg, "polygon") >= 1, "confirmed edges carry a distinct symbol");
    for (const text of ["観測", "推定", "確認", "コミュニティ", "レイアウト"]) assert.ok(svg.includes(text), text);
  });
  test("labels render as inert text", () => {
    const model = mutate("inventor-network.v1", p => { p.nodes[0]!.label = '{a}<script>"&'; });
    assert.equal(validateAdvancedModel(model), true);
    const svg = renderAdvancedModelToRawSvg(model, SPEC);
    assert.ok(svg.includes("{a}&lt;script&gt;"));
    assert.doesNotMatch(svg, /<script\b/iu);
  });
  test("empty network renders a bounded notice", () => {
    const model = mutate("inventor-network.v1", p => { p.nodes = []; p.edges = []; });
    assert.equal(validateAdvancedModel(model), true);
    assert.ok(renderAdvancedModelToRawSvg(model, SPEC).includes("対象データなし"));
  });
  test("supplied coordinates are preserved up to one uniform scale", () => {
    const svg = renderAdvancedModelToRawSvg(valid["inventor-network.v1"](), SPEC);
    const [a, b, c] = circles(svg).map(tag => [Number(/\bcx="(-?[0-9.]+)"/u.exec(tag)![1]), Number(/\bcy="(-?[0-9.]+)"/u.exec(tag)![1])]);
    // Source deltas a->b = (13, 4) and b->c = (9, -14): ratios must survive a uniform scale.
    const scaleX = (b![0]! - a![0]!) / 13, scaleY = (b![1]! - a![1]!) / 4;
    assert.ok(Math.abs(scaleX - scaleY) < 0.02, `${scaleX} ${scaleY}`);
    assert.ok(Math.abs((c![0]! - b![0]!) / 9 - scaleX) < 0.02);
  });
});
