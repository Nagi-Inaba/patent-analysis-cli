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
  render_profile_id: "matrix-svg-ja-jp-node22-echarts6.v1"
} as const;

const heatmapSpec = {
  ...bubbleSpec,
  renderer_kind: "matrix.heatmap.svg"
} as const;

const runtime = {
  node_version: "22.19.0",
  echarts_version: "6.1.0",
  renderer_build_digest: "b".repeat(64),
  render_profile_id: "matrix-svg-ja-jp-node22-echarts6.v1"
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
