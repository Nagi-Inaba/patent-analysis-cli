import assert from "node:assert/strict";
import { describe, test } from "vitest";
import type { AdvancedModel } from "../src/advanced-types.js";
import { validateAdvancedModel } from "../src/advanced-validation.js";
import { renderAdvancedModelToRawSvg } from "../src/advanced-index.js";
import {
  SPEC, alluvialProjection, inventorModel, networkProjection, scatterProjection, timelineProjection
} from "./inventor-models.js";

type NetworkProjection = ReturnType<typeof networkProjection>;
const network = () => inventorModel("inventor-network.v1", networkProjection());
function networkWith(change: (p: NetworkProjection) => void): AdvancedModel {
  const model = network();
  change(model.projection as NetworkProjection);
  return model;
}

describe("review 1: bidirectional marks", () => {
  const marks: [string, string][] = [["U+061C", "؜"], ["U+200E", "‎"], ["U+200F", "‏"]];
  for (const [name, mark] of marks) {
    test(`${name} is rejected in context, labels and ids`, () => {
      assert.equal(validateAdvancedModel(networkWith(p => { p.context = `A${mark}B`; })), false, "context");
      assert.equal(validateAdvancedModel(networkWith(p => { p.nodes[0]!.label = `A${mark}B`; })), false, "label");
      assert.equal(validateAdvancedModel(networkWith(p => { p.nodes[0]!.id = `n${mark}a`; })), false, "id");
      const titled = network(); titled.title = `T${mark}`;
      assert.equal(validateAdvancedModel(titled), false, "title");
    });
  }
  test("ordinary Arabic and Hebrew letters and emoji ZWJ graphemes stay valid", () => {
    const model = networkWith(p => {
      p.context = "مرحبا שלום 👨‍👩‍👧";
      p.nodes[0]!.label = "שלום";
      p.nodes[1]!.label = "مرحبا";
      p.nodes[2]!.label = "👨‍👩‍👧";
    });
    assert.equal(validateAdvancedModel(model), true);
  });
  test("embedding and isolate controls stay rejected", () => {
    for (const mark of ["‪", "‮", "⁦", "⁩"]) {
      assert.equal(validateAdvancedModel(networkWith(p => { p.context = `A${mark}B`; })), false, mark);
    }
  });
});

const SPEC_ = SPEC;
const tagsOf = (svg: string, name: string) => svg.match(new RegExp(`<${name}\\b[^>]*>`, "gu")) ?? [];
const attr = (tag: string, name: string) => new RegExp(`\\b${name}="([^"]*)"`, "u").exec(tag)?.[1];
const radiiOf = (svg: string) => tagsOf(svg, "circle").map(tag => Number(attr(tag, "r")));
const shownText = (svg: string) => [...svg.matchAll(/<text\b[^>]*>([^<]*)<\/text>/gu)].map(match => match[1]!);
const numbersOf = (d: string) => (d.match(/-?\d+(?:\.\d+)?/gu) ?? []).map(Number);
/** Straight two-point strokes with equal |dx| and |dy| (diagonals), as drawn for the zero cross. */
function crossStrokes(svg: string) {
  return tagsOf(svg, "path").map(tag => ({ tag, n: numbersOf(attr(tag, "d") ?? "") }))
    .filter(({ tag, n }) => attr(tag, "fill") === "none" && n.length === 4 && Math.abs(Math.abs(n[2]! - n[0]!) - Math.abs(n[3]! - n[1]!)) < 1e-9
      && Math.abs(n[2]! - n[0]!) > 0)
    .map(({ n }) => ({ dx: n[2]! - n[0]!, dy: n[3]! - n[1]!, mx: (n[0]! + n[2]!) / 2, my: (n[1]! + n[3]!) / 2 }));
}

describe("review 2: proportional circle area (network)", () => {
  test("values 1 and 4 give radii 1:2 so the areas are 1:4", () => {
    const svg = renderAdvancedModelToRawSvg(networkWith(p => {
      p.nodes = [
        { id: "n-1", label: "One", x: -5, y: 0, value: 1, group: 0, hop: null },
        { id: "n-2", label: "Four", x: 5, y: 0, value: 4, group: 0, hop: null }
      ];
      p.edges = [];
    }), SPEC_);
    const [small, large] = radiiOf(svg);
    assert.equal(large, 20, "maximum keeps the shared cap");
    assert.ok(Math.abs(large! / small! - 2) < 0.01, `${small} ${large}`);
  });
  test("a known zero is a fixed-size cross glyph, not a disk, and the legend says so", () => {
    const svg = renderAdvancedModelToRawSvg(networkWith(p => {
      p.nodes = [
        { id: "n-1", label: "Zero", x: -5, y: 0, value: 0, group: 0, hop: null },
        { id: "n-2", label: "Four", x: 5, y: 0, value: 4, group: 1, hop: null }
      ];
      p.edges = [];
    }), SPEC_);
    // One disk for the positive node plus two community legend swatches (r=5); nothing for the zero node.
    assert.equal(tagsOf(svg, "circle").length, 3, "zero must not be an activity disk");
    const strokes = crossStrokes(svg);
    assert.equal(strokes.length, 2, "two diagonal strokes form the zero cross");
    const [a, b] = strokes;
    assert.deepEqual([a!.mx, a!.my], [b!.mx, b!.my]);
    assert.deepEqual([Math.abs(a!.dx), Math.abs(a!.dy), Math.abs(b!.dx), Math.abs(b!.dy)], [8, 8, 8, 8]);
    assert.ok(a!.dx * a!.dy * b!.dx * b!.dy < 0, "the two strokes cross");
    assert.ok(shownText(svg).some(text => text.includes("×") && text.includes("0")), "legend explains the zero glyph");
  });
});

describe("review 2: proportional circle area (scatter)", () => {
  type ScatterProjection = ReturnType<typeof scatterProjection>;
  const scatterWith = (change: (p: ScatterProjection) => void) => {
    const model = inventorModel("inventor-impact.v1", scatterProjection());
    change(model.projection as ScatterProjection);
    return model;
  };
  const point = (id: string, size: number, category: string, x: number) => ({ id, label: id, x, y: 0, size, category });
  test("values 1 and 4 give radii 1:2", () => {
    const svg = renderAdvancedModelToRawSvg(scatterWith(p => {
      p.points = [point("p1", 1, "a", -1), point("p4", 4, "a", 1)]; p.edges = []; p.unplottable = [];
    }), SPEC_);
    const [small, large] = radiiOf(svg);
    assert.equal(large, 20);
    assert.ok(Math.abs(large! / small! - 2) < 0.01, `${small} ${large}`);
  });
  test("a known zero is a cross and all-zero data draws no disk", () => {
    const svg = renderAdvancedModelToRawSvg(scatterWith(p => {
      p.points = [point("p0", 0, "a", -1), point("p4", 4, "b", 1)]; p.edges = [];
    }), SPEC_);
    // One disk for the positive point plus two category legend swatches (r=5).
    assert.equal(tagsOf(svg, "circle").length, 3, "zero must not be an activity disk");
    assert.equal(crossStrokes(svg).length, 2);
    assert.ok(shownText(svg).some(text => text.includes("×") && text.includes("0")), "legend explains the zero glyph");
    const allZero = renderAdvancedModelToRawSvg(scatterWith(p => {
      p.points = [point("p0", 0, "a", -1), point("q0", 0, "a", 1)]; p.edges = []; p.unplottable = [];
    }), SPEC_);
    assert.deepEqual(radiiOf(allZero), [5], "only the legend swatch remains; no huge or floor-sized disks");
    assert.equal(crossStrokes(allZero).length, 4);
    assert.doesNotMatch(allZero, /NaN|Infinity/u);
  });
});

describe("review 3: reciprocal directed edges stay separate", () => {
  type Edge = NetworkProjection["edges"][number];
  const forward: Edge = { source: 0, target: 1, value: 3, directed: true, state: "observed" };
  const backward: Edge = { source: 1, target: 0, value: 3, directed: true, state: "inferred" };
  const pairSvg = (edges: Edge[]) => {
    const model = inventorModel("inventor-mobility-flow.v1", networkProjection());
    const p = model.projection as NetworkProjection;
    p.nodes = [
      { id: "c-1", label: "Company One", x: -8, y: 0, value: 6, group: 0, hop: null },
      { id: "c-2", label: "Company Two", x: 8, y: 0, value: 6, group: 1, hop: null }
    ];
    p.edges = edges;
    assert.equal(validateAdvancedModel(model), true, "ordered reciprocal edges are valid and not dropped");
    return renderAdvancedModelToRawSvg(model, SPEC_);
  };
  /** Edge strokes (plain lines before any node) as [x1, y1, x2, y2, dash]. */
  const strokes = (svg: string) => tagsOf(svg, "path")
    .filter(tag => attr(tag, "fill") === "none" && numbersOf(attr(tag, "d") ?? "").length === 4)
    .slice(0, 2).map(tag => ({ n: numbersOf(attr(tag, "d")!), dash: attr(tag, "stroke-dasharray") }));
  const tips = (svg: string) => tagsOf(svg, "polygon").map(tag => numbersOf(attr(tag, "points") ?? ""))
    .filter(n => n.length === 6 && n[0]! < 900).map(n => [n[0]!, n[1]!]);
  for (const [name, edges] of [["forward first", [forward, backward]], ["backward first", [backward, forward]]] as const) {
    test(`two strokes are visually separate with each state and direction identifiable (${name})`, () => {
      const svg = pairSvg([...edges]);
      const found = strokes(svg);
      assert.equal(found.length, 2);
      const observed = found.find(item => item.dash === undefined)!, inferred = found.find(item => item.dash === "6 4")!;
      assert.ok(observed && inferred, "one solid and one dashed stroke");
      const gap = Math.abs(observed.n[1]! - inferred.n[1]!);
      assert.ok(gap >= 10, `centre lines are ${gap}px apart`);
      assert.ok(observed.n[2]! > observed.n[0]! && inferred.n[2]! < inferred.n[0]!, "directions keep their own tangent");
      const arrows = tips(svg);
      assert.equal(arrows.length, 2);
      const obsTip = arrows.find(tip => Math.abs(tip[1]! - observed.n[3]!) < 0.01)!;
      const infTip = arrows.find(tip => Math.abs(tip[1]! - inferred.n[3]!) < 0.01)!;
      assert.ok(obsTip && infTip, "each arrowhead sits on its own stroke");
      assert.ok(obsTip[0]! > infTip[0]!, "observed points to the right-hand node, inferred to the left-hand node");
    });
  }
});

describe("review 4: alluvial common scale", () => {
  type AlluvialProjection = ReturnType<typeof alluvialProjection>;
  type AlluvialNode = AlluvialProjection["nodes"][number];
  type AlluvialLink = AlluvialProjection["links"][number];
  const flowSvg = (years: number[], nodes: AlluvialNode[], links: AlluvialLink[]) => {
    const model = inventorModel("inventor-cluster-flow.v1", alluvialProjection());
    const p = model.projection as AlluvialProjection;
    p.years = years; p.nodes = nodes; p.links = links;
    assert.equal(validateAdvancedModel(model), true);
    return renderAdvancedModelToRawSvg(model, SPEC_);
  };
  const polygonsOf = (svg: string) => tagsOf(svg, "polygon").map(tag => numbersOf(attr(tag, "points") ?? ""));
  const heightOf = (n: number[]) => {
    const ys = n.filter((_, i) => i % 2 === 1);
    return Math.max(...ys) - Math.min(...ys);
  };
  const node = (id: string, year: number, members: number): AlluvialNode => ({ id, label: id, year, members, kind: "cluster" });
  // The SVG serializer prints polygon points with one decimal, so a height carries up to 0.1 px of rounding.
  const ROUNDING = 0.1 + 1e-9;
  test("members 1 vs 1000 keep a 1:1000 height ratio and the ribbon uses the same scale", () => {
    const svg = flowSvg([2020, 2021], [node("small", 2020, 1), node("large", 2021, 1000)],
      [{ source: 0, target: 1, value: 1, kind: "continuation" }]);
    const shapes = polygonsOf(svg);
    const boxes = shapes.filter(n => n.length === 8).slice(0, 2), ribbon = shapes.find(n => n.length > 8)!;
    const small = heightOf(boxes[0]!), large = heightOf(boxes[1]!);
    assert.ok(Math.abs(large / 1000 - small) <= ROUNDING, `box heights ${small} and ${large}`);
    // The outline starts at the source edge top and returns along the bottom edge, so its last y is top + width.
    assert.ok(Math.abs((ribbon[ribbon.length - 1]! - ribbon[1]!) - small) <= ROUNDING, "ribbon width equals the small box scale");
  });
});

describe("review 4b: alluvial column layout stays above the legend", () => {
  type AlluvialProjection = ReturnType<typeof alluvialProjection>;
  type AlluvialNode = AlluvialProjection["nodes"][number];
  const LEGEND_TOP = 575;
  const build = (nodes: AlluvialNode[], links: AlluvialProjection["links"]) => {
    const model = inventorModel("inventor-cluster-flow.v1", alluvialProjection());
    const p = model.projection as AlluvialProjection;
    p.years = [2020, 2021]; p.nodes = nodes; p.links = links;
    assert.equal(validateAdvancedModel(model), true);
    return renderAdvancedModelToRawSvg(model, SPEC_);
  };
  const node = (id: string, year: number, members: number): AlluvialNode => ({ id, label: id, year, members, kind: "cluster" });
  const ys = (n: number[]) => n.filter((_, i) => i % 2 === 1);
  const polygonsOf = (svg: string) => tagsOf(svg, "polygon").map(tag => numbersOf(attr(tag, "points") ?? ""));
  test("ten members=1 boxes plus one members=1000 box and their adjacent-year counterparts never reach the legend", () => {
    const sizes = [...Array.from({ length: 10 }, () => 1), 1000];
    const nodes = [...sizes.map((m, i) => node(`a${i}`, 2020, m)), ...sizes.map((m, i) => node(`b${i}`, 2021, m))];
    const links = sizes.map((m, i) => ({ source: i, target: 11 + i, value: m, kind: "continuation" as const }));
    const shapes = polygonsOf(build(nodes, links));
    const boxes = shapes.filter(n => n.length === 8).slice(0, 22), ribbons = shapes.filter(n => n.length > 8);
    assert.equal(boxes.length, 22);
    assert.equal(ribbons.length, 11);
    const bottoms = [...boxes, ...ribbons].map(n => Math.max(...ys(n)));
    assert.ok(Math.max(...bottoms) < LEGEND_TOP - 5, `lowest quantitative edge ${Math.max(...bottoms)}`);
    const heights = boxes.map(n => Math.max(...ys(n)) - Math.min(...ys(n)));
    assert.ok(Math.abs(heights[10]! / 1000 - heights[0]!) <= 0.1 + 1e-9, `${heights[0]} ${heights[10]}`);
  });
  test("zero-member markers are reserved in the layout and are not quantitative boxes", () => {
    const nodes = [...Array.from({ length: 10 }, (_, i) => node(`z${i}`, 2020, 0)), node("big", 2020, 1000)];
    const svg = build(nodes, []);
    // The single quantitative box plus 6 link and 3 box legend swatches; the ten zero boxes add no polygon.
    assert.equal(polygonsOf(svg).filter(n => n.length === 8).length, 1 + 6 + 3);
    const markers = tagsOf(svg, "path").map(tag => ({ n: numbersOf(attr(tag, "d") ?? ""), w: Number(attr(tag, "stroke-width")) }))
      .filter(({ n, w }) => n.length === 4 && n[1] === n[3] && w === 3 && Math.abs(n[2]! - n[0]!) === 40);
    assert.equal(markers.length, 10);
    const lowestBox = Math.max(...ys(polygonsOf(svg).filter(n => n.length === 8)[0]!));
    assert.ok(lowestBox < LEGEND_TOP - 5, `${lowestBox}`);
    assert.ok(markers.every(({ n }) => n[1]! < LEGEND_TOP - 5));
  });
  test("a hundred nodes in one column keep a positive scale and stay above the legend", () => {
    const nodes = Array.from({ length: 100 }, (_, i) => node(`n${i}`, 2020, i % 3 === 0 ? 0 : 1 + (i % 5)));
    const svg = build(nodes, []);
    assert.doesNotMatch(svg, /NaN|Infinity/u);
    const boxes = polygonsOf(svg).filter(n => n.length === 8).slice(0, nodes.filter(n => n.members > 0).length);
    assert.ok(boxes.every(n => Math.max(...ys(n)) < LEGEND_TOP - 5 && Math.min(...ys(n)) >= 180));
  });
});

describe("review 5: timeline labels near the canvas edges", () => {
  type TimelineProjection = ReturnType<typeof timelineProjection>;
  const label = "あいうえおかきく";
  const edgeSvg = (x: number, text = label) => {
    const model = inventorModel("inventor-activity.v1", timelineProjection(false));
    const p = model.projection as TimelineProjection;
    p.years = [2020]; p.lanes = ["A"]; p.bands = []; p.links = [];
    p.nodes = [{ id: "n1", x, y: 0, size: 1, category: 0, label: text, state: "observed" }];
    assert.equal(validateAdvancedModel(model), true);
    return renderAdvancedModelToRawSvg(model, SPEC_);
  };
  /** Horizontal extent of the label text, using 9 px per full-width character at font-size 9. */
  function extentOfLabel(svg: string, prefix: string) {
    const tag = [...svg.matchAll(/<text\b[^>]*>([^<]*)<\/text>/gu)].find(match => match[1]!.startsWith(prefix));
    assert.ok(tag, `a label starting with ${prefix} is rendered`);
    const shown = tag[1]!, x = Number(attr(tag[0], "x")), anchor = attr(tag[0], "text-anchor") ?? "start";
    const width = [...shown].length * 9;
    return { shown, x0: anchor === "end" ? x - width : x, x1: anchor === "end" ? x : x + width };
  }
  const node = (svg: string) => {
    const tag = tagsOf(svg, "circle")[0]!;
    return { cx: Number(attr(tag, "cx")), r: Number(attr(tag, "r")) };
  };
  test("a label at x=2020.99 stays readable inside 1200 px and clear of its node", () => {
    const svg = edgeSvg(2020.99);
    const { x0, x1, shown } = extentOfLabel(svg, "あいう");
    const { cx, r } = node(svg);
    assert.ok(x0 >= 0 && x1 <= 1200, `label spans ${x0}..${x1}`);
    assert.ok(x1 <= cx - r || x0 >= cx + r, `label ${x0}..${x1} overlaps node ${cx}±${r}`);
    assert.ok(shown.length >= 3, "a short label is kept legible");
    const labelTag = [...svg.matchAll(/<text\b[^>]*>あいう[^<]*<\/text>/gu)][0]![0];
    const y = Number(attr(labelTag, "y"));
    assert.ok(y >= 160 && y <= 600, `label stays on its lane inside the vertical frame (y=${y})`);
  });
  test("a label at the left edge is still placed to the right of its node", () => {
    const svg = edgeSvg(2020);
    const { x0, x1 } = extentOfLabel(svg, "あいう");
    const { cx, r } = node(svg);
    assert.ok(x0 >= cx + r && x1 <= 1200, `${x0}..${x1} vs node ${cx}±${r}`);
  });
  test("an 18 character label at the right edge is also kept inside the canvas", () => {
    const svg = edgeSvg(2020.99, "あ".repeat(18));
    const { x0, x1 } = extentOfLabel(svg, "あ");
    assert.ok(x0 >= 0 && x1 <= 1200, `${x0}..${x1}`);
  });
});

describe("review 2: proportional circle area (timeline)", () => {
  type TimelineProjection = ReturnType<typeof timelineProjection>;
  const timelineWith = (sizes: number[], states: ("observed" | "inferred" | "confirmed" | "unknown")[] = []) => {
    const model = inventorModel("inventor-activity.v1", timelineProjection(false));
    const p = model.projection as TimelineProjection;
    p.lanes = ["Alpha Person"];
    p.nodes = sizes.map((size, i) => ({ id: `t-${i}`, x: 2019 + i * 1.5, y: 0, size, category: 0, label: `N${i}`, state: states[i] ?? "observed" }));
    p.links = [];
    return model;
  };
  test("values 1 and 4 give radii 1:2 under the shared 12 px cap", () => {
    const [small, large] = radiiOf(renderAdvancedModelToRawSvg(timelineWith([1, 4]), SPEC_));
    assert.equal(large, 12);
    assert.ok(Math.abs(large! / small! - 2) < 0.01, `${small} ${large}`);
  });
  test("a known zero is a cross, not a disk, and the legend explains it", () => {
    const svg = renderAdvancedModelToRawSvg(timelineWith([0, 4]), SPEC_);
    // One disk for the positive node plus three legend swatches (observed, inferred, unknown).
    assert.equal(tagsOf(svg, "circle").length, 4, "zero must not be an activity disk");
    assert.equal(crossStrokes(svg).length, 2);
    assert.ok(shownText(svg).some(text => text.includes("×") && text.includes("0")), "legend explains the zero glyph");
    assert.doesNotMatch(renderAdvancedModelToRawSvg(timelineWith([0, 0]), SPEC_), /NaN|Infinity/u);
  });
});
