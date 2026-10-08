import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "vitest";
import { validateAdvancedModel } from "../src/advanced-validation.js";
import type { AdvancedModel } from "../src/advanced-types.js";

const fixtures = JSON.parse(readFileSync(
  new URL("./fixtures/advanced-models.json", import.meta.url), "utf8"
)) as { models: AdvancedModel[] };

function bars(analysisId: string, counts: number[], denominators: number[]): AdvancedModel {
  const model = structuredClone(fixtures.models.find(m => m.analysis_id === analysisId)!);
  if (model.projection.kind !== "bars") throw new Error("fixture must have bars");
  model.projection.items = counts.map((value, index) => {
    const denominator = denominators[index]!;
    return { label: `C${index}`, value, denominator,
      share: denominator ? value / denominator : 0,
      record_count: 20, involvement_count: null };
  });
  return model;
}

test("matrix composition rejects combined 160 percent without changing the input", () => {
  const model = bars("matrix-composition.v1", [8, 8], [10, 10]);
  const before = JSON.stringify(model);
  assert.equal(validateAdvancedModel(model), false);
  assert.equal(JSON.stringify(model), before);
});

test("matrix composition requires one common denominator", () => {
  assert.equal(validateAdvancedModel(bars("matrix-composition.v1", [1, 1], [10, 20])), false);
});

test("matrix composition accepts an upper subset without renormalizing it", () => {
  const model = bars("matrix-composition.v1", [2, 3], [10, 10]);
  const before = JSON.stringify(model);
  assert.equal(validateAdvancedModel(model), true);
  assert.equal(JSON.stringify(model), before);
});

test("matrix composition accepts complete shares and harmless floating point summation", () => {
  assert.equal(validateAdvancedModel(bars("matrix-composition.v1", [3, 7], [10, 10])), true);
  assert.equal(validateAdvancedModel(bars(
    "matrix-composition.v1", Array(10).fill(1), Array(10).fill(10)
  )), true);
});

test("matrix composition retains empty and zero-population views", () => {
  assert.equal(validateAdvancedModel(bars("matrix-composition.v1", [], [])), true);
  assert.equal(validateAdvancedModel(bars("matrix-composition.v1", [0, 0], [0, 0])), true);
});

test("independent groups do not acquire a shared composition denominator", () => {
  assert.equal(validateAdvancedModel(bars("uniqueness.v1", [8, 16], [10, 20])), true);
});
