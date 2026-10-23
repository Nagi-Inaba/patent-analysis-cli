import { describe, expect, it } from "vitest";
import {
  buildCompositionOption,
  buildSeriesOption,
  renderCategoricalModelToRawSvg,
  renderRequest
} from "../src/categorical-index.js";
import {
  decodeCanonicalBase64,
  encodeCanonicalBase64,
  encodeUtf8,
  sha256Hex
} from "../src/categorical-payload.js";

const seriesModel = {
  chart_model_contract_version: "1.0.0",
  chart_type: "series.line",
  mark: "series-line-svg.v1",
  analysis_result_sha256: "a".repeat(64),
  title: "年次推移",
  measure: { mode: "count", role: null },
  x: ["2020", "2021"],
  series: [
    { label: "A社", values: [1, 2], row_counts: [1, 2], is_other: false },
    { label: "B社", values: [0, 1], row_counts: [0, 1], is_other: false }
  ],
  population: { input_rows: 3, analyzed_rows: 3, excluded_rows: 0 },
  warnings: []
} as const;

const stackedModel = {
  ...seriesModel,
  chart_type: "series.stacked-bar",
  mark: "series-stacked-bar-svg.v1"
} as const;

const compositionModel = {
  chart_model_contract_version: "1.0.0",
  chart_type: "composition.bar",
  mark: "composition-bar-svg.v1",
  analysis_result_sha256: "b".repeat(64),
  title: "構成比",
  measure: { mode: "sum", role: "score" },
  items: [
    {
      label: "A社",
      value: 1000,
      row_count: 1,
      share: 0.25,
      share_basis: "row_count",
      is_other: false
    },
    {
      label: "B社",
      value: 1,
      row_count: 3,
      share: 0.75,
      share_basis: "row_count",
      is_other: false
    }
  ],
  population: { input_rows: 4, analyzed_rows: 4, excluded_rows: 0 },
  warnings: []
} as const;

const pieModel = {
  ...compositionModel,
  chart_type: "composition.pie",
  mark: "composition-pie-svg.v1"
} as const;

const emptySeriesModel = {
  ...seriesModel,
  x: [],
  series: [],
  population: { input_rows: 0, analyzed_rows: 0, excluded_rows: 0 }
} as const;

const lineSpec = {
  render_spec_contract_version: "1.0.0",
  renderer_kind: "series.line.svg",
  locale: "ja-JP",
  timezone: "UTC",
  width: 1200,
  height: 675,
  font_family: "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif",
  animation: false,
  axis_label_max_graphemes: 28,
  echarts_version: "6.1.0",
  render_profile_id: "categorical-svg-ja-jp-node24-echarts6.v1"
} as const;

const stackedSpec = {
  ...lineSpec,
  renderer_kind: "series.stacked-bar.svg"
} as const;

const barSpec = {
  ...lineSpec,
  renderer_kind: "composition.bar.svg"
} as const;

const pieSpec = {
  ...lineSpec,
  renderer_kind: "composition.pie.svg"
} as const;

const runtime = {
  node_version: "24.22.1",
  echarts_version: "6.1.0",
  renderer_build_digest: "c".repeat(64),
  render_profile_id: "categorical-svg-ja-jp-node24-echarts6.v1"
} as const;

function canonicalValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, item]) => [key, canonicalValue(item)])
    );
  }
  return value;
}

function canonicalBytes(value: unknown): Uint8Array {
  return encodeUtf8(JSON.stringify(canonicalValue(value)));
}

function buildRequest(modelValue: unknown, specValue: unknown): string {
  const modelBytes = canonicalBytes(modelValue);
  const specBytes = canonicalBytes(specValue);
  const requestBytes = canonicalBytes({
    chart_model_b64: encodeCanonicalBase64(modelBytes),
    chart_model_sha256: sha256Hex(modelBytes),
    protocol_version: "1.0.0",
    render_spec_b64: encodeCanonicalBase64(specBytes),
    render_spec_sha256: sha256Hex(specBytes)
  });
  return encodeCanonicalBase64(requestBytes);
}

function checkedRecord(value: unknown, label: string): Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new TypeError(`${label} must be an object`);
  }
  return value as Record<string, unknown>;
}

function checkedRecords(value: unknown, label: string): Record<string, unknown>[] {
  if (!Array.isArray(value)) throw new TypeError(`${label} must be an array`);
  return value.map((item, index) => checkedRecord(item, `${label}[${index}]`));
}

describe("categorical renderer options", () => {
  it("builds fixed line and stacked-bar options", () => {
    const line = buildSeriesOption(seriesModel, lineSpec);
    const stacked = buildSeriesOption(stackedModel, stackedSpec);
    const lineXAxis = checkedRecord(line.xAxis, "line.xAxis");
    const lineSeries = checkedRecords(line.series, "line.series");
    const stackedSeries = checkedRecords(stacked.series, "stacked.series");

    expect(line.animation).toBe(false);
    expect(lineXAxis.data).toEqual(["2020", "2021"]);
    expect(lineSeries.map((item) => item.type)).toEqual(["line", "line"]);
    expect(stackedSeries.map((item) => item.type)).toEqual(["bar", "bar"]);
    expect(stackedSeries.map((item) => item.stack)).toEqual(["total", "total"]);
  });

  it("keeps analytical values for bars but declared shares for pie geometry", () => {
    const bar = buildCompositionOption(compositionModel, barSpec);
    const pie = buildCompositionOption(pieModel, pieSpec);
    const barSeries = checkedRecords(bar.series, "bar.series");
    const pieSeries = checkedRecords(pie.series, "pie.series");
    const barData = checkedRecords(barSeries[0]?.data, "bar.series[0].data");
    const pieData = checkedRecords(pieSeries[0]?.data, "pie.series[0].data");

    expect(barData.map((item) => item.value)).toEqual([1000, 1]);
    expect(pieData.map((item) => item.value)).toEqual([0.25, 0.75]);
  });

  it("renders deterministic explicit empty states", () => {
    const option = buildSeriesOption(emptySeriesModel, lineSpec);
    const title = checkedRecord(option.title, "option.title");

    expect(title.subtext).toBe("表示できる年次推移データがありません");
    expect(renderCategoricalModelToRawSvg(emptySeriesModel, lineSpec)).toContain(
      "表示できる年次推移データがありません"
    );
  });

  it("renders safe SVGs for all four closed marks", () => {
    const rendered = [
      renderCategoricalModelToRawSvg(seriesModel, lineSpec),
      renderCategoricalModelToRawSvg(stackedModel, stackedSpec),
      renderCategoricalModelToRawSvg(compositionModel, barSpec),
      renderCategoricalModelToRawSvg(pieModel, pieSpec)
    ];

    for (const svg of rendered) {
      expect(svg).toContain("<svg");
      for (const forbidden of [
        "<script",
        "<foreignObject",
        "xmlns:xlink",
        "baseProfile=",
        "xml:space",
        "<linearGradient",
        "<stop"
      ]) {
        expect(svg).not.toContain(forbidden);
      }
    }
  });
});

describe("categorical renderer wire protocol", () => {
  it("serializes protocol failures instead of throwing", () => {
    const serialized = renderRequest("not-base64", JSON.stringify(runtime));
    const response = JSON.parse(serialized) as {
      ok: boolean;
      error: { code: string };
    };

    expect(response.ok).toBe(false);
    expect(response.error.code).toBe("protocol.invalid");
  });

  it("rejects mismatched mark/type/spec combinations", () => {
    const mismatched = {
      ...seriesModel,
      mark: "series-stacked-bar-svg.v1"
    };
    const serialized = renderRequest(
      buildRequest(mismatched, lineSpec),
      JSON.stringify(runtime)
    );
    const response = JSON.parse(serialized) as {
      ok: boolean;
      error: { code: string };
    };

    expect(response.ok).toBe(false);
    expect(response.error.code).toBe("schema.invalid");
  });

  it("serializes successful SVG bytes as canonical base64", () => {
    const serialized = renderRequest(
      buildRequest(pieModel, pieSpec),
      JSON.stringify(runtime)
    );
    const response = JSON.parse(serialized) as {
      ok: boolean;
      svg_b64?: string;
      error?: { code: string; message: string };
    };
    if (!response.ok || response.svg_b64 === undefined) {
      throw new Error(`unexpected categorical failure: ${JSON.stringify(response)}`);
    }

    const svg = new TextDecoder().decode(
      decodeCanonicalBase64(response.svg_b64, 8 * 1024 * 1024)
    );
    expect(svg).toContain("<svg");
  });
});

describe("categorical palettes", () => {
  type LineSeries = { lineStyle: { color: string; width: number; type?: unknown }; symbol: string };

  it("keeps the standard colours and plain lines by default", () => {
    const series = buildSeriesOption(seriesModel, lineSpec).series as LineSeries[];

    expect(series.map((item) => item.lineStyle.color)).toEqual(["#0f766e", "#2563eb"]);
    expect(series.every((item) => item.lineStyle.width === 2 && item.lineStyle.type === undefined)).toBe(true);
    expect(series.every((item) => item.symbol === "circle")).toBe(true);
  });

  it("gives each line series its own line type and marker under an alternate palette", () => {
    const series = buildSeriesOption(seriesModel, { ...lineSpec, palette: "colorblind" }).series as LineSeries[];

    expect(series.map((item) => item.lineStyle.color)).toEqual(["#0072b2", "#009e73"]);
    expect(series.map((item) => item.lineStyle.type)).toEqual(["solid", "dashed"]);
    expect(series.map((item) => item.symbol)).toEqual(["circle", "rect"]);
    expect(series.every((item) => item.lineStyle.width === 3)).toBe(true);
  });

  it.each(["colorblind", "monochrome", "high-contrast"] as const)(
    "renders all four categorical marks with the %s palette inside the SVG policy",
    (palette) => {
      expect(() => renderCategoricalModelToRawSvg(seriesModel, { ...lineSpec, palette })).not.toThrow();
      expect(() => renderCategoricalModelToRawSvg(stackedModel, { ...stackedSpec, palette })).not.toThrow();
      expect(() => renderCategoricalModelToRawSvg(compositionModel, { ...barSpec, palette })).not.toThrow();
      expect(() => renderCategoricalModelToRawSvg(pieModel, { ...pieSpec, palette })).not.toThrow();
    }
  );
});
