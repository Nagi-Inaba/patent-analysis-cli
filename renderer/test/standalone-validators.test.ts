import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import type { ChartModel } from "../src/payload.js";

const SHA256 = "a".repeat(64);
const semanticCorpus = JSON.parse(
  await readFile(new URL("../../tests/fixtures/renderer-visual-cases.json", import.meta.url), "utf8")
) as {
  semantic_cases: Array<{
    id: string;
    operation: string;
    python_valid: boolean;
    renderer_valid: boolean;
  }>;
};
const segmenter = new Intl.Segmenter("ja-JP", { granularity: "grapheme" });

async function loadStandaloneValidators() {
  try {
    const modulePath = "../src/generated/standalone-validators.js";
    return { loaded: true, module: await import(modulePath) } as const;
  } catch {
    return { loaded: false } as const;
  }
}

function requestFixture() {
  return {
    protocol_version: "1.0.0",
    chart_model_b64: "e30=",
    chart_model_sha256: SHA256,
    render_spec_b64: "e30=",
    render_spec_sha256: SHA256
  };
}

function runtimeFixture() {
  return {
    node_version: "22.23.4",
    echarts_version: "6.1.0",
    renderer_build_digest: SHA256,
    render_profile_id: "ranking-svg-ja-jp-node22-echarts6.v1"
  };
}

function chartModelFixture() {
  return {
    chart_model_contract_version: "1.0.0",
    chart_type: "ranking.horizontal_bar",
    analysis_result_sha256: SHA256,
    label_overlay_sha256: null,
    title: "出願人のランキング",
    dimension: {
      source_label: "applicant",
      display_label: "出願人",
      description: null
    },
    measure: { mode: "count", column: null },
    population: { input_rows: 3, analyzed_rows: 3 },
    rows: [
      {
        index: 0,
        row_kind: "dimension_value",
        source_label: "甲社",
        display_label: "甲社",
        description: null,
        semantic_label: "データ中の分類値",
        value: 2,
        count: 2,
        share: 2 / 3
      },
      {
        index: 1,
        row_kind: "remainder",
        source_label: "その他",
        display_label: "その他",
        description: null,
        semantic_label: "上位表示外の合計",
        value: 1,
        count: 1,
        share: 1 / 3
      }
    ],
    warnings: []
  };
}

function renderSpecFixture() {
  return {
    render_spec_contract_version: "1.0.0",
    renderer_kind: "ranking.horizontal_bar.svg",
    locale: "ja-JP",
    timezone: "UTC",
    width: 1200,
    height: 675,
    font_family: "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif",
    animation: false,
    axis_label_max_graphemes: 28,
    echarts_version: "6.1.0",
    render_profile_id: "ranking-svg-ja-jp-node22-echarts6.v1"
  };
}

function semanticModelFixture(): ChartModel {
  return {
    chart_model_contract_version: "1.0.0",
    chart_type: "ranking.horizontal_bar",
    analysis_result_sha256: SHA256,
    label_overlay_sha256: null,
    title: "出願人のランキング",
    dimension: { source_label: "applicant", display_label: "出願人", description: null },
    measure: { mode: "count", column: null },
    population: { input_rows: 1, analyzed_rows: 1 },
    rows: [{
      index: 0,
      row_kind: "dimension_value",
      source_label: "甲社",
      display_label: "甲社",
      description: null,
      semantic_label: "データ中の分類値",
      value: 1,
      count: 1,
      share: 1
    }],
    warnings: []
  };
}

function graphemes(value: string): string[] {
  return Array.from(segmenter.segment(value), ({ segment }) => segment);
}

function derivedTitle(value: string): string {
  const clusters = graphemes(value);
  return clusters.length + graphemes("のランキング").length <= 256
    ? `${value}のランキング`
    : `${clusters.slice(0, 249).join("")}…のランキング`;
}

function semanticDisplayTexts(model: ChartModel): string[] {
  const texts = [model.title, model.dimension.source_label, model.dimension.display_label];
  if (model.dimension.description !== null) texts.push(model.dimension.description);
  if (model.measure.column !== null) texts.push(model.measure.column);
  for (const row of model.rows) {
    texts.push(row.source_label, row.display_label, row.semantic_label);
    if (row.description !== null) texts.push(row.description);
  }
  texts.push(...model.warnings);
  return texts;
}

function fillDisplayBudget(model: ChartModel, target: number): void {
  const base = semanticDisplayTexts(model)
    .reduce((total, text) => total + graphemes(text).length, 0);
  let remaining = target - base;
  if (remaining < 0) throw new Error("semantic fixture exceeds target before filler");
  const warnings: string[] = [];
  while (remaining > 0) {
    const size = Math.min(4096, remaining);
    warnings.push("w".repeat(size));
    remaining -= size;
  }
  model.warnings = warnings;
}

function applySemanticOperation(operation: string): ChartModel {
  const model = structuredClone(semanticModelFixture());
  if (operation === "none") return model;
  if (operation === "unicode_graphemes") {
    model.dimension.display_label = "👩‍🔬é";
    model.title = derivedTitle(model.dimension.display_label);
    model.rows[0]!.display_label = "👩‍🔬é";
  } else if (operation === "nfd_dimension_title") {
    model.dimension.display_label = "e\u0301";
    model.title = derivedTitle(model.dimension.display_label);
  } else if (operation === "nfd_row") {
    model.rows[0]!.display_label = "e\u0301";
  } else if (operation === "nfd_warning") {
    model.warnings = ["e\u0301"];
  } else if (operation === "two_other") {
    model.population = { input_rows: 2, analyzed_rows: 2 };
    model.rows = [
      { ...model.rows[0]!, source_label: "その他", display_label: "その他", value: 1, share: 0.5 },
      {
        ...model.rows[0]!,
        index: 1,
        row_kind: "remainder",
        source_label: "その他",
        display_label: "その他",
        semantic_label: "上位表示外の合計",
        value: -1,
        share: 0.5
      }
    ];
  } else if (operation === "title_250" || operation === "title_251") {
    const size = operation === "title_250" ? 250 : 251;
    model.dimension.display_label = "あ".repeat(size);
    model.title = derivedTitle(model.dimension.display_label);
  } else if (operation === "description_256" || operation === "dimension_description_257") {
    model.dimension.description = "説".repeat(operation === "description_256" ? 256 : 257);
  } else if (operation === "measure_column_256" || operation === "measure_column_257") {
    model.measure = {
      mode: "sum",
      column: "列".repeat(operation === "measure_column_256" ? 256 : 257)
    };
  } else if (operation === "display_budget_20000" || operation === "display_budget_20001") {
    fillDisplayBudget(model, operation === "display_budget_20000" ? 20_000 : 20_001);
  } else if (operation === "title_mismatch") {
    model.title = "wrong title";
  } else if (operation === "unsafe_newline") {
    model.rows[0]!.display_label = "unsafe\nlabel";
  } else if (operation === "unsafe_c1") {
    model.warnings = ["a\u0080"];
  } else if (operation === "unsafe_bidi") {
    model.warnings = ["a\u202e"];
  } else if (operation === "unsafe_noncharacter") {
    model.warnings = ["a\ufdd0"];
  } else if (operation === "unsafe_plane_noncharacter") {
    model.warnings = [`a${String.fromCodePoint(0x1FFFF)}`];
  } else if (operation === "dimension_source_257") {
    model.dimension.source_label = "源".repeat(257);
  } else if (operation === "row_display_257") {
    model.rows[0]!.display_label = "行".repeat(257);
  } else if (operation === "row_description_257") {
    model.rows[0]!.description = "説".repeat(257);
  } else {
    throw new Error(`unknown semantic fixture operation: ${operation}`);
  }
  return model;
}

describe("build-time standalone validators", () => {
  it("exports the four runtime validators without AJV", async () => {
    const loaded = await loadStandaloneValidators();

    expect(loaded).toEqual({
      loaded: true,
      module: expect.objectContaining({
        validateChartModel: expect.any(Function),
        validateRenderSpec: expect.any(Function),
        validateRendererRequest: expect.any(Function),
        validateRendererRuntime: expect.any(Function)
      })
    });
  });

  it("accepts the valid request/runtime/model/spec corpus and rejects closed-shape mutations", async () => {
    const loaded = await loadStandaloneValidators();
    expect(loaded.loaded).toBe(true);
    if (!loaded.loaded) return;
    const validators = loaded.module;

    expect(validators.validateRendererRequest(requestFixture())).toBe(true);
    expect(validators.validateRendererRuntime(runtimeFixture())).toBe(true);
    expect(validators.validateChartModel(chartModelFixture())).toBe(true);
    expect(validators.validateRenderSpec(renderSpecFixture())).toBe(true);

    for (const invalid of [
      { ...requestFixture(), protocol_version: "2.0.0" },
      { ...requestFixture(), chart_model_b64: "AB==" },
      { ...requestFixture(), chart_model_sha256: 7 },
      { ...requestFixture(), extra: true },
      Object.fromEntries(Object.entries(requestFixture()).filter(([key]) => key !== "render_spec_b64"))
    ]) {
      expect(validators.validateRendererRequest(invalid)).toBe(false);
    }
    expect(validators.validateRendererRuntime({ ...runtimeFixture(), node_version: "22.20.0" })).toBe(false);

    for (const invalid of [
      { ...chartModelFixture(), chart_model_contract_version: "2.0.0" },
      { ...chartModelFixture(), rows: "not-an-array" },
      { ...chartModelFixture(), extra: true },
      Object.fromEntries(
        Object.entries(chartModelFixture()).filter(([key]) => key !== "population")
      )
    ]) {
      expect(validators.validateChartModel(invalid)).toBe(false);
    }

    for (const invalid of [
      { ...renderSpecFixture(), render_spec_contract_version: "2.0.0" },
      { ...renderSpecFixture(), height: "675" },
      { ...renderSpecFixture(), extra: true },
      Object.fromEntries(Object.entries(renderSpecFixture()).filter(([key]) => key !== "timezone"))
    ]) {
      expect(validators.validateRenderSpec(invalid)).toBe(false);
    }
  });

  it("rejects model row semantic drift and heights outside the row-count formula image", async () => {
    const loaded = await loadStandaloneValidators();
    expect(loaded.loaded).toBe(true);
    if (!loaded.loaded) return;
    const validators = loaded.module;
    const wrongIndex = chartModelFixture();
    wrongIndex.rows[1]!.index = 0;
    const wrongRemainder = chartModelFixture();
    wrongRemainder.rows[1]!.semantic_label = "データ中の分類値";

    expect(validators.validateChartModel(wrongIndex)).toBe(false);
    expect(validators.validateChartModel(wrongRemainder)).toBe(false);
    expect(validators.validateRenderSpec({ ...renderSpecFixture(), height: 676 })).toBe(false);
  });

  it("implements Python semantics with only the explicit NFC renderer restriction", async () => {
    const loaded = await loadStandaloneValidators();
    expect(loaded.loaded).toBe(true);
    if (!loaded.loaded) return;

    const intentionalDivergences: string[] = [];
    for (const semanticCase of semanticCorpus.semantic_cases) {
      expect(
        loaded.module.validateChartModel(applySemanticOperation(semanticCase.operation)),
        semanticCase.id
      ).toBe(semanticCase.renderer_valid);
      if (semanticCase.python_valid === semanticCase.renderer_valid) {
        expect(semanticCase.renderer_valid, `${semanticCase.id} parity`).toBe(semanticCase.python_valid);
      } else {
        intentionalDivergences.push(semanticCase.id);
      }
    }
    expect(intentionalDivergences).toEqual([
      "python-valid-renderer-invalid-nfd-dimension-title",
      "python-valid-renderer-invalid-nfd-row",
      "python-valid-renderer-invalid-nfd-warning"
    ]);
  });

  it("omits inert schema annotation URLs from runtime validator source", async () => {
    const source = await readFile(
      new URL("../src/generated/standalone-validators.js", import.meta.url),
      "utf8"
    );

    expect(source).not.toMatch(/https?:\/\//iu);
    expect(source).toContain("Python ChartModel semantics");
    expect(source).toContain("renderer-only NFC restriction");
  });
});
