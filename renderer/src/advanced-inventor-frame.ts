import { displayLabel, fixed, truncateAdvancedLabel } from "./advanced-text.js";
import type { AdvancedModel, AdvancedSpec } from "./advanced-types.js";

export const TEXT = "#0f172a";
export const MUTED = "#475569";
export const GRID = "#cbd5e1";
export const LINE = "#64748b";
/** Fixed categorical palette; index is category % length, so colour never encodes a rank. */
export const PALETTE: readonly string[] = Object.freeze([
  "#0f766e", "#2563eb", "#b45309", "#7e22ce", "#be123c", "#0369a1", "#4d7c0f", "#a21caf", "#c2410c", "#475569"
]);
export const paletteColor = (index: number) => PALETTE[index % PALETTE.length]!;
/**
 * Area-true size: r = cap * sqrt(value / max), so area is proportional to value (no base radius, no floor).
 * Zero, negative, non-finite values and a non-positive maximum have no area (0); callers draw a zero glyph instead.
 */
export function areaRadius(value: number, maximum: number, cap = 20): number {
  if (!(value > 0) || !(maximum > 0) || !Number.isFinite(value) || !Number.isFinite(maximum)) return 0;
  return cap * Math.min(1, Math.sqrt(value) / Math.sqrt(maximum));
}
/** Below SVG coordinate resolution, use a non-area hollow square, never the zero glyph. */
export const SUBPIXEL_RADIUS = 0.1;
export const SUBPIXEL_HALF = 3;
export function tinyPositive(x: number, y: number, color: string, dash?: number[]): Graphic {
  return shape("rect", { x: fixed(x - SUBPIXEL_HALF), y: fixed(y - SUBPIXEL_HALF),
    width: 2 * SUBPIXEL_HALF, height: 2 * SUBPIXEL_HALF },
  { fill: "none", stroke: color, lineWidth: 1.5, ...(dash ? { lineDash: dash } : {}) });
}
/** Half-size of the fixed "known zero" cross; it carries no area meaning. */
export const ZERO_HALF = 4;
/** Visual extent used for edge clipping and label offsets: the disk radius, or the zero cross half-size. */
export const extentOf = (radius: number) => (radius > 0 ? radius : ZERO_HALF);
export type Graphic = Record<string, unknown>;
/** Plot area below the title block; legend column is carved out by each kind as needed. */
export const AREA = Object.freeze({ left: 60, right: 1150, top: 160, bottom: 635 });

type TextOptions = { size?: number; color?: string; align?: "left" | "center" | "right"; weight?: number };
export const shape = (type: string, geometry: Record<string, unknown>, style: Record<string, unknown>): Graphic =>
  ({ type, shape: geometry, style, silent: true });
export function textAt(spec: AdvancedSpec, x: number, y: number, text: string, options: TextOptions = {}): Graphic {
  return { type: "text", silent: true, style: {
    text, x: fixed(x), y: fixed(y), fill: options.color ?? TEXT, fontFamily: spec.font_family,
    fontSize: options.size ?? 11, fontWeight: options.weight ?? 400,
    textAlign: options.align ?? "left", textVerticalAlign: "middle"
  } };
}
export function lineAt(
  x1: number, y1: number, x2: number, y2: number, color: string, width: number, dash?: number[], opacity?: number
): Graphic {
  return shape("line", { x1: fixed(x1), y1: fixed(y1), x2: fixed(x2), y2: fixed(y2) },
    { stroke: color, lineWidth: fixed(width), ...(dash ? { lineDash: dash } : {}),
      ...(opacity === undefined ? {} : { opacity }), fill: "none" });
}
export function circleAt(x: number, y: number, r: number, fill: string, stroke: string, width: number): Graphic {
  return shape("circle", { cx: fixed(x), cy: fixed(y), r: fixed(r) }, { fill, stroke, lineWidth: fixed(width) });
}
/** Known zero: a fixed-size "x" built from two strokes, deliberately not a disk and not a missing value. */
export function zeroCross(x: number, y: number, color: string, dash?: number[]): Graphic[] {
  return [lineAt(x - ZERO_HALF, y - ZERO_HALF, x + ZERO_HALF, y + ZERO_HALF, color, 2, dash),
    lineAt(x - ZERO_HALF, y + ZERO_HALF, x + ZERO_HALF, y - ZERO_HALF, color, 2, dash)];
}
export function rectAt(x: number, y: number, width: number, height: number, fill: string, stroke = "none", lineWidth = 0): Graphic {
  return shape("rect", { x: fixed(x), y: fixed(y), width: fixed(width), height: fixed(height) },
    { fill, stroke, lineWidth });
}
export function polygonAt(points: [number, number][], fill: string, stroke = "none", lineWidth = 0): Graphic {
  return shape("polygon", { points: points.map(([x, y]) => [fixed(x), fixed(y)]) }, { fill, stroke, lineWidth });
}
/** Filled triangle whose tip is at (x, y) pointing along the unit vector (dx, dy). */
export function arrowhead(x: number, y: number, dx: number, dy: number, size: number, color: string): Graphic {
  const bx = x - dx * size, by = y - dy * size;
  return polygonAt([[x, y], [bx - dy * size * 0.45, by + dx * size * 0.45], [bx + dy * size * 0.45, by - dx * size * 0.45]], color);
}

export function frame(model: AdvancedModel, spec: AdvancedSpec, empty: boolean, graphic: Graphic[], notes: string[] = []): Record<string, unknown> {
  const population = `入力 ${model.population.input_rows} / 分析 ${model.population.analyzed_rows} / 除外 ${model.population.excluded_rows}`;
  const note = [empty ? "対象データなし" : "", ...notes, truncateAdvancedLabel(model.projection.context, 80), population,
    model.warnings.length ? `注意 ${model.warnings.length}件: ${displayLabel(model.warnings[0]!, 80)}` : ""]
    .filter(Boolean).join("\n");
  return {
    animation: false, backgroundColor: "#ffffff",
    textStyle: { fontFamily: spec.font_family, color: TEXT },
    title: { text: model.title, subtext: note, left: "center", top: 12,
      textStyle: { fontFamily: spec.font_family, fontSize: 22, fontWeight: 600, color: TEXT },
      subtextStyle: { fontFamily: spec.font_family, fontSize: 12, lineHeight: 18, color: MUTED } },
    graphic: { elements: graphic }, series: []
  };
}
