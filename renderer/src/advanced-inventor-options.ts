import { buildAlluvial } from "./advanced-inventor-alluvial.js";
import { buildHeatmap } from "./advanced-inventor-heatmap.js";
import { buildNetwork } from "./advanced-inventor-network.js";
import { buildScatter } from "./advanced-inventor-scatter.js";
import { buildTimeline } from "./advanced-inventor-timeline.js";
import type { AdvancedModel, AdvancedProjection, AdvancedSpec, InventorProjection } from "./advanced-types.js";

/**
 * Marks this renderer source can draw. It is a source-level fact only: whether a built asset
 * advertises them is decided by the build's own inventory, never by this list.
 */
export const SUPPORTED_INVENTOR_MARKS: readonly string[] = Object.freeze([
  "inventor-network-svg.v1", "inventor-ego-network-svg.v1", "inventor-technology-svg.v1",
  "inventor-activity-svg.v1", "inventor-cluster-flow-svg.v1", "inventor-similarity-svg.v1",
  "inventor-impact-svg.v1", "inventor-mobility-svg.v1", "inventor-mobility-flow-svg.v1"
]);

export const isInventorProjection = (p: AdvancedProjection): p is InventorProjection =>
  p.kind.startsWith("inventor-");

/** Fixed pixel-space option: no user functions, templates, URLs or interaction are ever emitted. */
export function buildInventorOption(model: AdvancedModel, spec: AdvancedSpec, p: InventorProjection): Record<string, unknown> {
  switch (p.kind) {
    case "inventor-network": return buildNetwork(model, spec, p);
    case "inventor-heatmap": return buildHeatmap(model, spec, p);
    case "inventor-timeline": return buildTimeline(model, spec, p);
    case "inventor-alluvial": return buildAlluvial(model, spec, p);
    case "inventor-scatter": return buildScatter(model, spec, p);
  }
}
