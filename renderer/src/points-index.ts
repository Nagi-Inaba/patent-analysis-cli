import { ScatterChart } from "echarts/charts";
import { GridComponent, LegendComponent, TitleComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { SVGRenderer } from "echarts/renderers";
import {
  encodeCanonicalBase64,
  encodeUtf8,
  processRendererTransfer,
  rendererFailure,
  type PointsChartModel,
  type PointsRenderSpec
} from "./points-payload.js";
import { normalizeEChartsSvg } from "./categorical-svg-normalize.js";

echarts.use([ScatterChart, GridComponent, LegendComponent, TitleComponent, SVGRenderer]);

const TEXT = "#0f172a";
const SECONDARY_TEXT = "#475569";
const GRID = "#cbd5e1";
const STAGE_COLORS = Object.freeze({
  growth: "#0f766e",
  stable: "#2563eb",
  slowing: "#a16207",
  decline: "#b45309"
} as const);
const segmenter = new Intl.Segmenter("ja-JP", { granularity: "grapheme" });

type SvgPainter = {
  renderToString(options: { cssAnimation: false; cssEmphasis: false; useViewBox: true }): string;
};

function truncateLabel(value: string, maximum: number): string {
  const parts: string[] = [];
  for (const segment of segmenter.segment(value)) {
    if (parts.length >= maximum) return `${parts.slice(0, maximum - 1).join("")}…`;
    parts.push(segment.segment);
  }
  return parts.join("");
}

function removeNonSemanticEChartsTextMetadata(rawSvg: string): string {
  return rawSvg.replaceAll(' xml:space="preserve"', "");
}

function diameter(value: number, maximum: number): number {
  if (maximum <= 0) return 12;
  return 12 + (Math.max(0, value) / maximum) * 12;
}

export function buildPointsOption(model: PointsChartModel, spec: PointsRenderSpec): Record<string, unknown> {
  const maximum = model.points.reduce((result, point) => Math.max(result, point.size), 0);
  return {
    animation: false,
    backgroundColor: "#ffffff",
    textStyle: { fontFamily: spec.font_family, color: TEXT },
    title: {
      text: model.title,
      subtext: model.points.length === 0 ? "表示できるライフサイクルデータがありません" : "",
      left: "center",
      top: 16,
      textStyle: { color: TEXT, fontFamily: spec.font_family, fontSize: 22, fontWeight: 600 },
      subtextStyle: { color: SECONDARY_TEXT, fontFamily: spec.font_family, fontSize: 14 }
    },
    grid: { left: 88, right: 56, top: 92, bottom: 76, containLabel: true },
    xAxis: {
      type: "value",
      name: model.x_axis.label,
      minInterval: 1,
      scale: true,
      axisLabel: { color: TEXT, fontFamily: spec.font_family },
      axisLine: { lineStyle: { color: SECONDARY_TEXT } },
      splitLine: { lineStyle: { color: GRID } }
    },
    yAxis: {
      type: "value",
      name: model.y_axis.label,
      axisLabel: { color: TEXT, fontFamily: spec.font_family },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: GRID } }
    },
    series: [{
      type: "scatter",
      data: model.points.map((point) => ({
        name: point.label,
        value: [point.x, point.y, point.size],
        symbolSize: diameter(point.size, maximum),
        itemStyle: { color: STAGE_COLORS[point.stage], opacity: 0.82 },
        label: {
          show: true,
          position: "top",
          color: TEXT,
          fontFamily: spec.font_family,
          formatter: () => truncateLabel(point.label, spec.axis_label_max_graphemes)
        }
      })),
      emphasis: { disabled: true },
      animation: false
    }]
  };
}

export function renderPointsModelToRawSvg(model: PointsChartModel, spec: PointsRenderSpec): string {
  const chart = echarts.init(null, undefined, {
    renderer: "svg",
    ssr: true,
    width: spec.width,
    height: spec.height
  });
  chart.getZr().animation.start = () => {};
  try {
    chart.setOption(buildPointsOption(model, spec) as Parameters<typeof chart.setOption>[0], {
      notMerge: true,
      lazyUpdate: false,
      silent: true
    });
    const painter = chart.getZr().painter as unknown as SvgPainter;
    const rawSvg = painter.renderToString({ cssAnimation: false, cssEmphasis: false, useViewBox: true });
    return normalizeEChartsSvg(removeNonSemanticEChartsTextMetadata(rawSvg));
  } finally {
    chart.dispose();
  }
}

export function renderRequest(requestBase64: unknown, runtimeJson: unknown): string {
  if (typeof requestBase64 !== "string" || typeof runtimeJson !== "string") {
    throw new Error("renderer input transfer is invalid");
  }
  const prepared = processRendererTransfer(requestBase64, runtimeJson);
  if (!prepared.ok) return JSON.stringify(prepared.response);
  const { runtime, model, spec } = prepared;
  try {
    if (echarts.version !== "6.1.0") return JSON.stringify(rendererFailure(runtime, "runtime.mismatch"));
    if (model.chart_type !== "points.bubble" || model.mark !== "points-bubble-svg.v1" || spec.renderer_kind !== "points.bubble.svg") {
      return JSON.stringify(rendererFailure(runtime, "schema.invalid"));
    }
    const svgBytes = encodeUtf8(renderPointsModelToRawSvg(model, spec));
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
