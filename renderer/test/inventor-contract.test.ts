import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { describe, test } from "vitest";
import { buildAdvancedOption } from "../src/advanced-options.js";
import { SUPPORTED_INVENTOR_MARKS } from "../src/advanced-inventor-options.js";
import { renderAdvancedModelToRawSvg, renderRequest } from "../src/advanced-index.js";
import type { AdvancedModel, AdvancedProjection } from "../src/advanced-types.js";
import { validateAdvancedModel } from "../src/advanced-validation.js";
import { decodeCanonicalBase64, encodeCanonicalBase64, encodeUtf8, sha256Hex } from "../src/points-payload.js";
import {
  ANALYSES, SPEC, alluvialProjection, egoProjection, flowProjection, heatmapProjection, inventorModel, markOf,
  networkProjection, scatterProjection, timelineProjection, type InventorAnalysisId
} from "./inventor-models.js";

const projections: Record<string, () => AdvancedProjection> = {
  "inventor-network": networkProjection, "inventor-heatmap": heatmapProjection,
  "inventor-timeline": () => timelineProjection(false), "inventor-alluvial": alluvialProjection,
  "inventor-scatter": scatterProjection
};
function validModel(id: InventorAnalysisId): AdvancedModel {
  const entry = ANALYSES.find(item => item.analysis_id === id)!;
  const projection = id === "inventor-ego-network.v1" ? egoProjection()
    : id === "inventor-mobility-flow.v1" ? flowProjection()
      : id === "inventor-mobility.v1" ? timelineProjection(true) : projections[entry.kind]!();
  return inventorModel(id, projection);
}
const asObject = (value: unknown) => value as Record<string, unknown>;
const renderAdvancedModelToRawSvgForTest = (model: AdvancedModel) => renderAdvancedModelToRawSvg(model, SPEC);

describe("nine inventor marks", () => {
  test("every mark is the analysis slug plus -svg.v1 and is reported as supported", () => {
    assert.deepEqual([...SUPPORTED_INVENTOR_MARKS].sort(), ANALYSES.map(item => markOf(item.analysis_id)).sort());
    assert.equal(SUPPORTED_INVENTOR_MARKS.length, 9);
    assert.ok(SUPPORTED_INVENTOR_MARKS.every(mark => /^inventor-[a-z-]+-svg\.v1$/u.test(mark)));
  });
  test("each analysis validates only with its own mark, title and kind", () => {
    for (const entry of ANALYSES) {
      const valid = validModel(entry.analysis_id);
      assert.equal(validateAdvancedModel(valid), true, entry.analysis_id);
      for (const other of ANALYSES) {
        if (other.analysis_id === entry.analysis_id) continue;
        const wrongMark = structuredClone(valid); wrongMark.mark = markOf(other.analysis_id);
        const wrongTitle = structuredClone(valid); wrongTitle.title = other.title;
        assert.equal(validateAdvancedModel(wrongMark), false, `${entry.analysis_id} with ${other.analysis_id} mark`);
        assert.equal(validateAdvancedModel(wrongTitle), false, `${entry.analysis_id} with ${other.analysis_id} title`);
        if (other.kind !== entry.kind) {
          const wrongKind = structuredClone(valid); wrongKind.projection = projections[other.kind]!();
          assert.equal(validateAdvancedModel(wrongKind), false, `${entry.analysis_id} with ${other.kind}`);
        }
      }
    }
  });
  test("a legacy analysis cannot carry an inventor projection, and the reverse", () => {
    const legacy = inventorModel("inventor-network.v1", networkProjection());
    legacy.analysis_id = "collaboration-network.v1"; legacy.mark = "collaboration-network-svg.v1"; legacy.title = "共同関係ネットワーク";
    assert.equal(validateAdvancedModel(legacy), false);
    const reverse = inventorModel("inventor-network.v1", { kind: "network", nodes: [], edges: [], context: "" });
    assert.equal(validateAdvancedModel(reverse), false);
  });
  test("closed model: unknown top-level keys, other chart types and non-NFC text are rejected", () => {
    for (const entry of ANALYSES) {
      const model = validModel(entry.analysis_id);
      assert.equal(validateAdvancedModel({ ...model, arbitrary_options: {} }), false);
      assert.equal(validateAdvancedModel({ ...model, chart_type: "points.bubble" }), false);
      assert.equal(validateAdvancedModel({ ...model, analysis_result_sha256: "XYZ" }), false);
      assert.equal(validateAdvancedModel({ ...model, population: { input_rows: 1, analyzed_rows: 1, excluded_rows: 1 } }), false);
      const decomposed = structuredClone(model);
      asObject(decomposed.projection).context = "é";
      assert.equal(validateAdvancedModel(decomposed), false, "combining sequences must arrive as NFC");
    }
  });
  test("raw model schema stays within the 16 KiB renderer schema limit", () => {
    const size = readFileSync(new URL("../../src/patent_analysis/schemas/advanced-chart-model-v1.schema.json", import.meta.url)).length;
    assert.ok(size <= 16 * 1024, `${size} bytes`);
  });
});

describe("closed schemas", () => {
  /** Every object inside the projection, as a path from the model root. */
  function objectPaths(value: unknown, path: (string | number)[] = []): (string | number)[][] {
    if (Array.isArray(value)) return value.flatMap((item, index) => objectPaths(item, [...path, index]));
    if (value === null || typeof value !== "object") return [];
    return [path, ...Object.entries(value).flatMap(([key, item]) => objectPaths(item, [...path, key]))];
  }
  const resolve = (root: unknown, path: (string | number)[]) =>
    path.reduce<unknown>((node, key) => (node as Record<string | number, unknown>)[key], root);

  test("every property of every inventor object is required, in the size-capped model schema", () => {
    for (const entry of ANALYSES) {
      const model = validModel(entry.analysis_id);
      for (const path of objectPaths(model.projection, ["projection"])) {
        for (const key of Object.keys(resolve(model, path) as object)) {
          const broken = structuredClone(model);
          delete asObject(resolve(broken, path))[key];
          assert.equal(validateAdvancedModel(broken), false, `${entry.analysis_id} ${path.join(".")}.${key}`);
        }
        const extra = structuredClone(model);
        asObject(resolve(extra, path)).__unexpected = 1;
        assert.equal(validateAdvancedModel(extra), false, `${entry.analysis_id} ${path.join(".")} extra key`);
      }
    }
  });
  test("the generated schema validator alone already enforces the approved per-analysis constraints", async () => {
    const modulePath = "../src/generated/advanced-standalone-validators.js";
    const { validateModelRaw } = await import(modulePath) as { validateModelRaw: (value: unknown) => boolean };
    const ego = validModel("inventor-ego-network.v1"); asObject(ego.projection).focus = null;
    const flow = validModel("inventor-mobility-flow.v1");
    (asObject(flow.projection).edges as { directed: boolean }[])[1]!.directed = false;
    const activity = validModel("inventor-activity.v1"); asObject(activity.projection).bands = timelineProjection(true).bands;
    const crossed = validModel("inventor-network.v1"); crossed.title = "発明者中心の関係マップ";
    const unmapped = validModel("inventor-network.v1"); unmapped.analysis_id = "inventor-unknown.v1";
    for (const model of [ego, flow, activity, crossed, unmapped]) assert.equal(validateModelRaw(model), false);
    for (const entry of ANALYSES) assert.equal(validateModelRaw(validModel(entry.analysis_id)), true, entry.analysis_id);
  });
  test("the public projection schema is strict-compilable and agrees on all five kinds", async () => {
    type AjvClass = new (options: object) => { compile(schema: object): (value: unknown) => boolean };
    const Ajv2020 = (await import("ajv/dist/2020.js")).default as unknown as AjvClass;
    const schema = JSON.parse(readFileSync(new URL("../../src/patent_analysis/schemas/advanced-projection-v1.schema.json", import.meta.url), "utf8"));
    const validate = new Ajv2020({ strict: true, allErrors: false }).compile(schema);
    for (const [kind, make] of Object.entries(projections)) {
      assert.equal(validate(make()), true, kind);
      assert.equal(validate({ ...make(), arbitrary_options: {} }), false, kind);
      for (const key of Object.keys(make())) {
        const broken = asObject(structuredClone(make()));
        delete broken[key];
        assert.equal(validate(broken), false, `${kind} without ${key}`);
      }
    }
    assert.equal(validate({ ...networkProjection(), kind: "inventor-unknown" }), false);
  });
});

describe("fixed options carry no user code, URLs or interaction", () => {
  const walk = (value: unknown, visit: (item: unknown, path: string) => void, path = "option") => {
    visit(value, path);
    if (Array.isArray(value)) value.forEach((item, index) => walk(item, visit, `${path}[${index}]`));
    else if (value !== null && typeof value === "object") {
      for (const [key, item] of Object.entries(value)) walk(item, visit, `${path}.${key}`);
    }
  };
  for (const entry of ANALYSES) {
    test(`${entry.analysis_id}: option is plain JSON data with a fixed top-level shape`, () => {
      const model = validModel(entry.analysis_id);
      const before = JSON.stringify(model);
      const option = buildAdvancedOption(model, SPEC);
      assert.equal(JSON.stringify(model), before);
      assert.deepEqual(Object.keys(option).sort(), ["animation", "backgroundColor", "graphic", "series", "textStyle", "title"]);
      assert.equal(option.animation, false);
      assert.equal(option.tooltip, undefined);
      walk(option, (item, path) => {
        assert.notEqual(typeof item, "function", path);
        if (typeof item === "string") assert.doesNotMatch(item, /https?:|javascript:|data:|<script/iu, path);
      });
      assert.equal(JSON.stringify(option), JSON.stringify(buildAdvancedOption(model, SPEC)));
    });
  }
  test("hostile option-like keys are rejected rather than forwarded", () => {
    for (const entry of ANALYSES) {
      for (const key of ["formatter", "options", "url", "link", "tooltip", "series"]) {
        const model = validModel(entry.analysis_id);
        asObject(model.projection)[key] = key === "formatter" ? "function(){}" : {};
        assert.equal(validateAdvancedModel(model), false, `${entry.analysis_id} ${key}`);
      }
    }
  });
});

describe("drawn geometry stays on the page", () => {
  const numbers = (tag: string, name: string) => [...tag.matchAll(new RegExp(`\\b${name}="(-?[0-9.]+)"`, "gu"))].map(match => Number(match[1]));
  for (const entry of ANALYSES) {
    test(`${entry.analysis_id}: shapes, text anchors and polygons lie inside 1200 x 675`, () => {
      const svg = renderAdvancedModelToRawSvgForTest(validModel(entry.analysis_id));
      for (const tag of svg.match(/<(?:circle|rect|text|polygon)\b[^>]*>/gu) ?? []) {
        if (tag.includes("transform=")) continue; // ECharts title block, positioned by the title component
        for (const x of [...numbers(tag, "cx"), ...numbers(tag, "x")]) assert.ok(x >= 0 && x <= 1200, `${tag} x=${x}`);
        for (const y of [...numbers(tag, "cy"), ...numbers(tag, "y")]) assert.ok(y >= 0 && y <= 675, `${tag} y=${y}`);
        const list = /\bpoints="([^"]+)"/u.exec(tag)?.[1];
        if (list) for (const pair of list.split(" ")) {
          const [x, y] = pair.split(",").map(Number);
          assert.ok(x! >= 0 && x! <= 1200 && y! >= 0 && y! <= 675, `${entry.analysis_id} point ${pair}`);
        }
      }
    });
  }
});

describe("request transfer", () => {
  const runtime = JSON.stringify({
    node_version: "22.19.0", echarts_version: "6.1.0", renderer_build_digest: "1".repeat(64),
    render_profile_id: "advanced-svg-ja-jp-node22-echarts6.v1"
  });
  function transfer(model: unknown, overrides: { modelDigest?: string } = {}): string {
    const modelBytes = encodeUtf8(JSON.stringify(model)), specBytes = encodeUtf8(JSON.stringify(SPEC));
    return encodeCanonicalBase64(encodeUtf8(JSON.stringify({
      protocol_version: "1.0.0",
      chart_model_b64: encodeCanonicalBase64(modelBytes), chart_model_sha256: overrides.modelDigest ?? sha256Hex(modelBytes),
      render_spec_b64: encodeCanonicalBase64(specBytes), render_spec_sha256: sha256Hex(specBytes)
    })));
  }
  const respond = (request: string) => JSON.parse(renderRequest(request, runtime)) as {
    ok: boolean; svg_b64?: string; error?: { code: string };
  };
  test("all nine analyses render through the existing request path", () => {
    for (const entry of ANALYSES) {
      const response = respond(transfer(validModel(entry.analysis_id)));
      assert.equal(response.ok, true, entry.analysis_id);
      const svg = new TextDecoder().decode(decodeCanonicalBase64(response.svg_b64, 8 * 1024 * 1024));
      assert.match(svg, /^<svg\b/u);
      assert.ok(svg.includes(entry.title), `${entry.analysis_id} carries its exact title`);
    }
  });
  test("a model digest mismatch is reported before any parsing of the model", () => {
    const response = respond(transfer(validModel("inventor-network.v1"), { modelDigest: "0".repeat(64) }));
    assert.deepEqual([response.ok, response.error?.code], [false, "digest.mismatch"]);
  });
  test("a digest-consistent but invalid mapping is a schema rejection", () => {
    const model = validModel("inventor-network.v1");
    model.mark = "inventor-ego-network-svg.v1";
    const response = respond(transfer(model));
    assert.deepEqual([response.ok, response.error?.code], [false, "schema.invalid"]);
  });
});
