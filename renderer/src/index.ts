import { BarChart } from "echarts/charts";
import { GridComponent, MarkLineComponent, TitleComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { SVGRenderer } from "echarts/renderers";
import {
  type ChartModel,
  encodeCanonicalBase64,
  encodeUtf8,
  processRendererTransfer,
  type RenderSpec,
  rendererFailure
} from "./payload.js";
import { alternatePalette } from "./palette.js";
import { normalizeEChartsSvg } from "./svg-normalize.js";

echarts.use([BarChart, GridComponent, MarkLineComponent, TitleComponent, SVGRenderer]);

const STANDARD_COLORS = Object.freeze({
  background: "#FFFFFF",
  positive: "#2563EB",
  negative: "#DC2626",
  remainder: "#94A3B8",
  text: "#0F172A",
  grid: "#E2E8F0",
  axis: "#E2E8F0"
});

type RankingColors = { readonly [Role in keyof typeof STANDARD_COLORS]: string };

function measureTitle(model: ChartModel): string {
  const column = model.measure.column;
  if (model.measure.mode === "count") return "件数";
  if (model.measure.mode === "sum") return `合計（${column}）`;
  if (model.measure.mode === "average") return `平均（${column}）`;
  if (model.measure.mode === "max") return `最大（${column}）`;
  return `最小（${column}）`;
}

function truncateAxisLabel(value: string): string {
  const graphemes = Array.from(new Intl.Segmenter("ja-JP", { granularity: "grapheme" }).segment(value));
  if (graphemes.length <= 28) return value;
  return `${graphemes.slice(0, 27).map(({ segment }) => segment).join("")}…`;
}

type SvgPainter = {
  renderToString(options: {
    cssAnimation: false;
    cssEmphasis: false;
    useViewBox: true;
  }): string;
};

function renderConfiguredChart(
  model: ChartModel,
  spec: RenderSpec,
  serialization: "static" | "measured-css"
): string {
  const chart = echarts.init(null, undefined, {
    renderer: "svg",
    ssr: true,
    width: spec.width,
    height: spec.height
  });
  chart.getZr().animation.start = () => {};
  try {
    const alt = alternatePalette(spec.palette);
    const COLORS: RankingColors =
      alt === null
        ? STANDARD_COLORS
        : {
            background: STANDARD_COLORS.background,
            positive: alt.positive,
            negative: alt.negative,
            remainder: alt.remainder,
            text: alt.text,
            grid: alt.grid,
            axis: alt.axis
          };
    const title = `${model.title}（${measureTitle(model)}）`;
    const seriesData = model.rows.map((row) => {
      const color = row.row_kind === "remainder"
        ? COLORS.remainder
        : row.value < 0 ? COLORS.negative : COLORS.positive;
      return {
        value: row.value,
        itemStyle: {
          color,
          borderColor: row.row_kind === "remainder" ? COLORS.remainder : (alt?.outline ?? color),
          borderWidth: row.row_kind === "remainder" ? 1 : (alt?.outlineWidth ?? 0),
          borderType: row.row_kind === "remainder" ? "dashed" : "solid",
          borderRadius: row.value < 0 ? [4, 0, 0, 4] : [0, 4, 4, 0]
        }
      };
    });
    chart.setOption({
      animation: false,
      backgroundColor: COLORS.background,
      textStyle: { fontFamily: spec.font_family, color: COLORS.text },
      title: {
        text: title,
        subtext: model.rows.length === 0 ? "表示できるランキングデータがありません" : "",
        left: "center",
        top: 16,
        textStyle: { color: COLORS.text, fontFamily: spec.font_family, fontSize: 18, fontWeight: "bold" },
        subtextStyle: { color: COLORS.text, fontFamily: spec.font_family, fontSize: 16 }
      },
      grid: { left: 220, right: 120, top: model.rows.length === 0 ? 150 : 90, bottom: 64 },
      xAxis: {
        type: "value",
        axisLine: { show: true, lineStyle: { color: COLORS.axis, width: 1 } },
        axisTick: { show: false },
        axisLabel: { color: COLORS.text, fontFamily: spec.font_family, fontSize: 12 },
        splitLine: { show: true, lineStyle: { color: COLORS.grid, width: 1, type: "solid" } }
      },
      yAxis: {
        type: "category",
        inverse: true,
        data: model.rows.map((row) => truncateAxisLabel(row.display_label)),
        axisLine: { show: true, lineStyle: { color: COLORS.axis, width: 1 } },
        axisTick: { show: false },
        axisLabel: { color: COLORS.text, fontFamily: spec.font_family, fontSize: 12 }
      },
      series: [{
        type: "bar",
        data: seriesData,
        barMaxWidth: 24,
        label: {
          show: true,
          position: "outside",
          color: COLORS.text,
          fontFamily: spec.font_family,
          fontSize: 12
        },
        markLine: {
          silent: true,
          symbol: "none",
          label: { show: false },
          lineStyle: { color: COLORS.text, width: 1, type: "solid" },
          data: [{ xAxis: 0 }]
        }
      }]
    }, { notMerge: true, lazyUpdate: false, silent: true });
    if (serialization === "measured-css") return chart.renderToSVGString();
    const painter = chart.getZr().painter as unknown as SvgPainter;
    return painter.renderToString({
      cssAnimation: false,
      cssEmphasis: false,
      useViewBox: true
    });
  } finally {
    chart.dispose();
  }
}

export function renderChartModelToRawSvg(model: ChartModel, spec: RenderSpec): string {
  return renderConfiguredChart(model, spec, "static");
}

export function renderChartModelToMeasuredCssSvg(model: ChartModel, spec: RenderSpec): string {
  return renderConfiguredChart(model, spec, "measured-css");
}

export function renderRequest(requestBase64: string, runtimeJson: string): string {
  if (typeof requestBase64 !== "string" || typeof runtimeJson !== "string") {
    throw new Error("renderer input transfer is invalid");
  }
  const prepared = processRendererTransfer(requestBase64, runtimeJson);
  if (!prepared.ok) return JSON.stringify(prepared.response);
  try {
    if (echarts.version !== "6.1.0") {
      return JSON.stringify(rendererFailure(prepared.runtime, "runtime.mismatch"));
    }
    const svg = normalizeEChartsSvg(renderChartModelToRawSvg(prepared.model, prepared.spec));
    const svgBytes = encodeUtf8(svg);
    if (svgBytes.byteLength > 8 * 1024 * 1024) {
      return JSON.stringify(rendererFailure(prepared.runtime, "render.failed"));
    }
    return JSON.stringify({
      protocol_version: "1.0.0",
      ok: true,
      runtime: prepared.runtime,
      svg_b64: encodeCanonicalBase64(svgBytes)
    } as const);
  } catch {
    return JSON.stringify(rendererFailure(prepared.runtime, "render.failed"));
  }
}
