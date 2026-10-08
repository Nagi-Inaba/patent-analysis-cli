import { HeatmapChart, ScatterChart } from "echarts/charts";
import {
  GridComponent,
  TitleComponent,
  VisualMapComponent
} from "echarts/components";
import * as echarts from "echarts/core";
import { SVGRenderer } from "echarts/renderers";
import { normalizeEChartsSvg } from "./svg-normalize.js";
import {
  encodeCanonicalBase64,
  encodeUtf8,
  type MatrixChartModel,
  type MatrixRenderSpec,
  processRendererTransfer,
  rendererFailure
} from "./matrix-payload.js";

echarts.use([
  HeatmapChart,
  ScatterChart,
  GridComponent,
  TitleComponent,
  VisualMapComponent,
  SVGRenderer
]);

const COLORS = Object.freeze({
  background: "#ffffff",
  bubble: "#0f766e",
  heatmapLow: "#f1f5f9",
  heatmapMid: "#5eead4",
  heatmapHigh: "#14b8a6",
  text: "#0f172a",
  secondaryText: "#475569",
  grid: "#cbd5e1"
});

const EMPTY_STATE = "表示できるマトリクスデータがありません";

type MatrixAxisOption = {
  data: string[];
  [key: string]: unknown;
};

type MatrixSeriesOption = {
  type: "scatter" | "heatmap";
  data: number[][];
  [key: string]: unknown;
};

type MatrixOption = {
  animation: boolean;
  xAxis: MatrixAxisOption;
  yAxis: MatrixAxisOption;
  series: MatrixSeriesOption[];
  [key: string]: unknown;
};

type SvgPainter = {
  renderToString(options: {
    cssAnimation: false;
    cssEmphasis: false;
    useViewBox: true;
  }): string;
};

function removeNonSemanticEChartsTextMetadata(rawSvg: string): string {
  return rawSvg.replaceAll(' xml:space="preserve"', "");
}

function matrixCountKey(spec: MatrixRenderSpec, maximum: number): string {
  const encoding =
    spec.renderer_kind === "matrix.bubble.svg"
      ? "円の面積"
      : "色の濃さ";
  return `件数は${encoding}で表現（最大 ${maximum}）`;
}

export function buildMatrixOption(
  model: MatrixChartModel,
  spec: MatrixRenderSpec
): MatrixOption {
  const xLabels = model.x_axis.categories.map((item) => item.label);
  const yLabels = model.y_axis.categories.map((item) => item.label);
  const maximum = Math.max(1, ...model.cells.map((item) => item.value));
  const data = model.cells.map((item) => [item.x_index, item.y_index, item.value]);
  const subtext =
    model.cells.length === 0 ? EMPTY_STATE : matrixCountKey(spec, maximum);
  const base = {
    animation: false,
    backgroundColor: COLORS.background,
    textStyle: {
      fontFamily: spec.font_family,
      color: COLORS.text
    },
    title: {
      text: model.title,
      subtext,
      left: "center",
      top: 16,
      textStyle: {
        color: COLORS.text,
        fontFamily: spec.font_family,
        fontSize: 22,
        fontWeight: 600
      },
      subtextStyle: {
        color: COLORS.secondaryText,
        fontFamily: spec.font_family,
        fontSize: 14
      }
    },
    grid: {
      left: 150,
      right: 70,
      top: 108,
      bottom: 120,
      containLabel: false
    },
    xAxis: {
      type: "category",
      data: xLabels,
      name: model.x_axis.role,
      nameLocation: "middle",
      nameGap: 76,
      nameTextStyle: {
        color: COLORS.text,
        fontFamily: spec.font_family
      },
      axisLine: {
        lineStyle: { color: COLORS.secondaryText }
      },
      axisLabel: {
        color: COLORS.text,
        fontFamily: spec.font_family,
        interval: 0,
        rotate: xLabels.length > 8 ? 35 : 0
      },
      splitLine: {
        lineStyle: { color: COLORS.grid }
      }
    },
    yAxis: {
      type: "category",
      data: yLabels,
      inverse: true,
      name: model.y_axis.role,
      nameLocation: "middle",
      nameGap: 110,
      nameTextStyle: {
        color: COLORS.text,
        fontFamily: spec.font_family
      },
      axisLine: {
        lineStyle: { color: COLORS.secondaryText }
      },
      axisLabel: {
        color: COLORS.text,
        fontFamily: spec.font_family,
        interval: 0
      },
      splitLine: {
        lineStyle: { color: COLORS.grid }
      }
    }
  };
  if (spec.renderer_kind === "matrix.heatmap.svg") {
    return {
      ...base,
      visualMap: {
        show: false,
        min: 0,
        max: maximum,
        calculable: false,
        inRange: {
          color: [COLORS.heatmapLow, COLORS.heatmapMid, COLORS.heatmapHigh]
        }
      },
      series: [
        {
          type: "heatmap",
          data,
          label: {
            show: true,
            color: COLORS.text,
            textBorderWidth: 0
          },
          emphasis: { disabled: true }
        }
      ]
    };
  }
  return {
    ...base,
    series: [
      {
        type: "scatter",
        data,
        itemStyle: { color: COLORS.bubble },
        symbolSize: (value: unknown) => {
          if (!Array.isArray(value) || typeof value[2] !== "number") return 12;
          return 12 + Math.sqrt(Math.max(0, value[2]) / maximum) * 48;
        },
        label: {
          show: true,
          position: "top",
          color: COLORS.text
        },
        emphasis: { disabled: true }
      }
    ]
  };
}

export function renderMatrixModelToRawSvg(
  model: MatrixChartModel,
  spec: MatrixRenderSpec
): string {
  const chart = echarts.init(null, undefined, {
    renderer: "svg",
    ssr: true,
    width: spec.width,
    height: spec.height
  });
  chart.getZr().animation.start = () => {};
  try {
    chart.setOption(
      buildMatrixOption(model, spec) as Parameters<typeof chart.setOption>[0],
      { notMerge: true, lazyUpdate: false, silent: true }
    );
    const painter = chart.getZr().painter as unknown as SvgPainter;
    const rawSvg = painter.renderToString({
      cssAnimation: false,
      cssEmphasis: false,
      useViewBox: true
    });
    return normalizeEChartsSvg(removeNonSemanticEChartsTextMetadata(rawSvg));
  } finally {
    chart.dispose();
  }
}

export function renderRequest(
  requestBase64: unknown,
  runtimeJson: unknown
): string {
  if (typeof requestBase64 !== "string" || typeof runtimeJson !== "string") {
    throw new Error("renderer input transfer is invalid");
  }
  const prepared = processRendererTransfer(requestBase64, runtimeJson);
  if (!prepared.ok) return JSON.stringify(prepared.response);
  const { runtime, model, spec } = prepared;
  try {
    if (echarts.version !== "6.1.0") {
      return JSON.stringify(rendererFailure(runtime, "runtime.mismatch"));
    }
    const expectedType =
      spec.renderer_kind === "matrix.bubble.svg"
        ? "matrix.bubble"
        : "matrix.heatmap";
    const expectedMark =
      spec.renderer_kind === "matrix.bubble.svg"
        ? "matrix-bubble-svg.v1"
        : "matrix-heatmap-svg.v1";
    if (model.chart_type !== expectedType || model.mark !== expectedMark) {
      return JSON.stringify(rendererFailure(runtime, "schema.invalid"));
    }
    const svgBytes = encodeUtf8(renderMatrixModelToRawSvg(model, spec));
    if (svgBytes.byteLength > 8 * 1024 * 1024) {
      return JSON.stringify(rendererFailure(runtime, "render.failed"));
    }
    return JSON.stringify({
      protocol_version: "1.0.0",
      ok: true,
      runtime,
      svg_b64: encodeCanonicalBase64(svgBytes)
    } as const);
  } catch {
    return JSON.stringify(rendererFailure(runtime, "render.failed"));
  }
}

declare global {
  var PatentAnalysisRenderer:
    | {
        renderRequest: typeof renderRequest;
      }
    | undefined;
}

globalThis.PatentAnalysisRenderer = Object.freeze({ renderRequest });
