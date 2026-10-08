import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "vitest";
import type { AdvancedModel } from "../src/advanced-types.js";
import { validateAdvancedModel } from "../src/advanced-validation.js";

const fixtures = JSON.parse(readFileSync(new URL("./fixtures/advanced-models.json", import.meta.url), "utf8")) as {
  models: AdvancedModel[];
};
const source = fixtures.models.find(model => model.analysis_id === "compara.v1")!;

for (const removeAll of [false, true]) {
  test(`Compara rejects ${removeAll ? "all" : "one"} missing coordinates instead of inventing zero`, () => {
    const model = structuredClone(source);
    if (model.projection.kind !== "heatmap") throw new Error("fixture");
    assert.ok(model.projection.cells.length > 1);
    if (removeAll) model.projection.cells = [];
    else model.projection.cells.pop();
    const before = JSON.stringify(model);
    assert.equal(validateAdvancedModel(model), false);
    assert.equal(JSON.stringify(model), before);
  });
}

test("Compara accepts complete signed data without changing it", () => {
  const model = structuredClone(source);
  const before = JSON.stringify(model);
  assert.equal(validateAdvancedModel(model), true);
  assert.equal(JSON.stringify(model), before);
});

test("Compara retains an empty population without fabricated cells", () => {
  const model = structuredClone(source);
  if (model.projection.kind !== "heatmap") throw new Error("fixture");
  model.projection.x = [];
  model.projection.y = [];
  model.projection.cells = [];
  assert.equal(validateAdvancedModel(model), true);
});

test("Compara rejects duplicate coordinates even when the cell count matches", () => {
  const model = structuredClone(source);
  if (model.projection.kind !== "heatmap") throw new Error("fixture");
  model.projection.cells[1] = { ...model.projection.cells[0]! };
  assert.equal(validateAdvancedModel(model), false);
});
