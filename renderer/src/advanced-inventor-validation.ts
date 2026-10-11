import type {
  AdvancedModel, InventorAlluvialProjection, InventorHeatmapProjection, InventorNetworkProjection,
  InventorScatterProjection, InventorTimelineProjection
} from "./advanced-types.js";

const unique = (values: readonly string[]) => new Set(values).size === values.length;

function networkIsConsistent(analysisId: string, p: InventorNetworkProjection): boolean {
  if (!unique(p.nodes.map(node => node.id))) return false;
  if (p.focus !== null && !p.nodes.some(node => node.id === p.focus)) return false;
  if (analysisId === "inventor-ego-network.v1" && p.focus === null) return false;
  if (analysisId === "inventor-mobility-flow.v1" && p.edges.some(edge => !edge.directed)) return false;
  // Directed relations are keyed by order; an undirected relation owns its unordered pair outright.
  const ordered = new Set<string>();
  const pairs = new Map<string, boolean>();
  for (const edge of p.edges) {
    if (!Number.isInteger(edge.source) || !Number.isInteger(edge.target) || edge.source === edge.target ||
      edge.source < 0 || edge.target < 0 || edge.source >= p.nodes.length || edge.target >= p.nodes.length) return false;
    const pair = `${Math.min(edge.source, edge.target)}:${Math.max(edge.source, edge.target)}`;
    if (!edge.directed) {
      if (pairs.has(pair)) return false;
      pairs.set(pair, false);
      continue;
    }
    const key = `${edge.source}>${edge.target}`;
    if (ordered.has(key) || pairs.get(pair) === false) return false;
    ordered.add(key);
    pairs.set(pair, true);
  }
  return true;
}

/** Every axis cell must be supplied exactly once; null stays unknown. */
function heatmapIsComplete(p: InventorHeatmapProjection): boolean {
  if (p.cells.length !== p.x.length * p.y.length) return false;
  const seen = new Set<string>();
  for (const cell of p.cells) {
    const key = `${cell.x}:${cell.y}`;
    if (cell.x < 0 || cell.y < 0 || cell.x >= p.x.length || cell.y >= p.y.length || seen.has(key)) return false;
    if (cell.value !== null && !(Number.isFinite(cell.value) && cell.value >= 0)) return false;
    seen.add(key);
  }
  return true;
}

const consecutive = (years: readonly number[]) =>
  years.every((year, index) => Number.isInteger(year) && (index === 0 || year === years[index - 1]! + 1));
/** An unordered pair may appear once: a time chain never needs both directions. */
function linksAreUnique(links: readonly { source: number; target: number }[], count: number): boolean {
  const seen = new Set<string>();
  for (const link of links) {
    if (!Number.isInteger(link.source) || !Number.isInteger(link.target) || link.source === link.target ||
      link.source < 0 || link.target < 0 || link.source >= count || link.target >= count) return false;
    const key = `${Math.min(link.source, link.target)}:${Math.max(link.source, link.target)}`;
    if (seen.has(key)) return false;
    seen.add(key);
  }
  return true;
}
function timelineIsConsistent(analysisId: string, p: InventorTimelineProjection): boolean {
  if (!consecutive(p.years) || !unique(p.nodes.map(node => node.id)) || !unique(p.bands.map(band => band.id))) return false;
  if (analysisId === "inventor-activity.v1" && p.bands.length > 0) return false;
  if ((p.nodes.length > 0 || p.bands.length > 0) && p.years.length === 0) return false;
  const first = p.years[0] ?? 0, end = (p.years[p.years.length - 1] ?? 0) + 1;
  for (const node of p.nodes) {
    if (!Number.isInteger(node.y) || node.y < 0 || node.y >= p.lanes.length || !(node.x >= first && node.x <= end)) return false;
  }
  for (const band of p.bands) if (!(band.start <= band.end && band.start >= first && band.end <= end)) return false;
  return linksAreUnique(p.links, p.nodes.length);
}

/**
 * Links only run forward in time. Continuation, split and merge join adjacent years of ordinary
 * boxes, gap links skip at least one year, and entry/exit links end or start at their own box kind,
 * so continuity is never implied across a year without observation. Because each person sits in one
 * box per year, the widths entering or leaving a box cannot exceed its member count.
 */
function alluvialIsConsistent(p: InventorAlluvialProjection): boolean {
  if (!consecutive(p.years) || !unique(p.nodes.map(node => node.id))) return false;
  if (p.nodes.length > 0 && p.years.length === 0) return false;
  const years = new Set(p.years);
  if (p.nodes.some(node => !years.has(node.year))) return false;
  const pairs = new Set<string>();
  const outgoing = new Array<number>(p.nodes.length).fill(0), incoming = new Array<number>(p.nodes.length).fill(0);
  for (const link of p.links) {
    const from = p.nodes[link.source], to = p.nodes[link.target];
    if (!from || !to || link.source === link.target || !Number.isInteger(link.value) || link.value < 1) return false;
    const pair = `${link.source}:${link.target}`;
    if (pairs.has(pair) || to.year <= from.year) return false;
    pairs.add(pair);
    const span = to.year - from.year;
    if (link.kind === "newly_observed") {
      if (from.kind !== "newly_observed" || to.kind !== "cluster") return false;
    } else if (link.kind === "not_observed") {
      if (from.kind !== "cluster" || to.kind !== "not_observed") return false;
    } else if (from.kind !== "cluster" || to.kind !== "cluster" || (link.kind === "gap" ? span < 2 : span !== 1)) {
      return false;
    }
    outgoing[link.source]! += link.value;
    incoming[link.target]! += link.value;
  }
  return p.nodes.every((node, index) => outgoing[index]! <= node.members && incoming[index]! <= node.members);
}

function scatterIsConsistent(p: InventorScatterProjection): boolean {
  const ids = [...p.points.map(point => point.id), ...p.unplottable.map(entry => entry.id)];
  return unique(ids) && p.points.every(point => point.size >= 0) && linksAreUnique(p.edges, p.points.length) &&
    p.edges.every(edge => edge.value >= 0);
}

/** Cross-field checks that a closed JSON Schema cannot express; shapes were already validated. */
export function validateInventorProjection(model: AdvancedModel): boolean {
  const p = model.projection;
  switch (p.kind) {
    case "inventor-network": return networkIsConsistent(model.analysis_id, p);
    case "inventor-heatmap": return heatmapIsComplete(p);
    case "inventor-timeline": return timelineIsConsistent(model.analysis_id, p);
    case "inventor-alluvial": return alluvialIsConsistent(p);
    case "inventor-scatter": return scatterIsConsistent(p);
    default: return false;
  }
}
