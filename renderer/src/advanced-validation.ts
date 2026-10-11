// @ts-expect-error -- generated validators are build-time assets, not handwritten declarations.
import { validateModelRaw, validateSpecRaw, validateRuntimeRaw, validateRequestRaw } from "./generated/advanced-standalone-validators.js";
import type { AdvancedModel } from "./advanced-types.js";
import { validateInventorProjection } from "./advanced-inventor-validation.js";

const segmenter = new Intl.Segmenter("ja-JP", { granularity: "grapheme" });
function textIsSafe(value: string): boolean {
  if (value.normalize("NFC") !== value) return false;
  for (const character of value) {
    const n = character.codePointAt(0)!;
    if (n <= 0x1f || (n >= 0x7f && n <= 0x9f) || (n >= 0xd800 && n <= 0xdfff) ||
      (n >= 0xfdd0 && n <= 0xfdef) || (n & 0xffff) >= 0xfffe ||
      n === 0x061c || n === 0x200e || n === 0x200f ||
      (n >= 0x202a && n <= 0x202e) || (n >= 0x2066 && n <= 0x2069)) return false;
  }
  return true;
}
function boundedTextAndNumbers(value: unknown): boolean {
  const stack: unknown[] = [value];
  let graphemes = 0;
  let nodes = 0;
  while (stack.length) {
    if (++nodes > 50_000) return false;
    const current = stack.pop();
    if (typeof current === "string") {
      if (!textIsSafe(current)) return false;
      const segments = segmenter.segment(current)[Symbol.iterator]();
      while (!segments.next().done) if (++graphemes > 20_000) return false;
    } else if (typeof current === "number") {
      if (!Number.isFinite(current)) return false;
    } else if (Array.isArray(current)) stack.push(...current);
    else if (current !== null && typeof current === "object") stack.push(...Object.values(current));
  }
  return true;
}
const unique = (values: string[]) => new Set(values).size === values.length;
export function validateAdvancedModel(value: unknown): value is AdvancedModel {
  if (!validateModelRaw(value) || !boundedTextAndNumbers(value)) return false;
  const model = value as AdvancedModel;
  const n = model.population;
  if (n.input_rows !== n.analyzed_rows + n.excluded_rows) return false;
  const p = model.projection;
  if (p.kind === "scatter" || p.kind === "quadrant") {
    if (!unique(p.points.map(point => point.id))) return false;
    if (model.analysis_id !== "citation.v1" && !unique(p.points.map(point => point.label))) return false;
    if (p.kind === "quadrant") {
      if (p.points.length + p.unplottable.length > 20 ||
        !unique([...p.points.map(v => v.label), ...p.unplottable.map(v => v.label)])) return false;
    }
  } else if (p.kind === "heatmap") {
    if (!unique(p.x) || !unique(p.y)) return false;
    const cells = new Map<string, number>();
    for (const cell of p.cells) {
      const key = `${cell.x}:${cell.y}`;
      if (cell.x >= p.x.length || cell.y >= p.y.length || cells.has(key) || (!p.signed && cell.value < 0)) return false;
      cells.set(key, cell.value);
    }
    if (model.analysis_id === "compara.v1" &&
      (!p.signed || p.cells.length !== p.x.length * p.y.length)) return false;
    if (model.analysis_id !== "compara.v1" && p.signed) return false;
    if (model.analysis_id === "cooccurrence.v1") {
      if (JSON.stringify(p.x) !== JSON.stringify(p.y) || p.cells.length !== p.x.length * p.y.length) return false;
      for (const cell of p.cells) {
        if (cell.x === cell.y && cell.value !== 0) return false;
        if (cells.get(`${cell.y}:${cell.x}`) !== cell.value) return false;
      }
    }
  } else if (p.kind === "bars") {
    if (!unique(p.items.map(item => item.label))) return false;
    if (model.analysis_id === "matrix-composition.v1" && p.items.length) {
      const denominator = p.items[0]!.denominator;
      if (p.items.some(item => item.denominator !== denominator) ||
        p.items.reduce((sum, item) => sum + item.value, 0) > denominator ||
        p.items.reduce((sum, item) => sum + item.share, 0) > 1 + 1e-10) return false;
    }
    for (const item of p.items) {
      if (item.value > item.denominator ||
        Math.abs(item.share - (item.denominator ? item.value / item.denominator : 0)) > 1e-10 ||
        (item.involvement_count !== null && item.involvement_count > item.record_count)) return false;
    }
  } else if (p.kind === "tracking") {
    if (!unique(p.inventors) || !unique(p.years.map(String)) ||
      p.years.some((year, i) => i > 0 && year !== p.years[i - 1]! + 1)) return false;
    const positions = new Set<string>();
    for (const node of p.nodes) {
      const key = `${node.x}:${node.y}`;
      if (node.x >= p.years.length || node.y >= p.inventors.length ||
        positions.has(key) || (node.changed && node.unknown)) return false;
      positions.add(key);
    }
    // Every consecutive observation of each inventor must have exactly one link.
    const expected = new Map<string, boolean>();
    for (let y = 0; y < p.inventors.length; y++) {
      const nodes = p.nodes.map((n, i) => ({ ...n, i })).filter(n => n.y === y).sort((a, b) => a.x - b.x);
      if (!nodes.length) return false;
      for (let i = 1; i < nodes.length; i++) {
        expected.set(`${nodes[i - 1]!.i}:${nodes[i]!.i}`, nodes[i]!.x - nodes[i - 1]!.x > 1);
      }
    }
    for (const link of p.links) {
      const key = `${link.source}:${link.target}`;
      if (!expected.has(key) || expected.get(key) !== link.gap) return false;
      expected.delete(key);
    }
    if (expected.size) return false;
  } else if (p.kind !== "network") {
    return validateInventorProjection(model);
  } else {
    if (!unique(p.nodes.map(node => node.label))) return false;
    const edges = new Set<string>();
    for (const edge of p.edges) {
      if (edge.source >= p.nodes.length || edge.target >= p.nodes.length || edge.source === edge.target) return false;
      if (edge.value > p.nodes[edge.source]!.value || edge.value > p.nodes[edge.target]!.value) return false;
      const key = `${Math.min(edge.source, edge.target)}:${Math.max(edge.source, edge.target)}`;
      if (edges.has(key)) return false;
      edges.add(key);
    }
  }
  return true;
}
export const validateAdvancedSpec = (value: unknown): boolean => Boolean(validateSpecRaw(value));
export const validateAdvancedRuntime = (value: unknown): boolean => Boolean(validateRuntimeRaw(value));
export const validateAdvancedRequest = (value: unknown): boolean => Boolean(validateRequestRaw(value));
