import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "vitest";
import { validateAdvancedModel } from "../src/advanced-validation.js";
import type { AdvancedModel } from "../src/advanced-types.js";

const fixtures = JSON.parse(readFileSync(
  new URL("./fixtures/advanced-models.json", import.meta.url), "utf8"
)) as { models: AdvancedModel[] };

for (const [left, right, joint, expected] of [
  [1, 1, 100, false], [2, 5, 3, false], [5, 2, 3, false],
  [2, 5, 2, true], [5, 2, 2, true], [0, 0, 0, false]
] as const) {
  test(`network ${left}/${right} endpoints and ${joint} joint count`, () => {
    const model = structuredClone(fixtures.models.find(
      m => m.analysis_id === "collaboration-network.v1"
    )!);
    if (model.projection.kind !== "network") throw new Error("fixture");
    model.projection.nodes = [{ label: "A", value: left }, { label: "B", value: right }];
    model.projection.edges = [{ source: 0, target: 1, value: joint }];
    const before = JSON.stringify(model);
    assert.equal(validateAdvancedModel(model), expected);
    assert.equal(JSON.stringify(model), before);
  });
}

test("three owners of one record allow two incident edges per node", () => {
  const model = structuredClone(fixtures.models.find(
    m => m.analysis_id === "collaboration-network.v1"
  )!);
  if (model.projection.kind !== "network") throw new Error("fixture");
  model.projection.nodes = ["A", "B", "C"].map(label => ({ label, value: 1 }));
  model.projection.edges = [
    { source: 0, target: 1, value: 1 },
    { source: 0, target: 2, value: 1 },
    { source: 1, target: 2, value: 1 }
  ];
  assert.equal(validateAdvancedModel(model), true);
});

// The closed model requires positive node/edge values; no records means empty arrays.
test("an empty collaboration model remains valid without zero-valued synthetic nodes", () => {
  const model = structuredClone(fixtures.models.find(
    m => m.analysis_id === "collaboration-network.v1"
  )!);
  if (model.projection.kind !== "network") throw new Error("fixture");
  model.projection.nodes = [];
  model.projection.edges = [];
  assert.equal(validateAdvancedModel(model), true);
});
