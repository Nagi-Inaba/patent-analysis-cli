import { describe, expect, it } from "vitest";
import {
  buildMatrixOption,
  renderMatrixModelToRawSvg,
  renderRequest
} from "../src/matrix-index.js";
import {
  decodeCanonicalBase64,
  encodeCanonicalBase64,
  encodeUtf8,
  sha256Hex
} from "../src/matrix-payload.js";

const model = {
  chart_model_contract_version: "1.0.0",
  chart_type: "matrix.bubble",
  mark: "matrix-bubble-svg.v1",
  analysis_result_sha256: "a".repeat(64),
  title: "出願人 × 分類",
  x_axis: {
    role: "applicant",
    categories: [
      { id: "x:0", index: 0, label: "A社", count: 2, is_other: false },
      { id: "x:1", index: 1, label: "B社", count: 1, is_other: false }
    ]
  },
  y_axis: {
    role: "classification",
    categories: [
      { id: "y:0", index: 0, label: "G06F", count: 2, is_other: false },
      { id: "y:1", index: 1, label: "H04L", count: 1, is_other: false }
    ]
  },
  cells: [
    {
      x_index: 0,
      y_index: 0,
      x_label: "A社",
      y_label: "G06F",
      value: 2,
      row_count: 2
    },
    {
      x_index: 1,
      y_index: 0,
      x_label: "B社",
      y_label: "G06F",
      value: 1,
      row_count: 1
    },
    {
      x_index: 0,
      y_index: 1,
      x_label: "A社",
      y_label: "H04L",
      value: 1,
      row_count: 1
    }
  ],
  population: { input_rows: 3, analyzed_rows: 2, excluded_rows: 1 },
  warnings: []
} as const;

const heatmapModel = {
  ...model,
  chart_type: "matrix.heatmap",
  mark: "matrix-heatmap-svg.v1"
} as const;

const emptyBubbleModel = {
  ...model,
  x_axis: { ...model.x_axis, categories: [] },
  y_axis: { ...model.y_axis, categories: [] },
  cells: [],
  population: { input_rows: 0, analyzed_rows: 0, excluded_rows: 0 }
} as const;

const bubbleSpec = {
  render_spec_contract_version: "1.0.0",
  renderer_kind: "matrix.bubble.svg",
  locale: "ja-JP",
  timezone: "UTC",
  width: 1200,
  height: 675,
  font_family: "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif",
  animation: false,
  axis_label_max_graphemes: 28,
  echarts_version: "6.1.0",
  render_profile_id: "matrix-svg-ja-jp-node24-echarts6.v1"
} as const;

const heatmapSpec = {
  ...bubbleSpec,
  renderer_kind: "matrix.heatmap.svg"
} as const;

const runtime = {
  node_version: "24.22.1",
  echarts_version: "6.1.0",
  renderer_build_digest: "b".repeat(64),
  render_profile_id: "matrix-svg-ja-jp-node24-echarts6.v1"
} as const;

type MatrixOptionView = {
  backgroundColor: string;
  textStyle: { color?: string };
  title: {
    subtext?: string;
    textStyle?: { color?: string };
    subtextStyle?: { color?: string };
  };
  visualMap?: {
    show: boolean;
    inRange: { color: string[] };
  };
  series: Array<{
    data: unknown[];
    itemStyle?: { color?: string };
    label?: { color?: string; textBorderWidth?: number };
  }>;
};

function optionView(value: ReturnType<typeof buildMatrixOption>): MatrixOptionView {
  return value as unknown as MatrixOptionView;
}

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

describe("matrix renderer options", () => {
  it("builds a fixed bubble option from neutral cells", () => {
    const option = buildMatrixOption(model, bubbleSpec);

    expect(option.animation).toBe(false);
    expect(option.xAxis.data).toEqual(["A社", "B社"]);
    expect(option.yAxis.data).toEqual(["G06F", "H04L"]);
    expect(option.series).toHaveLength(1);
    expect(option.series[0].type).toBe("scatter");
    expect(option.series[0].data).toEqual([
      [0, 0, 2],
      [1, 0, 1],
      [0, 1, 1]
    ]);
  });

  it("builds a fixed heatmap option without caller code", () => {
    const option = buildMatrixOption(heatmapModel, heatmapSpec);

    expect(option.animation).toBe(false);
    expect(option.series).toHaveLength(1);
    expect(option.series[0].type).toBe("heatmap");
    expect(JSON.stringify(option)).not.toContain("formatter");
    expect(JSON.stringify(option)).not.toContain("function");
  });

  it("uses fixed high-contrast palette and visible count keys", () => {
    const bubble = optionView(buildMatrixOption(model, bubbleSpec));
    const heatmap = optionView(buildMatrixOption(heatmapModel, heatmapSpec));

    expect(bubble.backgroundColor).toBe("#ffffff");
    expect(bubble.textStyle.color).toBe("#0f172a");
    expect(bubble.title.textStyle?.color).toBe("#0f172a");
    expect(bubble.title.subtextStyle?.color).toBe("#475569");
    expect(bubble.title.subtext).toBe("件数は円の面積で表現（最大 2）");
    expect(bubble.series[0].itemStyle?.color).toBe("#0f766e");

    expect(heatmap.title.subtext).toBe("件数は色の濃さで表現（最大 2）");
    expect(heatmap.visualMap?.show).toBe(false);
    expect(heatmap.visualMap?.inRange.color).toEqual([
      "#f1f5f9",
      "#5eead4",
      "#14b8a6"
    ]);
    expect(heatmap.series[0].label?.color).toBe("#0f172a");
    expect(heatmap.series[0].label?.textBorderWidth).toBe(0);

    expect(renderMatrixModelToRawSvg(model, bubbleSpec)).toContain(
      "件数は円の面積で表現"
    );
    expect(renderMatrixModelToRawSvg(heatmapModel, heatmapSpec)).toContain(
      "件数は色の濃さで表現"
    );
  });

  it("draws no grid lines on the bubble map but keeps them on the heatmap", () => {
    const bubble = buildMatrixOption(model, bubbleSpec);
    const heatmap = buildMatrixOption(heatmapModel, heatmapSpec);

    expect(bubble.xAxis.splitLine).toEqual({ show: false });
    expect(bubble.yAxis.splitLine).toEqual({ show: false });
    expect(heatmap.xAxis.splitLine).toEqual({ lineStyle: { color: "#cbd5e1" } });
    expect(heatmap.yAxis.splitLine).toEqual({ lineStyle: { color: "#cbd5e1" } });
  });

  it("hides bubble count labels by default and draws them only when asked", () => {
    const hidden = renderMatrixModelToRawSvg(model, bubbleSpec);
    const shown = renderMatrixModelToRawSvg(model, { ...bubbleSpec, value_labels: "shown" });
    const explicit = renderMatrixModelToRawSvg(model, { ...bubbleSpec, value_labels: "hidden" });
    const countTexts = (svg: string, value: string) =>
      [...svg.matchAll(new RegExp(`<text[^>]*>${value}</text>`, "gu"))].length;

    expect(buildMatrixOption(model, bubbleSpec).series[0].label).toEqual({ show: false });
    // The sample cells carry counts 2, 1 and 1.
    expect(countTexts(hidden, "2")).toBe(0);
    expect(countTexts(hidden, "1")).toBe(0);
    expect(explicit).toBe(hidden);
    expect(countTexts(shown, "2")).toBe(1);
    expect(countTexts(shown, "1")).toBe(2);
  });

  it("leaves the heatmap cell counts untouched by the bubble label choice", () => {
    const option = optionView(buildMatrixOption(heatmapModel, heatmapSpec));
    expect(option.series[0].label?.color).toBe("#0f172a");
    expect(renderMatrixModelToRawSvg(heatmapModel, heatmapSpec)).toContain(">2</text>");
  });

  it("recolours the bubble and heatmap for an alternate palette and leaves the default alone", () => {
    const bubble = optionView(buildMatrixOption(model, { ...bubbleSpec, palette: "colorblind" }));
    const heatmap = optionView(buildMatrixOption(heatmapModel, { ...heatmapSpec, palette: "colorblind" }));

    expect(bubble.series[0].itemStyle?.color).toBe("#0072b2");
    expect(optionView(buildMatrixOption(model, { ...bubbleSpec, palette: "standard" })).series[0].itemStyle?.color)
      .toBe("#0f766e");
    expect(heatmap.visualMap?.inRange.color).toEqual(["#eaf2f9", "#6baed6", "#08519c"]);
    // The darkest cell (count 2 of max 2) carries white ink; the lightest cell keeps the dark text colour.
    const cells = heatmap.series[0].data as Array<{ value: number[]; label: { color: string } }>;
    expect(cells.find((cell) => cell.value[2] === 2)?.label.color).toBe("#ffffff");
    expect(cells.find((cell) => cell.value[2] === 1)?.label.color).toBe("#0f172a");
  });

  it.each(["colorblind", "monochrome", "high-contrast"] as const)(
    "renders both matrix marks with the %s palette inside the SVG policy",
    (palette) => {
      expect(() =>
        renderMatrixModelToRawSvg(model, { ...bubbleSpec, palette, value_labels: "shown" })
      ).not.toThrow();
      expect(() => renderMatrixModelToRawSvg(heatmapModel, { ...heatmapSpec, palette })).not.toThrow();
    }
  );

  it("renders an explicit empty state", () => {
    const option = optionView(buildMatrixOption(emptyBubbleModel, bubbleSpec));

    expect(option.title.subtext).toBe(
      "表示できるマトリクスデータがありません"
    );
    expect(renderMatrixModelToRawSvg(emptyBubbleModel, bubbleSpec)).toContain(
      "表示できるマトリクスデータがありません"
    );
  });

  it("renders a safe bubble SVG before wire serialization", () => {
    const svg = renderMatrixModelToRawSvg(model, bubbleSpec);

    expect(svg).toContain("<svg");
    expect(svg).not.toContain("<script");
  });

  it("renders a safe heatmap SVG within the fixed normalizer subset", () => {
    const svg = renderMatrixModelToRawSvg(heatmapModel, heatmapSpec);

    expect(svg).toContain("<svg");
    expect(svg).not.toContain("<script");
    for (const forbidden of [
      "xmlns:xlink",
      "baseProfile=",
      "version=",
      "xml:space",
      "<linearGradient",
      "<stop",
      "paint-order=",
      "stroke-miterlimit="
    ]) {
      expect(svg).not.toContain(forbidden);
    }
  });
});

describe("matrix renderer wire response", () => {
  it("serializes failure responses for the fixed bootstrap", () => {
    const serialized = renderRequest("not-canonical-base64", JSON.stringify(runtime));

    expect(typeof serialized).toBe("string");
    const response = JSON.parse(serialized as unknown as string) as {
      ok: boolean;
      error: { code: string };
    };
    expect(response.ok).toBe(false);
    expect(response.error.code).toBe("protocol.invalid");
  });

  it("serializes successful SVG bytes as canonical base64", () => {
    const serialized = renderRequest(
      buildRequest(model, bubbleSpec),
      JSON.stringify(runtime)
    );

    expect(typeof serialized).toBe("string");
    const response = JSON.parse(serialized as unknown as string) as {
      ok: boolean;
      svg_b64: string;
      svg?: string;
      error?: { code: string; message: string };
    };
    if (!response.ok) {
      throw new Error(`unexpected Matrix wire failure: ${JSON.stringify(response)}`);
    }
    expect(response.svg).toBeUndefined();
    expect(response.svg_b64).toMatch(/^[A-Za-z0-9+/]+={0,2}$/u);
    const svg = new TextDecoder().decode(
      decodeCanonicalBase64(response.svg_b64, 8 * 1024 * 1024)
    );
    expect(svg).toContain("<svg");
  });
});

const pieModel = {
  ...model,
  pie: {
    role: "year",
    categories: [
      { id: "p:0", index: 0, label: "2020", count: 2, is_other: false },
      { id: "p:1", index: 1, label: "2021", count: 1, is_other: false },
      { id: "p:2", index: 2, label: "その他（上位外）", count: 1, is_other: true }
    ]
  },
  cells: [
    {
      ...model.cells[0],
      slices: [
        { index: 0, label: "2020", count: 1 },
        { index: 1, label: "2021", count: 1 }
      ]
    },
    { ...model.cells[1], slices: [{ index: 0, label: "2020", count: 1 }] },
    { ...model.cells[2], slices: [{ index: 2, label: "その他（上位外）", count: 1 }] }
  ]
} as const;

const fillCount = (svg: string, color: string) =>
  [...svg.matchAll(new RegExp(`fill="${color}"`, "gu"))].length;

describe("matrix pie bubbles", () => {
  it("keeps the plain bubble series when the model has no pie", () => {
    expect(buildMatrixOption(model, bubbleSpec).series.map((item) => item.type)).toEqual(["scatter"]);
  });

  it("draws the bubble cells and a legend as fixed custom series when the model has a pie", () => {
    const option = buildMatrixOption(pieModel, bubbleSpec);

    expect(option.series.map((item) => item.type)).toEqual(["custom", "custom"]);
    expect(optionView(option).title.subtext).toBe("件数は円の面積、円内は「year」の構成比で表現（最大 2）");
  });

  it("splits each bubble into slices coloured by pie category, with a matching legend", () => {
    const svg = renderMatrixModelToRawSvg(pieModel, bubbleSpec);

    // Cell 1 has two slices (2020, 2021); cells 2 and 3 are single circles; each colour is in the legend once.
    expect(fillCount(svg, "#0f766e")).toBe(3);
    expect(fillCount(svg, "#2563eb")).toBe(2);
    expect(fillCount(svg, "#94a3b8")).toBe(2);
    expect([...svg.matchAll(/<path[^>]*d="[^"]*A[^"]*"/gu)]).toHaveLength(2);
    for (const label of ["円内：year", "2020", "2021", "その他（上位外）"]) {
      expect(svg).toContain(`>${label}</text>`);
    }
    expect(svg).not.toContain("<script");
  });

  it("sizes bubbles by count and keeps the count labels opt-in", () => {
    const hidden = renderMatrixModelToRawSvg(pieModel, bubbleSpec);
    const shown = renderMatrixModelToRawSvg(pieModel, { ...bubbleSpec, value_labels: "shown" });
    const countTexts = (svg: string, value: string) =>
      [...svg.matchAll(new RegExp(`<text[^>]*>${value}</text>`, "gu"))].length;

    expect(countTexts(hidden, "2")).toBe(0);
    expect(countTexts(shown, "2")).toBe(1);
    expect(countTexts(shown, "1")).toBe(2);
    const radii = [...hidden.matchAll(/<circle[^>]*\br="([0-9.]+)"/gu)].map((match) => Number(match[1]));
    expect(Math.max(...radii)).toBeGreaterThan(Math.min(...radii));
  });

  it("does not change the heatmap when the model carries a pie", () => {
    const withPie = { ...pieModel, chart_type: "matrix.heatmap", mark: "matrix-heatmap-svg.v1" } as const;

    expect(renderMatrixModelToRawSvg(withPie, heatmapSpec)).toBe(
      renderMatrixModelToRawSvg(heatmapModel, heatmapSpec)
    );
  });

  it.each(["colorblind", "monochrome", "high-contrast"] as const)(
    "renders the pie with the %s palette inside the SVG policy with distinct slice colours",
    (palette) => {
      const svg = renderMatrixModelToRawSvg(pieModel, { ...bubbleSpec, palette, value_labels: "shown" });
      const fills = [...svg.matchAll(/<(?:path|circle)\b[^>]*\bfill="(#[0-9a-f]{6})"/gu)].map((m) => m[1]);

      expect(new Set(fills).size).toBeGreaterThanOrEqual(3);
    }
  );

  it("stays inside the SVG policy when cell widths are not whole pixels", () => {
    // Seven columns split the plot into 117.142857... px bands, so unrounded text positions
    // would carry endless decimals.
    const columns = Array.from({ length: 7 }, (_, index) => index);
    const rows = Array.from({ length: 6 }, (_, index) => index);
    const wide = {
      ...pieModel,
      x_axis: {
        role: "applicant",
        categories: columns.map((index) => ({ id: `x:${index}`, index, label: `X${index}`, count: 3, is_other: false }))
      },
      y_axis: {
        role: "theme",
        categories: rows.map((index) => ({ id: `y:${index}`, index, label: `Y${index}`, count: 3, is_other: false }))
      },
      cells: rows.flatMap((y) =>
        columns.map((x) => ({
          x_index: x,
          y_index: y,
          x_label: `X${x}`,
          y_label: `Y${y}`,
          value: 1 + ((x * 7 + y * 3) % 9),
          row_count: 1,
          slices: [
            { index: 0, label: "2020", count: 1 + (x % 3) },
            { index: 1, label: "2021", count: 1 + (y % 2) }
          ]
        }))
      )
    };

    for (const palette of [undefined, "colorblind", "monochrome", "high-contrast"] as const) {
      expect(() =>
        renderMatrixModelToRawSvg(wide, { ...bubbleSpec, value_labels: "shown", ...(palette ? { palette } : {}) })
      ).not.toThrow();
    }
  });

  it("falls back to the empty state when a pie model has no cells", () => {
    const option = buildMatrixOption({ ...emptyBubbleModel, pie: pieModel.pie }, bubbleSpec);

    expect(option.series.map((item) => item.type)).toEqual(["scatter"]);
    expect(optionView(option).title.subtext).toBe("表示できるマトリクスデータがありません");
  });

  it("accepts a pie model on the wire and rejects a slice that points past the pie", () => {
    const ok = JSON.parse(
      renderRequest(buildRequest(pieModel, bubbleSpec), JSON.stringify(runtime)) as unknown as string
    ) as { ok: boolean };
    const broken = {
      ...pieModel,
      cells: [{ ...pieModel.cells[0], slices: [{ index: 9, label: "x", count: 1 }] }, ...pieModel.cells.slice(1)]
    };
    const rejected = JSON.parse(
      renderRequest(buildRequest(broken, bubbleSpec), JSON.stringify(runtime)) as unknown as string
    ) as { ok: boolean; error?: { code: string } };

    expect(ok.ok).toBe(true);
    expect(rejected.ok).toBe(false);
    expect(rejected.error?.code).toBe("schema.invalid");
  });
});
