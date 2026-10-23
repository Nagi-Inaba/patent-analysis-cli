import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import type { ChartModel } from "../src/payload.js";

type VisualRow = {
  row_kind: "dimension_value" | "remainder";
  source_label: string;
  display_label: string;
  value: number;
  count: number;
  share: number;
};

type VisualCase = {
  id: string;
  dimension_source: string;
  dimension_display: string;
  measure_mode: "count" | "sum" | "average" | "max" | "min";
  measure_column: string | null;
  rows?: VisualRow[];
  generated_row_count?: number;
};

const visualCases = JSON.parse(
  await readFile(new URL("../../tests/fixtures/renderer-visual-cases.json", import.meta.url), "utf8")
) as {
  cases: VisualCase[];
  numeric_cases: Array<{
    id: string;
    lexeme: string;
    python_accepts: boolean;
    renderer_accepts: boolean;
  }>;
};

function sha256(value: Buffer): string {
  return createHash("sha256").update(value).digest("hex");
}

function canonicalJson(value: unknown): Buffer {
  const canonicalize = (nested: unknown): unknown => {
    if (Array.isArray(nested)) return nested.map(canonicalize);
    if (nested !== null && typeof nested === "object") {
      return Object.fromEntries(
        Object.entries(nested)
          .sort(([left], [right]) => (left < right ? -1 : left > right ? 1 : 0))
          .map(([key, item]) => [key, canonicalize(item)])
      );
    }
    return nested;
  };
  return Buffer.from(JSON.stringify(canonicalize(value)), "utf8");
}

function runtimeFixture() {
  return {
    node_version: "24.22.1",
    echarts_version: "6.1.0",
    renderer_build_digest: "a".repeat(64),
    render_profile_id: "ranking-svg-ja-jp-node24-echarts6.v1"
  };
}

function renderSpecBytes(rowCount = 2) {
  return canonicalJson({
    render_spec_contract_version: "1.0.0",
    renderer_kind: "ranking.horizontal_bar.svg",
    locale: "ja-JP",
    timezone: "UTC",
    width: 1200,
    height: Math.max(675, 160 + 36 * rowCount),
    font_family: "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif",
    animation: false,
    axis_label_max_graphemes: 28,
    echarts_version: "6.1.0",
    render_profile_id: "ranking-svg-ja-jp-node24-echarts6.v1"
  });
}

function rowsForCase(fixture: VisualCase): VisualRow[] {
  return fixture.rows ?? Array.from({ length: fixture.generated_row_count ?? 0 }, (_value, index) => ({
    row_kind: "dimension_value" as const,
    source_label: `分類${index}`,
    display_label: `分類${index}`,
    value: index + 1,
    count: 1,
    share: 1 / (fixture.generated_row_count ?? 1)
  }));
}

function chartModelBytes(fixture: VisualCase): Buffer {
  const rows = rowsForCase(fixture);
  const analyzedRows = rows.reduce((total, row) => total + row.count, 0);
  return canonicalJson({
    chart_model_contract_version: "1.0.0",
    chart_type: "ranking.horizontal_bar",
    analysis_result_sha256: "b".repeat(64),
    label_overlay_sha256: null,
    title: `${fixture.dimension_display}のランキング`,
    dimension: {
      source_label: fixture.dimension_source,
      display_label: fixture.dimension_display,
      description: null
    },
    measure: { mode: fixture.measure_mode, column: fixture.measure_column },
    population: { input_rows: analyzedRows, analyzed_rows: analyzedRows },
    rows: rows.map((row, index) => ({
      index,
      row_kind: row.row_kind,
      source_label: row.source_label,
      display_label: row.display_label,
      description: null,
      semantic_label: row.row_kind === "remainder" ? "上位表示外の合計" : "データ中の分類値",
      value: row.value,
      count: row.count,
      share: row.share
    })),
    warnings: []
  });
}

function requestTransfer(
  modelBytes: Buffer,
  modelDigest = sha256(modelBytes),
  rowCount = 2
): string {
  const specBytes = renderSpecBytes(rowCount);
  const request = canonicalJson({
    protocol_version: "1.0.0",
    chart_model_b64: modelBytes.toString("base64"),
    chart_model_sha256: modelDigest,
    render_spec_b64: specBytes.toString("base64"),
    render_spec_sha256: sha256(specBytes)
  });
  return request.toString("base64");
}

async function render(transfer: string) {
  const modulePath = "../src/index.ts";
  const renderer = await import(modulePath);
  return JSON.parse(renderer.renderRequest(transfer, JSON.stringify(runtimeFixture()))) as {
    ok: boolean;
    runtime: ReturnType<typeof runtimeFixture>;
    svg_b64?: string;
    error?: { code: string; message: string };
  };
}

describe("deterministic renderer request processing", () => {
  it("compares both payload digests before parsing either inner JSON object", async () => {
    const malformedModel = Buffer.from("{", "utf8");

    await expect(render(requestTransfer(malformedModel, "0".repeat(64)))).resolves.toMatchObject({
      ok: false,
      error: {
        code: "digest.mismatch",
        message: "Renderer payload digest does not match"
      }
    });
    await expect(render(requestTransfer(malformedModel))).resolves.toMatchObject({
      ok: false,
      error: {
        code: "schema.invalid",
        message: "Renderer input was rejected"
      }
    });
  });

  it("returns only fixed runtime, protocol, size, and bound-height failures", async () => {
    const modulePath = "../src/index.ts";
    const renderer = await import(modulePath);
    const invalidRuntime = JSON.parse(renderer.renderRequest(
      requestTransfer(Buffer.from("{}", "utf8")),
      JSON.stringify({ ...runtimeFixture(), node_version: "22.20.0" })
    ));
    expect(invalidRuntime).toMatchObject({
      ok: false,
      error: { code: "runtime.mismatch", message: "Renderer runtime does not match" }
    });

    await expect(render(Buffer.from("{}", "utf8").toString("base64"))).resolves.toMatchObject({
      ok: false,
      error: { code: "protocol.invalid", message: "Renderer protocol is invalid" }
    });
    await expect(render(Buffer.alloc(3 * 1024 * 1024 + 1).toString("base64"))).resolves.toMatchObject({
      ok: false,
      error: { code: "payload.too_large", message: "Renderer payload is too large" }
    });

    const fixture = visualCases.cases.find(({ id }) => id === "positive");
    if (fixture === undefined) throw new Error("Missing positive visual fixture");
    await expect(render(requestTransfer(chartModelBytes(fixture), undefined, 15))).resolves.toMatchObject({
      ok: false,
      error: { code: "schema.invalid", message: "Renderer input was rejected" }
    });
  });

  it("rejects noncanonical inner JSON before accepting schema-valid objects", async () => {
    const fixture = visualCases.cases.find(({ id }) => id === "positive");
    if (fixture === undefined) throw new Error("Missing positive visual fixture");
    const canonical = chartModelBytes(fixture);
    const text = canonical.toString("utf8");
    const parsed = JSON.parse(text) as Record<string, unknown>;
    const mutations = [
      Buffer.concat([Buffer.from(" "), canonical]),
      Buffer.from(`${text.slice(0, -1)},\"warnings\":[]}`, "utf8"),
      Buffer.from(JSON.stringify({ warnings: parsed.warnings, ...parsed }), "utf8"),
      Buffer.from(text.replace('"warnings"', '"warni\\u006egs"'), "utf8"),
      Buffer.from(text.replace('"value":5', '"value":-0'), "utf8")
    ];

    for (const modelBytes of mutations) {
      await expect(render(requestTransfer(modelBytes))).resolves.toMatchObject({
        ok: false,
        error: { code: "schema.invalid", message: "Renderer input was rejected" }
      });
    }
  });

  it("matches signed Python canonical classification for every shared numeric lexeme", async () => {
    const fixture = visualCases.cases.find(({ id }) => id === "positive");
    if (fixture === undefined) throw new Error("Missing positive visual fixture");
    const canonical = chartModelBytes(fixture).toString("utf8");
    const payloadPath = "../src/payload.ts";
    const payload = await import(payloadPath);

    for (const numericCase of visualCases.numeric_cases) {
      const modelBytes = Buffer.from(
        canonical.replace('"value":5', `"value":${numericCase.lexeme}`),
        "utf8"
      );
      const result = payload.processRendererTransfer(
        requestTransfer(modelBytes),
        JSON.stringify(runtimeFixture())
      );
      expect(result.ok, numericCase.id).toBe(numericCase.renderer_accepts);
      if (result.ok) {
        expect(result.model.rows[0]!.value, `${numericCase.id} parsed value`).toBe(
          Number(numericCase.lexeme)
        );
      }
    }
  });

  it("never aliases an unsafe canonical integer into a different rendered label", async () => {
    const fixture = visualCases.cases.find(({ id }) => id === "positive");
    if (fixture === undefined) throw new Error("Missing positive visual fixture");
    const modelBytes = Buffer.from(
      chartModelBytes(fixture).toString("utf8")
        .replace('"value":5', '"value":9007199254740993'),
      "utf8"
    );
    const transfer = requestTransfer(modelBytes);
    const request = JSON.parse(Buffer.from(transfer, "base64").toString("utf8")) as {
      chart_model_b64: string;
      chart_model_sha256: string;
    };
    expect(Buffer.from(request.chart_model_b64, "base64")).toEqual(modelBytes);
    expect(request.chart_model_sha256).toBe(sha256(modelBytes));

    const response = await render(transfer);
    if (response.ok) {
      const svg = Buffer.from(response.svg_b64 ?? "", "base64").toString("utf8");
      expect(svg, "canonical 9007199254740993 was numerically aliased").toContain(
        ">9007199254740993</text>"
      );
    }
    expect(response).toMatchObject({
      ok: false,
      error: { code: "schema.invalid", message: "Renderer input was rejected" }
    });
  });

  it("renders exact safe-integer boundaries and rejects every integer outside them", async () => {
    const fixture = visualCases.cases.find(({ id }) => id === "positive");
    if (fixture === undefined) throw new Error("Missing positive visual fixture");
    const canonical = chartModelBytes(fixture).toString("utf8");
    for (const lexeme of ["9007199254740991", "-9007199254740991"]) {
      const response = await render(requestTransfer(Buffer.from(
        canonical.replace('"value":5', `"value":${lexeme}`),
        "utf8"
      )));
      expect(response.ok, lexeme).toBe(true);
      const svg = Buffer.from(response.svg_b64 ?? "", "base64").toString("utf8");
      expect(svg).toContain(`>${lexeme}</text>`);
    }
    for (const lexeme of [
      "9007199254740992",
      "-9007199254740992",
      "9007199254740993",
      "123456789012345678901234567890"
    ]) {
      await expect(render(requestTransfer(Buffer.from(
        canonical.replace('"value":5', `"value":${lexeme}`),
        "utf8"
      )))).resolves.toMatchObject({
        ok: false,
        error: { code: "schema.invalid", message: "Renderer input was rejected" }
      });
    }
  });

  it("rejects NFD labels, derived titles, and warnings as schema.invalid without normalization", async () => {
    const fixture = visualCases.cases.find(({ id }) => id === "positive");
    if (fixture === undefined) throw new Error("Missing positive visual fixture");
    const base = JSON.parse(chartModelBytes(fixture).toString("utf8")) as ChartModel;
    const rowLabel = structuredClone(base);
    rowLabel.rows[0]!.display_label = "e\u0301";
    const derivedTitle = structuredClone(base);
    derivedTitle.dimension.display_label = "e\u0301";
    derivedTitle.title = "e\u0301のランキング";
    const warning = structuredClone(base);
    warning.warnings = ["e\u0301"];

    for (const model of [rowLabel, derivedTitle, warning]) {
      await expect(render(requestTransfer(canonicalJson(model)))).resolves.toMatchObject({
        ok: false,
        error: { code: "schema.invalid", message: "Renderer input was rejected" }
      });
    }
  });

  it("renders the positive visual case with the fixed ECharts SSR profile", async () => {
    const fixture = visualCases.cases.find(({ id }) => id === "positive");
    if (fixture === undefined) throw new Error("Missing positive visual fixture");

    const response = await render(requestTransfer(chartModelBytes(fixture)));

    expect(response).toMatchObject({ ok: true, runtime: runtimeFixture() });
    expect(response.svg_b64).toBeTypeOf("string");
    const svg = Buffer.from(response.svg_b64 ?? "", "base64").toString("utf8");
    expect(svg).toContain('<svg xmlns="http://www.w3.org/2000/svg"');
    expect(svg).toContain('width="1200"');
    expect(svg).toContain('height="675"');
    expect(svg).toContain("#FFFFFF");
    expect(svg).toContain("#2563EB");
    expect(svg).toContain("#E2E8F0");
    expect(svg).toContain("Yu Gothic UI, Yu Gothic, Meiryo, sans-serif");
    expect(svg).toContain("出願人のランキング（件数）");
    expect(svg.indexOf("甲社")).toBeLessThan(svg.indexOf("乙社"));
    expect(svg).toMatch(/>5<\/text>/u);
    expect(svg).toMatch(/>3<\/text>/u);
    expect(svg).toMatch(/A4 4 0 0 1/u);
    expect(svg).not.toMatch(/<(?:style|script)\b|\s(?:style|class|pointer-events|ecmeta_[a-z_]+)=/u);
    expect(svg).not.toContain("xmlns:xlink");
    expect(svg.endsWith("\n")).toBe(true);
  });

  it("preserves signed/source data and the fixed profile across every declared visual case", async () => {
    const rendered = new Map<string, string>();
    for (const fixture of visualCases.cases) {
      const rows = rowsForCase(fixture);
      const response = await render(
        requestTransfer(chartModelBytes(fixture), undefined, rows.length)
      );
      expect(response.ok, fixture.id).toBe(true);
      const svg = Buffer.from(response.svg_b64 ?? "", "base64").toString("utf8");
      expect(svg).not.toMatch(/<(?:style|script)\b|\s(?:style|class|pointer-events|ecmeta_[a-z_]+)=/u);
      expect(svg).toContain(`height="${Math.max(675, 160 + 36 * rows.length)}"`);
      expect(svg.normalize("NFC"), fixture.id).toBe(svg);
      rendered.set(fixture.id, svg);
    }

    const mixed = rendered.get("mixed-signed")!;
    expect(mixed).toContain("#2563EB");
    expect(mixed).toContain("#DC2626");
    for (const value of ["12.5", "0", "-7.25"]) expect(mixed).toContain(`>${value}</text>`);
    expect(mixed).toContain('stroke="#0F172A"');
    expect(mixed).toContain("技術分類のランキング（合計（スコア））");

    const remainder = rendered.get("two-other-labels")!;
    expect(remainder.match(/>その他<\/text>/gu)).toHaveLength(2);
    expect(remainder).toContain("#94A3B8");
    expect(remainder).toContain('stroke-dasharray="4 2"');
    expect(remainder.lastIndexOf(">1</text>")).toBeLessThan(remainder.lastIndexOf(">-1</text>"));

    const long = rendered.get("long-japanese")!;
    const longFixture = visualCases.cases.find(({ id }) => id === "long-japanese")!;
    const fullLabel = rowsForCase(longFixture)[0]!.display_label;
    const truncated = `${Array.from(
      new Intl.Segmenter("ja-JP", { granularity: "grapheme" }).segment(fullLabel)
    ).slice(0, 27).map(({ segment }) => segment).join("")}…`;
    expect(long).toContain(`>${truncated}</text>`);
    expect(long).not.toContain(`>${fullLabel}</text>`);

    const empty = rendered.get("empty")!;
    expect(empty).toContain("表示できるランキングデータがありません");
    expect(empty).not.toContain("#2563EB");
    expect(empty).not.toContain("#DC2626");
    expect(empty).not.toContain("#94A3B8");

    const maximum = rendered.get("max-rows-generated")!;
    expect(maximum).toContain('height="3796"');
    expect(maximum.indexOf(">分類0</text>")).toBeLessThan(maximum.indexOf(">分類100</text>"));

    const large = rendered.get("large-signed-values")!;
    expect(large).toContain(">999999999.25</text>");
    expect(large).toContain(">-999999999.5</text>");
  });
});
