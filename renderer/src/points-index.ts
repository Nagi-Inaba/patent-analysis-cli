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
import { alternatePalette } from "./palette.js";
import { drawnTextBoxes, estimateLabelSize, placeLabels, type LabelSlot, type Rect } from "./label-layout.js";
import { normalizeEChartsSvg } from "./categorical-svg-normalize.js";

echarts.use([ScatterChart, GridComponent, LegendComponent, TitleComponent, SVGRenderer]);

const STANDARD_TEXT = "#0f172a";
const STANDARD_SECONDARY_TEXT = "#475569";
const STANDARD_OPACITY = 0.82;
const STANDARD_STAGE_COLORS: Readonly<Record<"growth" | "stable" | "slowing" | "decline", string>> = Object.freeze({
  growth: "#0f766e",
  stable: "#2563eb",
  slowing: "#a16207",
  decline: "#b45309"
});
const STAGES = Object.freeze([
  { stage: "growth", label: "成長" },
  { stage: "stable", label: "安定" },
  { stage: "slowing", label: "減速" },
  { stage: "decline", label: "衰退" }
] as const);
const segmenter = new Intl.Segmenter("ja-JP", { granularity: "grapheme" });
// Fixed margins (not containLabel) so the y-axis name can sit left of the tick labels,
// where no point or point label is ever drawn.
const GRID = Object.freeze({ left: 120, right: 56, top: 112, bottom: 76 });
// ECharts' default label size, which the point labels use.
const LABEL_FONT_SIZE = 12;
// Labels may reach just past the y axis and up to the legend, but never onto the x tick labels.
const LABEL_TOP = 80;
const LABEL_MARGIN = 8;

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

function maximumSize(model: PointsChartModel): number {
  return model.points.reduce((result, point) => Math.max(result, point.size), 0);
}

/**
 * `placement` is one slot per point (index-aligned with `model.points`); without one every label
 * sits above its point. "hidden" draws no labels, which is how the fixed text is measured.
 */
export function buildPointsOption(
  model: PointsChartModel,
  spec: PointsRenderSpec,
  placement: readonly LabelSlot[] | "hidden" = []
): Record<string, unknown> {
  const alt = alternatePalette(spec.palette);
  const TEXT = alt?.text ?? STANDARD_TEXT;
  const SECONDARY_TEXT = alt?.muted ?? STANDARD_SECONDARY_TEXT;
  const STAGE_COLORS = alt?.stage ?? STANDARD_STAGE_COLORS;
  const opacity = alt?.bubbleOpacity ?? STANDARD_OPACITY;
  const maximum = maximumSize(model);
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
    legend: {
      show: model.points.length > 0,
      top: 54,
      left: "center",
      icon: "circle",
      selectedMode: false,
      data: STAGES.map(({ label }) => label),
      textStyle: { color: TEXT, fontFamily: spec.font_family }
    },
    grid: { ...GRID, containLabel: false },
    xAxis: {
      type: "value",
      name: model.x_axis.label,
      minInterval: 1,
      scale: true,
      // Years are plain integers; the default label adds a thousands separator ("2,018").
      axisLabel: { color: TEXT, fontFamily: spec.font_family, formatter: (value: number) => String(value) },
      axisLine: { lineStyle: { color: SECONDARY_TEXT } },
      splitLine: { show: false }
    },
    yAxis: {
      type: "value",
      name: model.y_axis.label,
      nameLocation: "middle",
      nameGap: 80,
      nameTextStyle: { color: TEXT, fontFamily: spec.font_family },
      axisLabel: { color: TEXT, fontFamily: spec.font_family },
      axisLine: { lineStyle: { color: SECONDARY_TEXT } },
      splitLine: { show: false }
    },
    series: STAGES.map(({ stage, label: stageLabel }) => ({
      type: "scatter",
      name: stageLabel,
      itemStyle: { color: STAGE_COLORS[stage], opacity },
      data: model.points.flatMap((point, index) => point.stage !== stage ? [] : [{
        name: point.label,
        value: [point.x, point.y, point.size],
        symbolSize: diameter(point.size, maximum),
        label: placement === "hidden" ? { show: false } : {
          show: true,
          position: placement[index]?.position ?? "top",
          ...(placement[index]?.offset ? { offset: placement[index]!.offset } : {}),
          color: TEXT,
          fontFamily: spec.font_family,
          formatter: () => truncateLabel(point.label, spec.axis_label_max_graphemes)
        }
      }]),
      emphasis: { disabled: true },
      animation: false
    }))
  };
}

type PointsChart = ReturnType<typeof echarts.init>;

/** Where each label goes so that none lands on another label, a bubble or the chart's own text. */
function placePointLabels(chart: PointsChart, model: PointsChartModel, spec: PointsRenderSpec): LabelSlot[] {
  const maximum = maximumSize(model);
  const subjects = model.points.map((point) => {
    const [x, y] = chart.convertToPixel({ gridIndex: 0 }, [point.x, point.y]) as number[];
    const text = truncateLabel(point.label, spec.axis_label_max_graphemes);
    return {
      x: x!,
      y: y!,
      radius: diameter(point.size, maximum) / 2,
      ...estimateLabelSize(text, LABEL_FONT_SIZE)
    };
  });
  const bounds: Rect = {
    left: GRID.left - 16,
    top: LABEL_TOP,
    right: spec.width - LABEL_MARGIN,
    bottom: spec.height - GRID.bottom
  };
  return placeLabels(subjects, bounds, drawnTextBoxes(chart));
}

export function renderPointsModelToRawSvg(model: PointsChartModel, spec: PointsRenderSpec): string {
  const chart = echarts.init(null, undefined, {
    renderer: "svg",
    ssr: true,
    width: spec.width,
    height: spec.height
  });
  chart.getZr().animation.start = () => {};
  const draw = (placement: readonly LabelSlot[] | "hidden"): void => {
    chart.setOption(buildPointsOption(model, spec, placement) as Parameters<typeof chart.setOption>[0], {
      notMerge: true,
      lazyUpdate: false,
      silent: true
    });
  };
  try {
    if (model.points.length === 0) {
      draw([]);
    } else {
      // First pass: no labels, to learn where the points and the fixed text are.
      draw("hidden");
      draw(placePointLabels(chart, model, spec));
    }
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
