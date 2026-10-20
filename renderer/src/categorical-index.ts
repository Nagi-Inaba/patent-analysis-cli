import { BarChart, LineChart, PieChart } from "echarts/charts";
import { GridComponent, LegendComponent, TitleComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { SVGRenderer } from "echarts/renderers";
import {
  type CategoricalChartModel,
  type CategoricalRenderSpec,
  type CompositionChartModel,
  encodeCanonicalBase64,
  encodeUtf8,
  processRendererTransfer,
  rendererFailure,
  type SeriesChartModel
} from "./categorical-payload.js";
import { normalizeEChartsSvg } from "./categorical-svg-normalize.js";
import { alternatePalette, cycle } from "./palette.js";

echarts.use([BarChart, LineChart, PieChart, GridComponent, LegendComponent, TitleComponent, SVGRenderer]);

const STANDARD_COLORS: readonly string[] = Object.freeze([
  "#0f766e",
  "#2563eb",
  "#9333ea",
  "#c2410c",
  "#047857",
  "#475569",
  "#be123c",
  "#4f46e5",
  "#a16207",
  "#0891b2"
]);
const STANDARD_TEXT = "#0f172a";
const STANDARD_SECONDARY_TEXT = "#475569";
const STANDARD_GRID = "#cbd5e1";
const EMPTY_SERIES = "表示できる年次推移データがありません";
const EMPTY_COMPOSITION = "表示できる構成比データがありません";
const segmenter = new Intl.Segmenter("ja-JP", { granularity: "grapheme" });

type SvgPainter = {
  renderToString(options: { cssAnimation: false; cssEmphasis: false; useViewBox: true }): string;
};

type EChartsOption = Record<string, unknown>;

function removeNonSemanticEChartsTextMetadata(rawSvg: string): string {
  return rawSvg.replaceAll(' xml:space="preserve"', "");
}

function truncateLabel(value: string, maximum: number): string {
  const parts: string[] = [];
  for (const segment of segmenter.segment(value)) {
    if (parts.length >= maximum) return `${parts.join("")}…`;
    parts.push(segment.segment);
  }
  return parts.join("");
}

type Ink = {
  text: string;
  secondaryText: string;
  grid: string;
  fills: readonly string[];
  lines: readonly string[];
};

function inkFor(spec: CategoricalRenderSpec): Ink {
  const alt = alternatePalette(spec.palette);
  if (alt === null) {
    return {
      text: STANDARD_TEXT,
      secondaryText: STANDARD_SECONDARY_TEXT,
      grid: STANDARD_GRID,
      fills: STANDARD_COLORS,
      lines: STANDARD_COLORS
    };
  }
  return { text: alt.text, secondaryText: alt.muted, grid: alt.grid, fills: alt.categorical, lines: alt.lineColors };
}

function title(model: CategoricalChartModel, empty: boolean, emptyText: string, fontFamily: string, ink: Ink) {
  return {
    text: model.title,
    subtext: empty ? emptyText : "",
    left: "center",
    top: 16,
    textStyle: { color: ink.text, fontFamily, fontSize: 22, fontWeight: 600 },
    subtextStyle: { color: ink.secondaryText, fontFamily, fontSize: 14 }
  };
}

export function buildSeriesOption(model: SeriesChartModel, spec: CategoricalRenderSpec): EChartsOption {
  const alt = alternatePalette(spec.palette);
  const ink = inkFor(spec);
  const { text: TEXT, secondaryText: SECONDARY_TEXT, grid: GRID } = ink;
  const outline = alt === null ? {} : { borderColor: alt.outline, borderWidth: alt.outlineWidth };
  const empty = model.x.length === 0 || model.series.length === 0;
  const stacked = spec.renderer_kind === "series.stacked-bar.svg";
  return {
    animation: false,
    backgroundColor: "#ffffff",
    textStyle: { fontFamily: spec.font_family, color: TEXT },
    title: title(model, empty, EMPTY_SERIES, spec.font_family, ink),
    legend: {
      type: "plain",
      top: 66,
      left: "center",
      textStyle: { color: TEXT, fontFamily: spec.font_family },
      formatter: (name: string) => truncateLabel(name, spec.axis_label_max_graphemes)
    },
    grid: { left: 84, right: 44, top: 116, bottom: 84, containLabel: true },
    xAxis: {
      type: "category",
      data: model.x.map((value) => truncateLabel(value, spec.axis_label_max_graphemes)),
      boundaryGap: stacked,
      axisLine: { lineStyle: { color: SECONDARY_TEXT } },
      axisLabel: { color: TEXT, fontFamily: spec.font_family, interval: 0, rotate: model.x.length > 12 ? 35 : 0 }
    },
    yAxis: {
      type: "value",
      min: (value: { min: number }) => Math.min(0, value.min),
      axisLine: { show: false },
      axisLabel: { color: TEXT, fontFamily: spec.font_family },
      splitLine: { lineStyle: { color: GRID } }
    },
    series: model.series.map((item, index) => {
      // Alternate palettes add a colour-independent line style and marker per series.
      const style = alt === null ? null : cycle(alt.lineStyles, index);
      const stroke = cycle(ink.lines, index);
      return {
        name: item.label,
        type: stacked ? "bar" : "line",
        stack: stacked ? "total" : undefined,
        data: item.values,
        symbol: stacked ? undefined : (style?.symbol ?? "circle"),
        symbolSize: stacked ? undefined : style === null ? 6 : 9,
        showSymbol: stacked ? undefined : true,
        lineStyle: stacked
          ? undefined
          : { width: alt?.lineWidth ?? 2, color: stroke, ...(style === null ? {} : { type: style.type }) },
        itemStyle: stacked ? { color: cycle(ink.fills, index), ...outline } : { color: stroke },
        emphasis: { disabled: true },
        animation: false
      };
    })
  };
}

export function buildCompositionOption(
  model: CompositionChartModel,
  spec: CategoricalRenderSpec
): EChartsOption {
  const alt = alternatePalette(spec.palette);
  const ink = inkFor(spec);
  const { text: TEXT, secondaryText: SECONDARY_TEXT, grid: GRID } = ink;
  const outline = alt === null ? {} : { borderColor: alt.outline, borderWidth: alt.outlineWidth };
  const empty = model.items.length === 0;
  if (spec.renderer_kind === "composition.pie.svg") {
    return {
      animation: false,
      backgroundColor: "#ffffff",
      textStyle: { fontFamily: spec.font_family, color: TEXT },
      title: title(model, empty, EMPTY_COMPOSITION, spec.font_family, ink),
      legend: {
        type: "plain",
        orient: "vertical",
        right: 34,
        top: 112,
        textStyle: { color: TEXT, fontFamily: spec.font_family },
        formatter: (name: string) => truncateLabel(name, spec.axis_label_max_graphemes)
      },
      series: [{
        type: "pie",
        radius: ["32%", "62%"],
        center: ["42%", "55%"],
        avoidLabelOverlap: true,
        data: model.items.map((item, index) => ({
          name: item.label,
          value: item.share,
          itemStyle: { color: cycle(ink.fills, index), ...outline }
        })),
        label: {
          show: true,
          color: TEXT,
          fontFamily: spec.font_family,
          formatter: (params: { name?: string; percent?: number }) =>
            `${truncateLabel(params.name ?? "", spec.axis_label_max_graphemes)} ${Number(params.percent ?? 0).toFixed(1)}%`
        },
        emphasis: { disabled: true },
        animation: false
      }]
    };
  }
  return {
    animation: false,
    backgroundColor: "#ffffff",
    textStyle: { fontFamily: spec.font_family, color: TEXT },
    title: title(model, empty, EMPTY_COMPOSITION, spec.font_family, ink),
    grid: { left: 180, right: 64, top: 100, bottom: 56, containLabel: false },
    xAxis: {
      type: "value",
      min: (value: { min: number }) => Math.min(0, value.min),
      axisLabel: { color: TEXT, fontFamily: spec.font_family },
      splitLine: { lineStyle: { color: GRID } }
    },
    yAxis: {
      type: "category",
      inverse: true,
      data: model.items.map((item) => truncateLabel(item.label, spec.axis_label_max_graphemes)),
      axisLine: { lineStyle: { color: SECONDARY_TEXT } },
      axisLabel: { color: TEXT, fontFamily: spec.font_family, interval: 0 }
    },
    series: [{
      type: "bar",
      data: model.items.map((item, index) => ({
        value: item.value,
        itemStyle: { color: cycle(ink.fills, index), ...outline }
      })),
      label: { show: true, position: "right", color: TEXT, fontFamily: spec.font_family },
      emphasis: { disabled: true },
      animation: false
    }]
  };
}

export function renderCategoricalModelToRawSvg(
  model: CategoricalChartModel,
  spec: CategoricalRenderSpec
): string {
  const chart = echarts.init(null, undefined, {
    renderer: "svg",
    ssr: true,
    width: spec.width,
    height: spec.height
  });
  chart.getZr().animation.start = () => {};
  try {
    const option = model.chart_type.startsWith("series.")
      ? buildSeriesOption(model as SeriesChartModel, spec)
      : buildCompositionOption(model as CompositionChartModel, spec);
    chart.setOption(option as Parameters<typeof chart.setOption>[0], { notMerge: true, lazyUpdate: false, silent: true });
    const painter = chart.getZr().painter as unknown as SvgPainter;
    const rawSvg = painter.renderToString({ cssAnimation: false, cssEmphasis: false, useViewBox: true });
    return normalizeEChartsSvg(removeNonSemanticEChartsTextMetadata(rawSvg));
  } finally {
    chart.dispose();
  }
}

function expectedPair(kind: CategoricalRenderSpec["renderer_kind"]): readonly [string, string] {
  if (kind === "series.line.svg") return ["series.line", "series-line-svg.v1"];
  if (kind === "series.stacked-bar.svg") return ["series.stacked-bar", "series-stacked-bar-svg.v1"];
  if (kind === "composition.bar.svg") return ["composition.bar", "composition-bar-svg.v1"];
  return ["composition.pie", "composition-pie-svg.v1"];
}

export function renderRequest(requestBase64: unknown, runtimeJson: unknown): string {
  if (typeof requestBase64 !== "string" || typeof runtimeJson !== "string") throw new Error("renderer input transfer is invalid");
  const prepared = processRendererTransfer(requestBase64, runtimeJson);
  if (!prepared.ok) return JSON.stringify(prepared.response);
  const { runtime, model, spec } = prepared;
  try {
    if (echarts.version !== "6.1.0") return JSON.stringify(rendererFailure(runtime, "runtime.mismatch"));
    const [expectedType, expectedMark] = expectedPair(spec.renderer_kind);
    if (model.chart_type !== expectedType || model.mark !== expectedMark) {
      return JSON.stringify(rendererFailure(runtime, "schema.invalid"));
    }
    const svgBytes = encodeUtf8(renderCategoricalModelToRawSvg(model, spec));
    if (svgBytes.byteLength > 8 * 1024 * 1024) return JSON.stringify(rendererFailure(runtime, "render.failed"));
    return JSON.stringify({ protocol_version: "1.0.0", ok: true, runtime, svg_b64: encodeCanonicalBase64(svgBytes) } as const);
  } catch {
    return JSON.stringify(rendererFailure(runtime, "render.failed"));
  }
}

declare global {
  var PatentAnalysisRenderer: { renderRequest: typeof renderRequest } | undefined;
}

globalThis.PatentAnalysisRenderer = Object.freeze({ renderRequest });
