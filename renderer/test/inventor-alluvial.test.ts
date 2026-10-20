import assert from "node:assert/strict";
import { describe, test } from "vitest";
import { renderAdvancedModelToRawSvg } from "../src/advanced-index.js";
import type { AdvancedModel } from "../src/advanced-types.js";
import { validateAdvancedModel } from "../src/advanced-validation.js";
import { SPEC, alluvialProjection, inventorModel } from "./inventor-models.js";

type AlluvialProjection = ReturnType<typeof alluvialProjection>;
const base = () => inventorModel("inventor-cluster-flow.v1", alluvialProjection());
function mutate(change: (p: AlluvialProjection) => void): AdvancedModel {
  const model = base();
  change(model.projection as AlluvialProjection);
  return model;
}
const texts = (svg: string) => [...svg.matchAll(/<text\b[^>]*>([^<]*)<\/text>/gu)].map(match => match[1]!);
const tags = (svg: string, name: string) => svg.match(new RegExp(`<${name}\\b[^>]*>`, "gu")) ?? [];
const attribute = (tag: string, name: string) => new RegExp(`\\b${name}="([^"]*)"`, "u").exec(tag)?.[1];
// Boxes (and legend swatches) are four-point polygons; ribbons are sampled curves with more points.
const polygons = (svg: string) => tags(svg, "polygon");
const boxTags = (svg: string) => polygons(svg).filter(tag => attribute(tag, "points")!.split(" ").length === 4);
const ribbonTags = (svg: string) => polygons(svg).filter(tag => attribute(tag, "points")!.split(" ").length > 4);
const points = (tag: string) => attribute(tag, "points")!.split(" ").map(pair => pair.split(",").map(Number) as [number, number]);

function nodeBoxes(svg: string) {
  return boxTags(svg).slice(0, 7).map(tag => {
    const corners = points(tag);
    const xs = corners.map(corner => corner[0]), ys = corners.map(corner => corner[1]);
    return { x: Math.min(...xs), width: Math.max(...xs) - Math.min(...xs), height: Math.max(...ys) - Math.min(...ys) };
  });
}

describe("inventor-alluvial validation", () => {
  test("accepts a complete model with every link kind, without mutating it", () => {
    const model = base();
    const before = JSON.stringify(model);
    assert.equal(validateAdvancedModel(model), true);
    assert.equal(JSON.stringify(model), before);
  });
  const corruptions: [string, (p: AlluvialProjection) => void][] = [
    ["a duplicate node id", p => { p.nodes[1]!.id = p.nodes[0]!.id; }],
    ["a node year outside the years", p => { p.nodes[0]!.year = 2018; }],
    ["unsorted years", p => { p.years = [2019, 2021, 2020, 2022]; }],
    ["non consecutive years", p => { p.years = [2019, 2020, 2022, 2023]; }],
    ["duplicated years", p => { p.years = [2019, 2020, 2020, 2021, 2022]; }],
    ["a link source out of range", p => { p.links[0]!.source = 7; }],
    ["a link target out of range", p => { p.links[0]!.target = 7; }],
    ["a negative link index", p => { p.links[0]!.source = -1; }],
    ["a self loop", p => { p.links[0]!.target = p.links[0]!.source; }],
    ["a duplicate link", p => { p.links.push({ ...p.links[0]! }); }],
    ["a backwards link", p => { p.links[0] = { source: 2, target: 0, value: 4, kind: "continuation" }; }],
    ["a continuation that skips a year", p => { p.links[3]!.kind = "continuation"; }],
    ["a split that skips a year", p => { p.links[3]!.kind = "split"; }],
    ["a merge that skips a year", p => { p.links[3]!.kind = "merge"; }],
    ["a gap link between adjacent years", p => { p.links[0]!.kind = "gap"; }],
    ["a continuation from a not observed box", p => { p.links[0]!.source = 6; }],
    ["a newly observed link from a cluster", p => { p.links[4]!.source = 1; }],
    ["a newly observed link inside one year", p => { p.nodes[4]!.year = 2020; }],
    ["a not observed link into a cluster", p => { p.links[5]!.target = 3; }],
    ["a zero width link", p => { p.links[0]!.value = 0; }],
    ["a fractional link width", p => { p.links[0]!.value = 1.5; }],
    ["a negative link width", p => { p.links[0]!.value = -1; }],
    ["a link wider than its source box", p => { p.links[2]!.value = 4; }],
    ["outgoing links wider than their box", p => { p.nodes[0]!.members = 5; }],
    ["incoming links wider than their box", p => { p.nodes[2]!.members = 5; }],
    ["a negative member count", p => { p.nodes[0]!.members = -1; }],
    ["a fractional member count", p => { p.nodes[0]!.members = 2.5; }],
    ["an unknown node kind", p => { (p.nodes[0] as { kind: string }).kind = "retired"; }],
    ["an unknown link kind", p => { (p.links[0] as { kind: string }).kind = "probability"; }],
    ["an unknown node key", p => { (p.nodes[0] as Record<string, unknown>).url = "x"; }],
    ["an unknown link key", p => { (p.links[0] as Record<string, unknown>).probability = 0.5; }],
    ["an unknown projection key", p => { (p as Record<string, unknown>).options = {}; }],
    ["31 years", p => {
      p.years = Array.from({ length: 31 }, (_, i) => 1990 + i); p.nodes = []; p.links = [];
    }],
    ["101 nodes", p => {
      p.nodes = Array.from({ length: 101 }, (_, i) => ({ ...p.nodes[0]!, id: `n${i}` })); p.links = [];
    }],
    ["301 links", p => {
      p.nodes = Array.from({ length: 100 }, (_, i) => ({ id: `n${i}`, label: `L${i}`, year: 2019 + (i % 2), members: 1000, kind: "cluster" as const }));
      p.links = Array.from({ length: 301 }, (_, i) => ({ source: i % 50 * 2, target: (i % 50) * 2 + 1, value: 1, kind: "continuation" as const }));
    }]
  ];
  for (const [name, change] of corruptions) {
    test(`rejects ${name} before rendering`, () => {
      const model = mutate(change);
      const before = JSON.stringify(model);
      assert.equal(validateAdvancedModel(model), false);
      assert.equal(JSON.stringify(model), before);
    });
  }
  test("accepts boxes without links and a fully empty projection", () => {
    assert.equal(validateAdvancedModel(mutate(p => { p.links = []; })), true);
    assert.equal(validateAdvancedModel(mutate(p => { p.years = []; p.nodes = []; p.links = []; })), true);
  });
  test("rejects nodes when no years are declared", () => {
    assert.equal(validateAdvancedModel(mutate(p => { p.years = []; p.links = []; })), false);
  });
  test("rejects an incorrect mark, title, analysis or kind", () => {
    const wrongMark = base(); wrongMark.mark = "inventor-similarity-svg.v1";
    const wrongTitle = base(); wrongTitle.title = "発明者の活動履歴";
    const wrongAnalysis = base(); wrongAnalysis.analysis_id = "inventor-activity.v1";
    const wrongKind = base(); wrongKind.projection = {
      kind: "inventor-network", nodes: [], edges: [], focus: null, context: ""
    };
    for (const model of [wrongMark, wrongTitle, wrongAnalysis, wrongKind]) assert.equal(validateAdvancedModel(model), false);
  });
});

describe("inventor-alluvial rendering", () => {
  test("is deterministic, closed, and labels every year and every box", () => {
    const model = base();
    const before = JSON.stringify(model);
    const first = renderAdvancedModelToRawSvg(model, SPEC);
    assert.equal(first, renderAdvancedModelToRawSvg(model, SPEC));
    assert.equal(JSON.stringify(model), before);
    assert.doesNotMatch(first, /<script\b|<foreignObject\b|<image\b|<a\b|href=|onload=/iu);
    const shown = texts(first);
    for (const label of ["2019", "2020", "2021", "2022", "Group A 2019", "Group B 2019", "Group C 2020", "Group D 2022",
      "New 2019", "Unseen 2021"]) assert.ok(shown.includes(label), label);
  });
  test("numbers in the chart are never bold, while headings stay bold", () => {
    const svg = renderAdvancedModelToRawSvg(base(), SPEC);
    const textTags = [...svg.matchAll(/<text\b([^>]*)>([^<]*)<\/text>/gu)].map(match => ({ tag: match[1]!, text: match[2]! }));
    const isBold = (tag: string) => /font-weight="(?:bold|[6-9]00)"/u.test(tag);
    const numbers = textTags.filter(item => /^\d+$/u.test(item.text));
    assert.ok(numbers.length >= 4 + 3, "year headings and member counts are present");
    assert.deepEqual(numbers.filter(item => isBold(item.tag)).map(item => item.text), []);
    assert.ok(textTags.some(item => item.text === "リンク:" && isBold(item.tag)), "legend headings keep their weight");
  });
  test("box height and link width share one membership scale", () => {
    const svg = renderAdvancedModelToRawSvg(base(), SPEC);
    const heights = nodeBoxes(svg).map(box => box.height);
    assert.ok(Math.abs(heights[0]! / heights[1]! - 2) < 0.02, "6 members vs 3 members");
    assert.ok(Math.abs(heights[2]! / heights[3]! - 3) < 0.02, "6 members vs 2 members");
    const ribbon = points(ribbonTags(svg)[0]!);
    const thickness = ribbon[ribbon.length - 1]![1] - ribbon[0]![1];
    // Link 0 carries 4 of the 6 members of box 0, so it is 4/6 of that box's height.
    assert.ok(Math.abs(thickness - heights[0]! * 4 / 6) < 0.05, `${thickness} vs ${heights[0]! * 4 / 6}`);
  });
  test("ribbons start at the source box edge and end at the target box edge", () => {
    const svg = renderAdvancedModelToRawSvg(base(), SPEC);
    const boxes = nodeBoxes(svg);
    const ribbon = points(ribbonTags(svg)[0]!);
    assert.equal(ribbon[0]![0], boxes[0]!.x + boxes[0]!.width);
    assert.equal(Math.max(...ribbon.map(point => point[0])), boxes[2]!.x);
  });
  test("one ribbon per link, with gap links dashed and never drawn as continuity", () => {
    const ribbons = ribbonTags(renderAdvancedModelToRawSvg(base(), SPEC));
    assert.equal(ribbons.length, 6);
    assert.deepEqual(ribbons.map(tag => attribute(tag, "stroke-dasharray")),
      [undefined, undefined, undefined, "5 3", undefined, undefined]);
  });
  test("entry and exit boxes are dashed and explicitly not employment events", () => {
    const svg = renderAdvancedModelToRawSvg(base(), SPEC);
    const dashedBoxes = boxTags(svg).filter(tag => attribute(tag, "stroke-dasharray") === "3 2");
    assert.equal(dashedBoxes.length, 2 + 2, "two entry/exit boxes plus two legend swatches");
    const shown = texts(svg);
    assert.ok(shown.some(text => text.includes("入社") && text.includes("退職")), "entry/exit are not hiring/leaving");
    assert.ok(shown.some(text => text.includes("共有して観測された人数")), "widths are shared observed persons");
    assert.ok(shown.some(text => text.includes("確率") && text.includes("部門")), "not probabilities or departments");
  });
  test("a model without links draws boxes only", () => {
    const svg = renderAdvancedModelToRawSvg(mutate(p => { p.links = []; }), SPEC);
    assert.equal(ribbonTags(svg).length, 0);
  });
  test("labels render as inert text", () => {
    const model = mutate(p => { p.nodes[0]!.label = '{a}<i>"&'; });
    assert.equal(validateAdvancedModel(model), true);
    const svg = renderAdvancedModelToRawSvg(model, SPEC);
    assert.ok(svg.includes("{a}&lt;i&gt;"));
    assert.doesNotMatch(svg, /<script\b|<i>/iu);
  });
  test("zero member boxes stay visible as a thin box", () => {
    const model = mutate(p => { p.nodes[6]!.members = 0; p.links = []; });
    assert.equal(validateAdvancedModel(model), true);
    const heights = nodeBoxes(renderAdvancedModelToRawSvg(model, SPEC)).map(box => box.height);
    assert.ok(heights[6]! > 0 && heights[6]! < heights[3]!, `${heights[6]}`);
  });
  test("empty flow renders a bounded notice", () => {
    const svg = renderAdvancedModelToRawSvg(mutate(p => { p.years = []; p.nodes = []; p.links = []; }), SPEC);
    assert.ok(svg.includes("対象データなし"));
  });
  test("100 maximum length labels in two columns stay inside the SVG text budget", () => {
    const model = mutate(p => {
      p.years = [2019, 2020];
      p.nodes = Array.from({ length: 100 }, (_, i) => ({
        id: `n${i}`, label: "L".repeat(180), year: 2019 + (i % 2), members: 1, kind: "cluster" as const
      }));
      p.links = [];
    });
    assert.equal(validateAdvancedModel(model), true);
    assert.ok(renderAdvancedModelToRawSvg(model, SPEC).length > 0);
  });
  test("the 30 year, 100 node, 300 link maximum stays inside the SVG budgets", () => {
    const model = mutate(p => {
      p.years = Array.from({ length: 30 }, (_, i) => 1990 + i);
      p.nodes = Array.from({ length: 100 }, (_, i) => ({
        id: `n${i}`, label: `Group ${i}`, year: 1990 + Math.floor(i / 4) % 30, members: 3 + (i % 5), kind: "cluster" as const
      }));
      p.links = Array.from({ length: 96 }, (_, i) => ({ source: i, target: i + 4, value: 1, kind: "continuation" as const }));
    });
    assert.equal(validateAdvancedModel(model), true);
    assert.ok(renderAdvancedModelToRawSvg(model, SPEC).length > 0);
  });
});
