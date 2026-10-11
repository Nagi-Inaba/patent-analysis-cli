import assert from "node:assert/strict";
import { describe, test } from "vitest";
import { renderAdvancedModelToRawSvg } from "../src/advanced-index.js";
import type { AdvancedModel } from "../src/advanced-types.js";
import { validateAdvancedModel } from "../src/advanced-validation.js";
import { SPEC, inventorModel, timelineProjection } from "./inventor-models.js";

type TimelineProjection = ReturnType<typeof timelineProjection>;
const activity = () => inventorModel("inventor-activity.v1", timelineProjection(false));
const mobility = () => inventorModel("inventor-mobility.v1", timelineProjection(true));
const valid = { "inventor-activity.v1": activity, "inventor-mobility.v1": mobility } as const;
function mutate(id: keyof typeof valid, change: (p: TimelineProjection) => void): AdvancedModel {
  const model = valid[id]();
  change(model.projection as TimelineProjection);
  return model;
}
const texts = (svg: string) => [...svg.matchAll(/<text\b[^>]*>([^<]*)<\/text>/gu)].map(match => match[1]!);
const tags = (svg: string, name: string) => svg.match(new RegExp(`<${name}\\b[^>]*>`, "gu")) ?? [];
const attribute = (tag: string, name: string) => new RegExp(`\\b${name}="([^"]*)"`, "u").exec(tag)?.[1];
const allObserved = (model: AdvancedModel) => {
  (model.projection as TimelineProjection).nodes.forEach(node => { node.state = "observed"; });
  return model;
};

describe("inventor-timeline validation", () => {
  for (const id of Object.keys(valid) as (keyof typeof valid)[]) {
    test(`${id} accepts a complete synthetic model without mutation`, () => {
      const model = valid[id]();
      const before = JSON.stringify(model);
      assert.equal(validateAdvancedModel(model), true);
      assert.equal(JSON.stringify(model), before);
    });
  }
  const corruptions: [string, keyof typeof valid, (p: TimelineProjection) => void][] = [
    ["employment-like bands on the activity history", "inventor-activity.v1", p => {
      p.bands = timelineProjection(true).bands;
    }],
    ["a duplicate node id", "inventor-mobility.v1", p => { p.nodes[1]!.id = p.nodes[0]!.id; }],
    ["a duplicate band id", "inventor-mobility.v1", p => { p.bands[1]!.id = p.bands[0]!.id; }],
    ["a lane index outside the lanes", "inventor-mobility.v1", p => { p.nodes[0]!.y = 2; }],
    ["a node before the first year", "inventor-mobility.v1", p => { p.nodes[0]!.x = 2018.99; }],
    ["a node after the last year", "inventor-mobility.v1", p => { p.nodes[2]!.x = 2024.01; }],
    ["unsorted years", "inventor-mobility.v1", p => { p.years = [2019, 2021, 2020, 2022, 2023]; }],
    ["a gap in the years", "inventor-mobility.v1", p => { p.years = [2019, 2020, 2022, 2023]; }],
    ["a duplicated year", "inventor-mobility.v1", p => { p.years = [2019, 2020, 2020, 2021, 2022, 2023]; }],
    ["a fractional year", "inventor-mobility.v1", p => { (p.years as number[])[0] = 2019.5; }],
    ["a link source out of range", "inventor-mobility.v1", p => { p.links[0]!.source = 4; }],
    ["a link target out of range", "inventor-mobility.v1", p => { p.links[0]!.target = 9; }],
    ["a self linked node", "inventor-mobility.v1", p => { p.links[0]!.target = p.links[0]!.source; }],
    ["a duplicate link", "inventor-mobility.v1", p => { p.links.push({ ...p.links[0]! }); }],
    ["a reversed duplicate link", "inventor-mobility.v1", p => {
      p.links.push({ ...p.links[0]!, source: p.links[0]!.target, target: p.links[0]!.source });
    }],
    ["an unknown link state", "inventor-mobility.v1", p => { (p.links[0] as { state: string }).state = "unknown"; }],
    ["a non boolean gap", "inventor-mobility.v1", p => { (p.links[0] as { gap: unknown }).gap = "yes"; }],
    ["an unknown node state", "inventor-mobility.v1", p => { (p.nodes[0] as { state: string }).state = "employed"; }],
    ["a band that ends before it starts", "inventor-mobility.v1", p => { p.bands[0]!.end = p.bands[0]!.start - 0.1; }],
    ["a band outside the declared years", "inventor-mobility.v1", p => { p.bands[0]!.end = 2025; }],
    ["a band that never touches the declared years", "inventor-mobility.v1", p => {
      p.bands[0]!.start = 2010; p.bands[0]!.end = 2011;
    }],
    ["an unknown band kind", "inventor-mobility.v1", p => { (p.bands[0] as { kind: string }).kind = "hired"; }],
    ["an unknown band status", "inventor-mobility.v1", p => { (p.bands[0] as { status: string }).status = "rumoured"; }],
    ["a category above 199", "inventor-mobility.v1", p => { p.nodes[0]!.category = 200; }],
    ["a negative size", "inventor-mobility.v1", p => { p.nodes[0]!.size = -1; }],
    ["a non finite coordinate", "inventor-mobility.v1", p => { p.nodes[0]!.x = Number.NaN; }],
    ["an unknown node property", "inventor-mobility.v1", p => { (p.nodes[0] as Record<string, unknown>).url = "x"; }],
    ["an unknown band property", "inventor-mobility.v1", p => { (p.bands[0] as Record<string, unknown>).lane = 0; }],
    ["an unknown projection property", "inventor-mobility.v1", p => { (p as Record<string, unknown>).options = {}; }],
    ["21 lanes", "inventor-mobility.v1", p => {
      p.lanes = Array.from({ length: 21 }, (_, i) => `Person ${i}`); p.nodes = []; p.links = [];
    }],
    ["31 years", "inventor-mobility.v1", p => {
      p.years = Array.from({ length: 31 }, (_, i) => 1990 + i); p.nodes = []; p.links = []; p.bands = [];
    }],
    ["501 nodes", "inventor-mobility.v1", p => {
      p.nodes = Array.from({ length: 501 }, (_, i) => ({ ...p.nodes[0]!, id: `n${i}` })); p.links = [];
    }],
    ["nodes without any lane or year", "inventor-mobility.v1", p => { p.lanes = []; p.years = []; }]
  ];
  for (const [name, id, change] of corruptions) {
    test(`rejects ${name} before rendering`, () => {
      const model = mutate(id, change);
      const before = JSON.stringify(model);
      assert.equal(validateAdvancedModel(model), false);
      assert.equal(JSON.stringify(model), before);
    });
  }
  test("keeps empty calendar years and unobserved lanes as valid, unfabricated data", () => {
    const model = mutate("inventor-mobility.v1", p => {
      p.years = Array.from({ length: 30 }, (_, i) => 1990 + i);
      p.nodes = [{ ...p.nodes[0]!, x: 1990.5, y: 0 }]; p.links = []; p.bands = [];
    });
    assert.equal(validateAdvancedModel(model), true);
    assert.equal(validateAdvancedModel(mutate("inventor-mobility.v1", p => {
      p.lanes = []; p.years = []; p.nodes = []; p.links = []; p.bands = [];
    })), true);
  });
  test("accepts the boundary instants of the declared range", () => {
    const model = mutate("inventor-mobility.v1", p => { p.nodes[0]!.x = 2019; p.nodes[2]!.x = 2024; });
    assert.equal(validateAdvancedModel(model), true);
  });
  test("rejects an incorrect mark, title, analysis or kind for both analyses", () => {
    for (const id of Object.keys(valid) as (keyof typeof valid)[]) {
      const wrongMark = valid[id](); wrongMark.mark = "inventor-tracking-svg.v1";
      const wrongTitle = valid[id](); wrongTitle.title = "発明者の技術類似度";
      const wrongAnalysis = valid[id](); wrongAnalysis.analysis_id = "inventor-technology.v1";
      const wrongKind = valid[id](); wrongKind.projection = {
        kind: "inventor-network", nodes: [], edges: [], focus: null, context: ""
      };
      const swapped = valid[id](); swapped.mark = id === "inventor-activity.v1" ? "inventor-mobility-svg.v1" : "inventor-activity-svg.v1";
      for (const model of [wrongMark, wrongTitle, wrongAnalysis, wrongKind, swapped]) {
        assert.equal(validateAdvancedModel(model), false, id);
      }
    }
  });
});

describe("inventor-timeline rendering", () => {
  test("is deterministic, closed, and shows lanes, every year and node descriptions", () => {
    const model = mobility();
    const before = JSON.stringify(model);
    const first = renderAdvancedModelToRawSvg(model, SPEC);
    assert.equal(first, renderAdvancedModelToRawSvg(model, SPEC));
    assert.equal(JSON.stringify(model), before);
    assert.doesNotMatch(first, /<script\b|<foreignObject\b|<image\b|<a\b|href=|onload=/iu);
    const shown = texts(first);
    for (const label of ["Alpha Person", "Beta Person", "2019", "2020", "2021", "2022", "2023",
      "Company X 2019", "Company Y 2021-06", "Company Z"]) assert.ok(shown.includes(label), label);
  });
  test("empty calendar years stay visible and imply no zero or retirement", () => {
    const model = mutate("inventor-activity.v1", p => {
      p.years = Array.from({ length: 10 }, (_, i) => 2014 + i); p.nodes = p.nodes.slice(0, 1);
      p.nodes[0]!.x = 2014.5; p.links = [];
    });
    const shown = texts(renderAdvancedModelToRawSvg(model, SPEC));
    for (let year = 2014; year < 2024; year++) assert.ok(shown.includes(String(year)), String(year));
    assert.ok(shown.some(text => text.includes("観測のない年")), "empty years are explained as unobserved");
  });
  test("x positions are proportional to fractional calendar years", () => {
    const model = allObserved(activity());
    (model.projection as TimelineProjection).nodes[2]!.size = 1; // a known zero would be a cross, not a circle
    const svg = renderAdvancedModelToRawSvg(model, SPEC);
    const [a, b, c] = tags(svg, "circle").map(tag => Number(attribute(tag, "cx")));
    // 2019.0 -> 2021.5 spans 2.5 years and 2021.5 -> 2022.25 spans 0.75 years.
    const ratio = (b! - a!) / (c! - b!);
    assert.ok(Math.abs(ratio - 2.5 / 0.75) < 0.05, String(ratio));
  });
  test("node area follows the fixed size scale", () => {
    const svg = renderAdvancedModelToRawSvg(allObserved(activity()), SPEC);
    // Sizes 4, 1, 0, 4: r = 12 * sqrt(size / 4). The known zero is a cross, so it contributes no circle.
    assert.deepEqual(tags(svg, "circle").slice(0, 3).map(tag => attribute(tag, "r")), ["12", "6", "12"]);
  });
  test("inferred is dashed, confirmed has its own symbol, unknown is hollow", () => {
    const base = allObserved(activity());
    const countDashed = (svg: string) => tags(svg, "circle").filter(tag => attribute(tag, "stroke-dasharray") === "4 3").length;
    const baseline = renderAdvancedModelToRawSvg(base, SPEC);
    const withInferred = renderAdvancedModelToRawSvg(mutate("inventor-activity.v1", p => {
      p.nodes.forEach(node => { node.state = "observed"; }); p.nodes[1]!.state = "inferred";
    }), SPEC);
    assert.equal(countDashed(withInferred) - countDashed(baseline), 1);
    const withConfirmed = renderAdvancedModelToRawSvg(mutate("inventor-activity.v1", p => {
      p.nodes.forEach(node => { node.state = "observed"; }); p.nodes[2]!.state = "confirmed";
    }), SPEC);
    assert.equal(tags(withConfirmed, "polygon").length - tags(baseline, "polygon").length, 1);
    const withUnknown = renderAdvancedModelToRawSvg(mutate("inventor-activity.v1", p => {
      p.nodes.forEach(node => { node.state = "observed"; }); p.nodes[3]!.state = "unknown";
    }), SPEC);
    // Node circles are, in order, sizes 4, 1 and 4 (the size 0 node is a cross); the unknown node is the third.
    const fills = (svg: string) => tags(svg, "circle").slice(0, 3).map(tag => attribute(tag, "fill"));
    assert.notEqual(fills(withUnknown)[2], fills(baseline)[2]);
  });
  test("link state dashes inferred transitions and gap styling is independent", () => {
    const linkPaths = (svg: string) => tags(svg, "path").filter(tag => /fill="none"/u.test(tag) && attribute(tag, "stroke-width") === "2");
    const regular = renderAdvancedModelToRawSvg(activity(), SPEC);
    const [observedGap, inferredPlain] = linkPaths(regular);
    assert.equal(attribute(observedGap!, "stroke-dasharray"), undefined, "gap alone must not dash");
    assert.equal(attribute(inferredPlain!, "stroke-dasharray"), "6 4");
    const swapped = renderAdvancedModelToRawSvg(mutate("inventor-activity.v1", p => {
      p.links[0]!.gap = false; p.links[1]!.gap = true;
    }), SPEC);
    const [observedPlain, inferredGap] = linkPaths(swapped);
    assert.equal(attribute(observedPlain!, "stroke-dasharray"), undefined);
    assert.equal(attribute(inferredGap!, "stroke-dasharray"), "6 4", "gap must not remove the inferred dash");
    assert.notEqual(attribute(observedGap!, "opacity"), attribute(observedPlain!, "opacity"), "gap is shown separately");
  });
  test("corporate bands are drawn only when supplied and are not employment", () => {
    const withBands = texts(renderAdvancedModelToRawSvg(mobility(), SPEC));
    for (const label of ["Event One", "Event Two"]) assert.ok(withBands.some(text => text.includes(label)), label);
    assert.ok(withBands.some(text => text.includes("在籍")), "caveat that a band is not employment");
    const without = texts(renderAdvancedModelToRawSvg(activity(), SPEC));
    assert.ok(!without.some(text => text.includes("Event")));
    assert.ok(!without.some(text => text.includes("企業イベント")), "no fabricated band area for the activity history");
  });
  test("announced and completed bands differ in outline", () => {
    const svg = renderAdvancedModelToRawSvg(mobility(), SPEC);
    const dashes = tags(svg, "path").filter(tag => attribute(tag, "stroke-dasharray") === "5 3");
    assert.ok(dashes.length >= 1, "an announced band has a dashed outline");
  });
  test("labels render as inert text", () => {
    const model = mutate("inventor-mobility.v1", p => {
      p.lanes[0] = '{a}<i>"&'; p.nodes[0]!.label = "<b>x</b>"; p.bands[0]!.label = "<u>y</u>";
    });
    assert.equal(validateAdvancedModel(model), true);
    const svg = renderAdvancedModelToRawSvg(model, SPEC);
    for (const escaped of ["{a}&lt;i&gt;", "&lt;b&gt;x&lt;/b&gt;", "&lt;u&gt;y&lt;/u&gt;"]) assert.ok(svg.includes(escaped), escaped);
    assert.doesNotMatch(svg, /<script\b|<b>|<i>|<u>/iu);
  });
  test("empty timeline renders a bounded notice", () => {
    const svg = renderAdvancedModelToRawSvg(mutate("inventor-activity.v1", p => {
      p.lanes = []; p.years = []; p.nodes = []; p.links = [];
    }), SPEC);
    assert.ok(svg.includes("対象データなし"));
  });
  test("maximum size with maximum length labels stays inside the SVG text budget", () => {
    // The model may carry at most 20,000 graphemes in total, so spend them where the drawing prints most:
    // 500 node labels of 18 shown characters plus wide bands of 102 shown characters.
    const model = mutate("inventor-mobility.v1", p => {
      p.lanes = ["Lane"];
      p.years = Array.from({ length: 30 }, (_, i) => 1990 + i);
      p.nodes = Array.from({ length: 500 }, (_, i) => ({
        id: `n${i}`, x: 1990 + (i % 30) + 0.5, y: 0, size: 1, category: 0, label: "N".repeat(18), state: "observed" as const
      }));
      p.links = [];
      p.bands = Array.from({ length: 30 }, (_, i) => ({
        id: `b${i}`, start: 1990, end: 2020, label: "B".repeat(102), kind: "merger" as const, status: "completed" as const
      }));
      p.context = "";
    });
    assert.equal(validateAdvancedModel(model), true);
    assert.ok(renderAdvancedModelToRawSvg(model, SPEC).length > 0);
  });
  test("the 20 lane, 30 year, 500 node maximum stays inside the SVG budgets", () => {
    const model = mutate("inventor-mobility.v1", p => {
      p.lanes = Array.from({ length: 20 }, (_, i) => `Person ${i}`);
      p.years = Array.from({ length: 30 }, (_, i) => 1990 + i);
      p.nodes = Array.from({ length: 500 }, (_, i) => ({
        id: `n${i}`, x: 1990 + (i % 30) + 0.25, y: i % 20, size: i % 7, category: i % 12,
        label: `Company ${i}`, state: (["observed", "inferred", "confirmed", "unknown"] as const)[i % 4]!
      }));
      p.links = Array.from({ length: 480 }, (_, i) => ({ source: i, target: i + 20, gap: i % 2 === 0, state: "observed" as const }));
      p.bands = Array.from({ length: 100 }, (_, i) => ({
        id: `b${i}`, start: 1990 + (i % 25), end: 1992 + (i % 25), label: `Event ${i}`,
        kind: "merger" as const, status: "completed" as const
      }));
    });
    assert.equal(validateAdvancedModel(model), true);
    assert.ok(renderAdvancedModelToRawSvg(model, SPEC).length > 0);
  });
});
