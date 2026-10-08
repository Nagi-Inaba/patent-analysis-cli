import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "vitest";
import { renderAdvancedModelToRawSvg } from "../src/advanced-index.js";
import { validateAdvancedModel, validateAdvancedSpec } from "../src/advanced-validation.js";
import type { AdvancedModel, AdvancedSpec } from "../src/advanced-types.js";

const fixture = JSON.parse(readFileSync(new URL("./fixtures/advanced-models.json", import.meta.url), "utf8")) as {
  models: AdvancedModel[]; spec: AdvancedSpec;
};
for (const model of fixture.models) {
  test(`${model.analysis_id}: real closed ECharts SVG, deterministic and safe`, () => {
    assert.ok(validateAdvancedModel(model));
    assert.ok(validateAdvancedSpec(fixture.spec));
    const before = JSON.stringify(model);
    const first = renderAdvancedModelToRawSvg(model, fixture.spec);
    const second = renderAdvancedModelToRawSvg(model, fixture.spec);
    assert.equal(first, second);
    assert.equal(JSON.stringify(model), before);
    assert.match(first, /^<svg\b/);
    assert.doesNotMatch(first, /<script\b|<foreignObject\b|<iframe\b|<image\b|\bonload=/i);
    assert.ok(new TextEncoder().encode(first).length < 8 * 1024 * 1024);
  });
}

test("hostile literal citation labels remain escaped in real SVG", () => {
  const model = structuredClone(fixture.models.find(m => m.analysis_id === "citation.v1")!);
  if (model.projection.kind !== "scatter") throw new Error("fixture");
  model.projection.points[0]!.label = '{a}<script>"&';
  assert.ok(validateAdvancedModel(model));
  const svg = renderAdvancedModelToRawSvg(model, fixture.spec);
  assert.ok(svg.includes("{a}&lt;script&gt;"));
  assert.doesNotMatch(svg, /<script\b/i);
});

test("closed model rejects invalid mark, invented field, unsafe text and inconsistent totals", () => {
  const original = fixture.models.find(m => m.analysis_id === "citation.v1")!;
  for (const changed of [
    { ...original, mark: "ranking-svg.v1" },
    { ...original, arbitrary_options: {} },
    { ...original, population: { ...original.population, input_rows: original.population.input_rows + 1 } }
  ]) assert.equal(validateAdvancedModel(changed), false);
  const model = structuredClone(original);
  if (model.projection.kind !== "scatter") throw new Error("fixture");
  model.projection.points[0]!.label = "\u202e";
  assert.equal(validateAdvancedModel(model), false);
});

test("network validation rejects self links and duplicate unordered links", () => {
  const model = structuredClone(fixture.models.find(m => m.analysis_id === "collaboration-network.v1")!);
  if (model.projection.kind !== "network") throw new Error("fixture");
  const edge = model.projection.edges[0]!;
  model.projection.edges.push({ ...edge, source: edge.target, target: edge.source });
  assert.equal(validateAdvancedModel(model), false);
  model.projection.edges.pop();
  edge.target = edge.source;
  assert.equal(validateAdvancedModel(model), false);
});

test("cooccurrence validation rejects asymmetric cells or nonzero diagonal", () => {
  const model = structuredClone(fixture.models.find(m => m.analysis_id === "cooccurrence.v1")!);
  if (model.projection.kind !== "heatmap") throw new Error("fixture");
  model.projection.cells.find(c => c.x === c.y)!.value = 1;
  assert.equal(validateAdvancedModel(model), false);
});

for (const analysisId of ["citation.v1", "entry-exit.v1"]) {
  test(`${analysisId}: fixed axis flags and category vocabulary are enforced`, () => {
    const original = fixture.models.find(m => m.analysis_id === analysisId)!;
    for (const flag of ["x_year", "y_year"] as const) {
      const model = structuredClone(original);
      if (model.projection.kind !== "scatter") throw new Error("fixture");
      model.projection[flag] = !model.projection[flag];
      assert.equal(validateAdvancedModel(model), false);
    }
    const model = structuredClone(original);
    if (model.projection.kind !== "scatter") throw new Error("fixture");
    model.projection.points[0]!.category = analysisId === "citation.v1" ? "active" : "citation";
    assert.equal(validateAdvancedModel(model), false);
  });
}
