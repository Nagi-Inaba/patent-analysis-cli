import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "vitest";
import { renderAdvancedModelToRawSvg } from "../src/advanced-index.js";
import { buildNetwork } from "../src/advanced-inventor-network.js";
import { buildTimeline } from "../src/advanced-inventor-timeline.js";
import * as echarts from "echarts/core";
import { validateAdvancedModel } from "../src/advanced-validation.js";
import type { InventorScatterProjection, InventorTimelineProjection } from "../src/advanced-types.js";
import { SPEC, inventorModel, networkProjection, timelineProjection } from "./inventor-models.js";

// Captured from actual P1 annual_activity/citation_metrics then Python project_advanced_data.
const real = JSON.parse(readFileSync(new URL("./inventor-boundary-projections.json", import.meta.url), "utf8")) as {
  positive: InventorScatterProjection; unknown: InventorTimelineProjection;
};
const tags = (svg: string, type: string) => svg.match(new RegExp(`<${type}\\b[^>]*>`, "gu")) ?? [];
const attr = (tag: string, name: string) => new RegExp(`\\b${name}="([^"]*)"`, "u").exec(tag)?.[1];
const numbers = (text: string) => (text.match(/-?\d+(?:\.\d+)?/gu) ?? []).map(Number);
const crossStrokes = (svg: string) => tags(svg, "path").filter(tag => {
  const n = numbers(attr(tag, "d") ?? "");
  return attr(tag, "fill") === "none" && n.length === 4
    && Math.abs(n[2]! - n[0]!) === 8 && Math.abs(n[3]! - n[1]!) === 8;
});

type BoundaryElement = { type: string; shape: Record<string, number> & { points?: number[][] };
  style: { fill?: string; stroke?: string; lineWidth?: number; lineDash?: number[] } };

test("ordinary diagonal network edges and arrow tips reach the tiny-positive square boundary", () => {
  for (const directed of [false, true]) for (const reverse of [false, true]) {
    const p = networkProjection();
    p.nodes = [
      { id: "small", label: "Small", x: 0, y: 0, value: 1, group: 0, hop: null },
      { id: "large", label: "Large", x: 1, y: 1, value: 100000000, group: 1, hop: null }
    ];
    p.edges = [{ source: reverse ? 0 : 1, target: reverse ? 1 : 0, value: 1, directed, state: "inferred" }];
    const model = inventorModel(directed ? "inventor-mobility-flow.v1" : "inventor-network.v1", p);
    assert.equal(validateAdvancedModel(model), true);
    const before = JSON.stringify(model);
    const option = buildNetwork(model, SPEC, p) as { graphic: { elements: BoundaryElement[] } };
    const elements = option.graphic.elements;
    const square = elements.find(e => e.type === "rect" && e.shape.width === 6 && e.style.fill === "none")!.shape;
    const edge = elements.find(e => e.type === "line")!;
    const endpoint = reverse ? [edge.shape.x1!, edge.shape.y1!] : [edge.shape.x2!, edge.shape.y2!];
    const extent = Math.max(Math.abs(endpoint[0]! - square.x! - 3), Math.abs(endpoint[1]! - square.y! - 3));
    assert.ok(Math.abs(extent - 3) < 0.02, `square endpoint extent ${extent} must equal half-size 3`);
    assert.deepEqual(edge.style.lineDash, [6, 4]);
    if (directed) {
      const arrow = elements.find(e => e.type === "polygon")!.shape.points!;
      assert.deepEqual(arrow[0], [edge.shape.x2, edge.shape.y2]);
    }
    assert.doesNotMatch(renderAdvancedModelToRawSvg(model, SPEC), /NaN|Infinity/u);
    assert.equal(JSON.stringify(model), before);
  }
});

test("diagonal timeline links reach the tiny-positive square boundary in either direction", () => {
  for (const reverse of [false, true]) {
    const p = timelineProjection(false);
    p.years = Array.from({ length: 15 }, (_, i) => 2020 + i);
    p.lanes = ["A", "B"]; p.bands = [];
    p.nodes = [
      { id: "small", label: "Small", x: 2020, y: 0, size: 1, category: 0, state: "observed" },
      { id: "large", label: "Large", x: 2021, y: 1, size: 100000000, category: 1, state: "observed" }
    ];
    p.links = [{ source: reverse ? 0 : 1, target: reverse ? 1 : 0, gap: true, state: "inferred" }];
    const model = inventorModel("inventor-activity.v1", p);
    assert.equal(validateAdvancedModel(model), true);
    const before = JSON.stringify(model);
    const option = buildTimeline(model, SPEC, p) as { graphic: { elements: BoundaryElement[] } };
    const elements = option.graphic.elements;
    const square = elements.find(e => e.type === "rect" && e.shape.width === 6 && e.style.fill === "none")!.shape;
    const link = elements.find(e => e.type === "line" && e.style.stroke === "#64748b" && e.style.lineWidth === 2)!;
    const endpoint = reverse ? [link.shape.x1!, link.shape.y1!] : [link.shape.x2!, link.shape.y2!];
    const extent = Math.max(Math.abs(endpoint[0]! - square.x! - 3), Math.abs(endpoint[1]! - square.y! - 3));
    assert.ok(Math.abs(extent - 3) < 0.02, `square endpoint extent ${extent} must equal half-size 3`);
    assert.deepEqual(link.style.lineDash, [6, 4]);
    assert.doesNotMatch(renderAdvancedModelToRawSvg(model, SPEC), /NaN|Infinity/u);
    assert.equal(JSON.stringify(model), before);
  }
});

test("coincident tiny-positive linked markers retain finite SVG geometry", () => {
  const network = networkProjection();
  network.nodes = [
    { id: "small", label: "Small", x: 0, y: 0, value: 1, group: 0, hop: null },
    { id: "large", label: "Large", x: 0, y: 0, value: 100000000, group: 1, hop: null }
  ];
  network.edges = [{ source: 1, target: 0, value: 1, directed: true, state: "observed" }];
  const timeline = timelineProjection(false);
  timeline.years = [2020]; timeline.lanes = ["A"]; timeline.bands = [];
  timeline.nodes = [
    { id: "small", label: "Small", x: 2020, y: 0, size: 1, category: 0, state: "observed" },
    { id: "large", label: "Large", x: 2020, y: 0, size: 100000000, category: 1, state: "observed" }
  ];
  timeline.links = [{ source: 1, target: 0, gap: false, state: "observed" }];
  for (const model of [inventorModel("inventor-mobility-flow.v1", network),
    inventorModel("inventor-activity.v1", timeline)]) {
    assert.equal(validateAdvancedModel(model), true);
    const finiteGeometry = (value: unknown): void => {
      if (typeof value === "number") assert.ok(Number.isFinite(value), `nonfinite geometry ${value}`);
      else if (value !== null && typeof value === "object") Object.values(value).forEach(finiteGeometry);
    };
    const option = (model.analysis_id === "inventor-mobility-flow.v1"
      ? buildNetwork(model, SPEC, network) : buildTimeline(model, SPEC, timeline)) as {
        graphic: { elements: BoundaryElement[] } };
    finiteGeometry(option);
    const center = option.graphic.elements.find(e => e.type === "rect" && e.shape.width === 6)!.shape;
    const stroke = option.graphic.elements.find(e => e.type === "line" && e.style.stroke === "#64748b")!.shape;
    assert.deepEqual([stroke.x1, stroke.y1, stroke.x2, stroke.y2],
      [center.x! + 3, center.y! + 3, center.x! + 3, center.y! + 3], "coincident links stay at marker centers");
    assert.doesNotMatch(renderAdvancedModelToRawSvg(model, SPEC), /NaN|Infinity/u);
  }
});

test("coincident reciprocal square markers keep every endpoint at the marker center", () => {
  for (const values of [[1, 2], [1, 100000000], [100000000, 1]]) {
    for (const reverse of [false, true]) {
      const p = networkProjection();
      p.nodes = values.concat(100000000).map((value, index) => ({
        id: `node-${index}`, label: `Node ${index}`, x: 0, y: 0, value, group: index, hop: null
      }));
      p.edges = [
        { source: 0, target: 1, value: 1, directed: true, state: "observed" },
        { source: 1, target: 0, value: 1, directed: true, state: "inferred" }
      ];
      if (reverse) p.edges.reverse();
      const model = inventorModel("inventor-mobility-flow.v1", p);
      assert.equal(validateAdvancedModel(model), true);
      const before = JSON.stringify(model);
      const option = buildNetwork(model, SPEC, p) as { graphic: { elements: BoundaryElement[] } };
      const elements = option.graphic.elements;
      const square = elements.find(e => e.type === "rect" && e.shape.width === 6)!.shape;
      const center = [square.x! + 3, square.y! + 3];
      const strokes = elements.filter(e => e.type === "polyline");
      assert.equal(strokes.length, 2);
      for (const [i, edge] of p.edges.entries()) {
        const points = strokes[i]!.shape.points!;
        for (const point of points) assert.deepEqual(point, center, "coincident reciprocal path stays at its marker center");
        assert.deepEqual(strokes[i]!.style.lineDash, edge.state === "inferred" ? [6, 4] : undefined);
      }
      const arrows = elements.filter(e => e.type === "polygon").slice(0, 2);
      for (const arrow of arrows) assert.deepEqual(arrow.shape.points![0], center);
      assert.doesNotMatch(renderAdvancedModelToRawSvg(model, SPEC), /NaN|Infinity/u);
      assert.equal(JSON.stringify(model), before);
    }
  }
});

for (const maximum of [100000000, 1000000000000]) {
  test(`positive activity at size ratio 1:${maximum} never uses a known-zero cross in any kind`, () => {
    const scatter = structuredClone(real.positive);
    scatter.points[1]!.size = maximum;
    const network = networkProjection();
    network.nodes = [
      { id: "a", label: "A", x: -5, y: 0, value: 1, group: 0, hop: null },
      { id: "b", label: "B", x: 5, y: 0, value: maximum, group: 0, hop: null }
    ];
    network.edges = [];
    const timeline = timelineProjection(false);
    timeline.lanes = ["A"]; timeline.years = [2020, 2021]; timeline.links = []; timeline.bands = [];
    timeline.nodes = [
      { id: "a", x: 2020, y: 0, size: 1, category: 0, label: "A", state: "observed" },
      { id: "b", x: 2021, y: 0, size: maximum, category: 0, label: "B", state: "observed" }
    ];
    for (const model of [inventorModel("inventor-impact.v1", scatter),
      inventorModel("inventor-network.v1", network), inventorModel("inventor-activity.v1", timeline)]) {
      assert.equal(validateAdvancedModel(model), true);
      const before = JSON.stringify(model);
      const svg = renderAdvancedModelToRawSvg(model, SPEC);
      assert.equal(crossStrokes(svg).length, 0, model.analysis_id);
      assert.match(svg, /微小正値/u, "a distinct non-area marker is explicitly explained");
      assert.doesNotMatch(svg, /NaN|Infinity/u);
      assert.equal(JSON.stringify(model), before);
    }
  });
}

test("real annual unknown placeholders use the dotted hollow missing glyph, never the zero cross", () => {
  const projection = structuredClone(real.unknown);
  const model = inventorModel("inventor-activity.v1", projection);
  assert.equal(validateAdvancedModel(model), true);
  const before = JSON.stringify(model);
  const svg = renderAdvancedModelToRawSvg(model, SPEC);
  assert.equal(crossStrokes(svg).length, 0);
  const missing = tags(svg, "circle").filter(tag => attr(tag, "stroke") === "#94a3b8"
    && attr(tag, "stroke-dasharray") === "1 2" && Number(attr(tag, "cy")) < 600);
  assert.equal(missing.length, 1, "unknown data has the same dotted circle as its legend");
  assert.equal(attr(missing[0]!, "fill"), "#ffffff");
  assert.equal(JSON.stringify(model), before);
  projection.nodes.push({ id: "known-zero", x: 2020.5, y: 0, size: 0, category: 0,
    label: "既知0", state: "observed" });
  assert.equal(validateAdvancedModel(model), true);
  assert.equal(crossStrokes(renderAdvancedModelToRawSvg(model, SPEC)).length, 2,
    "only the newly added known zero uses crossing strokes");
});

for (const reverse of [false, true]) {
  test(`reciprocal strokes attach to small disk boundaries and retain arrow tangents (reverse=${reverse})`, () => {
    const p = networkProjection();
    p.nodes = [
      { id: "small", label: "Small", x: -5, y: 0, value: 1, group: 0, hop: null },
      { id: "large", label: "Large", x: 5, y: 0, value: 1000, group: 0, hop: null }
    ];
    p.edges = [
      { source: 0, target: 1, value: 1, directed: true, state: "observed" },
      { source: 1, target: 0, value: 1, directed: true, state: "inferred" }
    ];
    if (reverse) p.edges.reverse();
    const model = inventorModel("inventor-mobility-flow.v1", p);
    assert.equal(validateAdvancedModel(model), true);
    type Element = { type: string; shape: Record<string, number> & { points?: number[][] };
      style: { lineDash?: number[] } };
    const option = buildNetwork(model, SPEC, p) as { graphic: { elements: Element[] } };
    const elements = option.graphic.elements;
    const disks = elements.filter(e => e.type === "circle").slice(0, 2);
    const strokes = elements.filter(e => e.type === "line" || e.type === "polyline").slice(0, 2);
    const arrows = elements.filter(e => e.type === "polygon").slice(0, 2);
    const paths = strokes.map(e => e.type === "polyline" ? e.shape.points!
      : [[e.shape.x1!, e.shape.y1!], [e.shape.x2!, e.shape.y2!]]);
    for (const [i, edge] of p.edges.entries()) {
      const path = paths[i]!;
      for (const [point, disk] of [[path[0]!, disks[edge.source]!],
        [path[path.length - 1]!, disks[edge.target]!]] as const) {
        const distance = Math.hypot(point[0]! - disk.shape.cx!, point[1]! - disk.shape.cy!);
        assert.ok(Math.abs(distance - disk.shape.r!) < 0.02,
          `endpoint distance ${distance} must equal disk radius ${disk.shape.r}`);
      }
      assert.deepEqual(strokes[i]!.style.lineDash, edge.state === "inferred" ? [6, 4] : undefined);
      const end = path[path.length - 1]!, previous = path[path.length - 2]!;
      const arrow = arrows[i]!.shape.points!;
      assert.ok(Math.hypot(arrow[0]![0]! - end[0]!, arrow[0]![1]! - end[1]!) < 0.02);
      const base = [(arrow[1]![0]! + arrow[2]![0]!) / 2, (arrow[1]![1]! + arrow[2]![1]!) / 2];
      const tangent = [end[0]! - previous[0]!, end[1]! - previous[1]!];
      const direction = [end[0]! - base[0]!, end[1]! - base[1]!];
      assert.ok(direction[0]! * tangent[0]! + direction[1]! * tangent[1]! > 0);
      assert.ok(Math.abs(direction[0]! * tangent[1]! - direction[1]! * tangent[0]!)
        / Math.hypot(...tangent) < 0.02, "arrowhead follows final segment tangent");
    }
    const interior = paths.map(path => path.slice(1, -1));
    assert.ok(interior.every(points => points.length > 0), "small endpoints need separately routed interiors");
    assert.ok(Math.abs(interior[0]![0]![1]! - interior[1]![0]![1]!) >= 10);
    assert.doesNotMatch(renderAdvancedModelToRawSvg(model, SPEC), /NaN|Infinity/u);
  });
}

for (const label of ["W".repeat(18), "あ".repeat(18), "שלום".repeat(4), "👩‍🔬".repeat(18)]) {
  test(`timeline label fits actual installed font measurement near either edge: ${label}`, () => {
    for (const x of [2020, 2020.90, 2020.99]) {
      const p = timelineProjection(false);
      p.years = [2020]; p.lanes = ["A"]; p.links = []; p.bands = [];
      p.nodes = [{ id: "wide", x, y: 0, size: 1, category: 0, label, state: "observed" }];
      const model = inventorModel("inventor-activity.v1", p);
      assert.equal(validateAdvancedModel(model), true);
      const svg = renderAdvancedModelToRawSvg(model, SPEC);
      const matches = [...svg.matchAll(/<text\b[^>]*>([^<]*)<\/text>/gu)];
      const found = matches.find(match => match[1]!.startsWith([...label][0]!));
      assert.ok(found, "label remains visible");
      const left = Number(attr(found[0], "x"));
      const measure = new echarts.graphic.Text({ style: { text: found[1]!, fontSize: 9,
        fontFamily: SPEC.font_family, fontWeight: 400 } }).getBoundingRect();
      const anchor = attr(found[0], "text-anchor") ?? "start";
      const right = anchor === "end" ? left : left + measure.width;
      const start = anchor === "end" ? left - measure.width : left;
      assert.ok(start >= 6 && right <= SPEC.width - 6, `actual text bounds ${start}..${right}`);
    }
  });
}
