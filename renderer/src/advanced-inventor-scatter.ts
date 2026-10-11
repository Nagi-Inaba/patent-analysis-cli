import {
  GRID, MUTED, SUBPIXEL_HALF, SUBPIXEL_RADIUS, TEXT, areaRadius, circleAt, extentOf, frame, lineAt,
  paletteColor, textAt, tinyPositive, zeroCross, type Graphic
} from "./advanced-inventor-frame.js";
import { displayLabel } from "./advanced-text.js";
import type { AdvancedModel, AdvancedSpec, InventorScatterProjection } from "./advanced-types.js";

const PLOT = Object.freeze({ left: 120, right: 880, top: 175, bottom: 565 });
const LEGEND_X = 910;
const EDGE_COLOR = "#94a3b8";
const MAX_CATEGORIES = 8;
const MAX_LISTED = 6;
const numberText = (value: number) => value.toLocaleString("ja-JP", { maximumFractionDigits: 2 });

function range(values: readonly number[]): [number, number] {
  if (values.length === 0) return [0, 1];
  let low = Math.min(...values), high = Math.max(...values);
  if (low === high) { low -= 1; high += 1; }
  const pad = (high - low) * 0.05;
  return [low - pad, high + pad];
}

export function buildScatter(model: AdvancedModel, spec: AdvancedSpec, p: InventorScatterProjection): Record<string, unknown> {
  const [x0, x1] = range(p.points.map(point => point.x)), [y0, y1] = range(p.points.map(point => point.y));
  const toX = (x: number) => PLOT.left + (x - x0) / (x1 - x0) * (PLOT.right - PLOT.left);
  const toY = (y: number) => PLOT.bottom - (y - y0) / (y1 - y0) * (PLOT.bottom - PLOT.top);
  const maximum = Math.max(0, ...p.points.map(point => point.size));
  const categories = [...new Set(p.points.map(point => point.category))].sort();
  const elements: Graphic[] = [];

  if (p.points.length) {
    for (let step = 0; step <= 4; step++) {
      const x = x0 + (x1 - x0) * step / 4, y = y0 + (y1 - y0) * step / 4;
      elements.push(lineAt(toX(x), PLOT.top, toX(x), PLOT.bottom, GRID, 1));
      elements.push(lineAt(PLOT.left, toY(y), PLOT.right, toY(y), GRID, 1));
      elements.push(textAt(spec, toX(x), PLOT.bottom + 14, numberText(x), { align: "center", size: 10, color: MUTED }));
      elements.push(textAt(spec, PLOT.left - 8, toY(y), numberText(y), { align: "right", size: 10, color: MUTED }));
    }
    elements.push(textAt(spec, (PLOT.left + PLOT.right) / 2, PLOT.bottom + 38, p.x_label, { align: "center", weight: 600 }));
    elements.push(textAt(spec, PLOT.left, PLOT.top - 14, p.y_label, { weight: 600 }));
  }
  const edgeMaximum = Math.max(0, ...p.edges.map(edge => edge.value));
  for (const edge of p.edges) {
    const a = p.points[edge.source]!, b = p.points[edge.target]!;
    elements.push(lineAt(toX(a.x), toY(a.y), toX(b.x), toY(b.y), EDGE_COLOR, 1 + 3 * (edgeMaximum > 0 ? edge.value / edgeMaximum : 0)));
  }
  for (const point of p.points) {
    const r = areaRadius(point.size, maximum), color = paletteColor(categories.indexOf(point.category));
    if (point.size > 0 && r < SUBPIXEL_RADIUS) elements.push(tinyPositive(toX(point.x), toY(point.y), color));
    else if (point.size > 0) elements.push(circleAt(toX(point.x), toY(point.y), r, color, "#ffffff", 1.5));
    else elements.push(...zeroCross(toX(point.x), toY(point.y), color));
  }
  for (const point of p.points) {
    const r = areaRadius(point.size, maximum);
    const extent = point.size > 0 && r < SUBPIXEL_RADIUS ? SUBPIXEL_HALF : extentOf(r);
    elements.push(textAt(spec, toX(point.x) + extent + 3, toY(point.y),
      displayLabel(point.label, 12), { size: 10 }));
  }

  // Right column: categories, size and overlay keys, and the count of entries that cannot be plotted.
  let y = PLOT.top - 14;
  const line = (text: string, options: { color?: string; weight?: number } = {}) => {
    elements.push(textAt(spec, LEGEND_X, y, text, { size: 10, ...options }));
    y += 16;
  };
  if (categories.length) {
    line("カテゴリ", { weight: 600 });
    categories.slice(0, MAX_CATEGORIES).forEach(category => {
      elements.push(circleAt(LEGEND_X + 6, y, 5, paletteColor(categories.indexOf(category)), "#ffffff", 1));
      elements.push(textAt(spec, LEGEND_X + 18, y, displayLabel(category, 14), { size: 10 }));
      y += 16;
    });
    if (categories.length > MAX_CATEGORIES) line(`ほか ${categories.length - MAX_CATEGORIES} カテゴリ`, { color: MUTED });
    y += 8;
  }
  line(`円の面積は ${displayLabel(p.size_label, 10)} です`, { color: MUTED });
  line("×は値0 (面積なし。未定義ではありません)", { color: MUTED });
  line("□は微小正値 (面積なし)", { color: MUTED });
  if (p.edges.length) {
    elements.push(lineAt(LEGEND_X, y, LEGEND_X + 24, y, EDGE_COLOR, 2));
    elements.push(textAt(spec, LEGEND_X + 32, y, "共発明の重ね描き (太さは値)", { size: 10, color: MUTED }));
    y += 16;
  }
  y += 10;
  line("プロット対象外", { weight: 600 });
  line(`値が未定義の対象: ${p.unplottable.length}件`);
  line("(0としては描画していません)", { color: MUTED });
  p.unplottable.slice(0, MAX_LISTED).forEach(entry => {
    line(displayLabel(`${entry.label}: ${entry.reason}`, 26), { color: TEXT });
  });
  if (p.unplottable.length > MAX_LISTED) line(`ほか ${p.unplottable.length - MAX_LISTED}件`, { color: MUTED });
  y += 10;
  line("座標には、重なりを避けるための", { color: MUTED });
  line("表示上のずれが含まれることがあります。", { color: MUTED });
  return frame(model, spec, p.points.length === 0, elements);
}
