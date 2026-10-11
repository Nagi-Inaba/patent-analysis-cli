import { BarChart, HeatmapChart, ScatterChart } from "echarts/charts";
import { GraphicComponent, GridComponent, MarkLineComponent, TitleComponent, VisualMapComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { SVGRenderer } from "echarts/renderers";
import { buildAdvancedOption } from "./advanced-options.js";
import { advancedFailure, encodeCanonicalBase64, encodeUtf8, processAdvancedTransfer } from "./advanced-payload.js";
import type { AdvancedModel, AdvancedSpec } from "./advanced-types.js";
import { normalizeEChartsSvg } from "./categorical-svg-normalize.js";

echarts.use([BarChart, HeatmapChart, ScatterChart, GraphicComponent, GridComponent,
  MarkLineComponent, TitleComponent, VisualMapComponent, SVGRenderer]);
type Painter = { renderToString(options: { cssAnimation: false; cssEmphasis: false; useViewBox: true }): string };
export function renderAdvancedModelToRawSvg(model: AdvancedModel, spec: AdvancedSpec): string {
  const chart = echarts.init(null, undefined, { renderer: "svg", ssr: true, width: spec.width, height: spec.height });
  chart.getZr().animation.start = () => {};
  try {
    chart.setOption(buildAdvancedOption(model, spec) as Parameters<typeof chart.setOption>[0], {
      notMerge: true, lazyUpdate: false, silent: true
    });
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
