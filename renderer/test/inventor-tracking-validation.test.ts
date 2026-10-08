import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "vitest";
import type { AdvancedModel } from "../src/advanced-types.js";
import { validateAdvancedModel } from "../src/advanced-validation.js";

const fixtures = JSON.parse(readFileSync(new URL("./fixtures/advanced-models.json", import.meta.url), "utf8")) as { models: AdvancedModel[] };
const source = fixtures.models.find(m => m.analysis_id === "inventor-tracking.v1")!;
for (const corruption of ["missing-link", "false-gap", "invalid-coordinate", "duplicate-node", "false-year"] as const) {
  test(`tracking rejects ${corruption} before rendering`, () => {
    const model = structuredClone(source);
    const p = model.projection;
    if (p.kind !== "tracking") throw new Error("fixture");
    if (corruption === "missing-link") p.links.pop();
    if (corruption === "false-gap") p.links[0]!.gap = !p.links[0]!.gap;
    if (corruption === "invalid-coordinate") p.nodes[0]!.x = p.years.length;
    if (corruption === "duplicate-node") p.nodes.push({ ...p.nodes[0]! });
    if (corruption === "false-year") p.years[1]! += 1;
    assert.equal(validateAdvancedModel(model), false);
  });
}
