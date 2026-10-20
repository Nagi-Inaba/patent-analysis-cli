import { BarChart, HeatmapChart, ScatterChart } from "echarts/charts";
import { GraphicComponent, GridComponent, MarkLineComponent, TitleComponent, VisualMapComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { SVGRenderer } from "echarts/renderers";
import { POINT_LABEL_SIZE, buildAdvancedOption, symbolSize, truncateAdvancedLabel } from "./advanced-options.js";
import { advancedFailure, encodeCanonicalBase64, encodeUtf8, processAdvancedTransfer } from "./advanced-payload.js";
import type { AdvancedModel, AdvancedSpec } from "./advanced-types.js";
import { normalizeEChartsSvg } from "./categorical-svg-normalize.js";
import { drawnTextBoxes, estimateLabelSize, placeLabels, type LabelSlot } from "./label-layout.js";

echarts.use([BarChart, HeatmapChart, ScatterChart, GraphicComponent, GridComponent,
  MarkLineComponent, TitleComponent, VisualMapComponent, SVGRenderer]);
type Painter = { renderToString(options: { cssAnimation: false; cssEmphasis: false; useViewBox: true }): string };
// Grid margins of the scatter and quadrant charts (see advanced-options.ts) and the room above the plot.
const GRID_BOTTOM_MARGIN = 90;
const GRID_LEFT_MARGIN = 120;
const LABEL_TOP = 118;
const LABEL_MARGIN = 8;

/**
 * Where each scatter or quadrant point label goes so that none lands on another label, another
 * point's bubble or text the chart draws. Other chart kinds have no such labels and return null.
 */
function placePointLabels(chart: ReturnType<typeof echarts.init>, model: AdvancedModel, spec: AdvancedSpec): LabelSlot[] | null {
  const p = model.projection;
  if ((p.kind !== "scatter" && p.kind !== "quadrant") || p.points.length === 0) return null;
  const maximum = Math.max(0, ...p.points.map(point => point.size));
  const subjects = p.points.map(point => {
    const [x, y] = chart.convertToPixel({ gridIndex: 0 }, [point.x, point.y]) as number[];
    const text = truncateAdvancedLabel(point.label, spec.axis_label_max_graphemes);
    return { x: x!, y: y!, radius: symbolSize(point.size, maximum) / 2, ...estimateLabelSize(text, POINT_LABEL_SIZE) };
  });
  const bounds = {
    left: GRID_LEFT_MARGIN - 16, top: LABEL_TOP,
    right: spec.width - LABEL_MARGIN, bottom: spec.height - GRID_BOTTOM_MARGIN
  };
  return placeLabels(subjects, bounds, drawnTextBoxes(chart));
}

export function renderAdvancedModelToRawSvg(model: AdvancedModel, spec: AdvancedSpec): string {
  const chart = echarts.init(null, undefined, { renderer: "svg", ssr: true, width: spec.width, height: spec.height });
  chart.getZr().animation.start = () => {};
  const draw = (placement: readonly LabelSlot[] | "hidden"): void => {
    chart.setOption(buildAdvancedOption(model, spec, placement) as Parameters<typeof chart.setOption>[0], {
      notMerge: true, lazyUpdate: false, silent: true
    });
  };
  try {
    const kind = model.projection.kind;
    if (kind === "scatter" || kind === "quadrant") {
      // First pass: no labels, to learn where the points and the fixed text are.
      draw("hidden");
      draw(placePointLabels(chart, model, spec) ?? []);
    } else {
      draw([]);
    }
    const raw = (chart.getZr().painter as unknown as Painter).renderToString({
      cssAnimation: false, cssEmphasis: false, useViewBox: true
    });
    return normalizeEChartsSvg(raw.replaceAll(' xml:space="preserve"', ""));
  } finally { chart.dispose(); }
}
export function renderRequest(requestBase64: unknown, runtimeJson: unknown): string {
  const prepared = processAdvancedTransfer(requestBase64, runtimeJson);
  if (!prepared.ok) return JSON.stringify(prepared.response);
  const { runtime, model, spec } = prepared;
  try {
    if (echarts.version !== "6.1.0") return JSON.stringify(advancedFailure(runtime, "runtime.mismatch"));
    const bytes = encodeUtf8(renderAdvancedModelToRawSvg(model, spec));
    if (!bytes.length || bytes.length > 8 * 1024 * 1024) return JSON.stringify(advancedFailure(runtime, "render.failed"));
    return JSON.stringify({ protocol_version: "1.0.0", ok: true, runtime, svg_b64: encodeCanonicalBase64(bytes) });
  } catch { return JSON.stringify(advancedFailure(runtime, "render.failed")); }
}
// Existing family declarations describe the same single frozen entrypoint.
globalThis.PatentAnalysisRenderer = Object.freeze({ renderRequest });
