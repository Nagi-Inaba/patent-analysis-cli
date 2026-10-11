import {
  AREA, GRID, LINE, MUTED, SUBPIXEL_HALF, SUBPIXEL_RADIUS, TEXT, arrowhead, areaRadius, circleAt,
  extentOf, frame, lineAt, paletteColor, polygonAt, rectAt, shape, textAt, tinyPositive, zeroCross, type Graphic
} from "./advanced-inventor-frame.js";
import { displayLabel, fixed } from "./advanced-text.js";
import type { AdvancedModel, AdvancedSpec, InventorNetworkProjection } from "./advanced-types.js";

type EdgeState = InventorNetworkProjection["edges"][number]["state"];
const STATE_STYLE: Readonly<Record<EdgeState, { color: string; dash?: number[]; label: string }>> = Object.freeze({
  observed: { color: LINE, label: "観測" },
  inferred: { color: LINE, dash: [6, 4], label: "推定" },
  confirmed: { color: TEXT, label: "確認" },
  corporate: { color: "#b45309", dash: [2, 3], label: "企業事実" }
});
const RECIPROCAL_OFFSET = 6;
const LEGEND_X = 930;
const MAX_LEGEND_GROUPS = 8;

export function buildNetwork(model: AdvancedModel, spec: AdvancedSpec, p: InventorNetworkProjection): Record<string, unknown> {
  const plot = { left: AREA.left + 30, right: LEGEND_X - 50, top: AREA.top + 30, bottom: AREA.bottom - 30 };
  const xs = p.nodes.map(n => n.x), ys = p.nodes.map(n => n.y);
  const minX = Math.min(...xs), minY = Math.min(...ys);
  const spanX = Math.max(...xs) - minX, spanY = Math.max(...ys) - minY;
  // One uniform scale keeps the supplied geometry; the layout itself is never recomputed here.
  const scale = Math.min(spanX > 0 ? (plot.right - plot.left) / spanX : Infinity,
    spanY > 0 ? (plot.bottom - plot.top) / spanY : Infinity);
  const unit = Number.isFinite(scale) ? scale : 1;
  const offsetX = (plot.left + plot.right) / 2 - (minX + spanX / 2) * unit;
  const offsetY = (plot.top + plot.bottom) / 2 - (minY + spanY / 2) * unit;
  const maximum = Math.max(0, ...p.nodes.map(n => n.value));
  const maxEdge = Math.max(0, ...p.edges.map(e => e.value));
  // r is the area radius (0 for a known zero); e is the visual extent used to clip edges and offset labels.
  const pos = p.nodes.map(n => {
    const r = areaRadius(n.value, maximum);
    return { x: n.x * unit + offsetX, y: n.y * unit + offsetY, r,
      e: n.value > 0 && r < SUBPIXEL_RADIUS ? SUBPIXEL_HALF : extentOf(r) };
  });

  const elements: Graphic[] = [];
  const directedPairs = new Set(p.edges.filter(edge => edge.directed).map(edge => `${edge.source}>${edge.target}`));
  for (const edge of p.edges) {
    const a = pos[edge.source]!, b = pos[edge.target]!;
    const style = STATE_STYLE[edge.state];
    const width = fixed(1 + 4 * (maxEdge > 0 ? edge.value / maxEdge : 0));
    const length = Math.hypot(b.x - a.x, b.y - a.y) || 1;
    const dx = (b.x - a.x) / length, dy = (b.y - a.y) / length;
    // Opposite directed edges are shifted to their own left, i.e. to opposite sides, so neither hides the other's dash.
    const side = edge.directed && directedPairs.has(`${edge.target}>${edge.source}`) ? RECIPROCAL_OFFSET : 0;
    if (side > Math.min(a.e, b.e)) {
      // A parallel offset line cannot intersect a smaller disk. Keep the separated
      // interior, but route its ends along rays from the actual node centers.
      const inset = Math.min(length / 3, Math.max(a.e, b.e) + side + 10);
      const innerA: [number, number] = [a.x + dx * inset - dy * side, a.y + dy * inset + dx * side];
      const innerB: [number, number] = [b.x - dx * inset - dy * side, b.y - dy * inset + dx * side];
      const endpoint = (at: typeof a, interior: [number, number], index: number): [number, number] => {
        const distance = Math.hypot(interior[0] - at.x, interior[1] - at.y);
        if (distance === 0) return [at.x, at.y];
        const ux = (interior[0] - at.x) / distance, uy = (interior[1] - at.y) / distance;
        const square = p.nodes[index]!.value > 0 && at.r < SUBPIXEL_RADIUS;
        const reach = square ? at.e / Math.max(Math.abs(ux), Math.abs(uy)) : at.e;
        return [at.x + ux * reach, at.y + uy * reach];
      };
      const start = endpoint(a, innerA, edge.source), end = endpoint(b, innerB, edge.target);
      const points = [start, innerA, innerB, end].map(([x, y]) => [fixed(x!), fixed(y!)]);
      elements.push(shape("polyline", { points }, { stroke: style.color, fill: "none", lineWidth: width,
        ...(style.dash ? { lineDash: style.dash } : {}) }));
      const lastLength = Math.hypot(end[0] - innerB[0], end[1] - innerB[1]) || 1;
      elements.push(arrowhead(end[0], end[1], (end[0] - innerB[0]) / lastLength,
        (end[1] - innerB[1]) / lastLength, 9 + width, style.color));
    } else {
      const ox = -dy * side, oy = dx * side;
      const reach = (at: typeof a, index: number) => p.nodes[index]!.value > 0 && at.r < SUBPIXEL_RADIUS
        ? at.e / (Math.max(Math.abs(dx), Math.abs(dy)) || 1)
        : Math.sqrt(Math.max(at.e * at.e - side * side, 0));
      const startReach = reach(a, edge.source), endReach = reach(b, edge.target);
      const x1 = a.x + ox + dx * startReach, y1 = a.y + oy + dy * startReach;
      const x2 = b.x + ox - dx * endReach, y2 = b.y + oy - dy * endReach;
      elements.push(lineAt(x1, y1, x2, y2, style.color, width, style.dash));
      if (edge.directed) {
        elements.push(arrowhead(x2, y2, dx, dy, 9 + width, style.color));
      }
    }
    if (edge.state === "confirmed") {
      const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
      elements.push(polygonAt([[mx, my - 5], [mx + 5, my], [mx, my + 5], [mx - 5, my]], TEXT));
    }
  }
  p.nodes.forEach((node, index) => {
    const at = pos[index]!;
    const focused = node.id === p.focus;
    if (node.value > 0 && at.r < SUBPIXEL_RADIUS) {
      elements.push(tinyPositive(at.x, at.y, paletteColor(node.group)));
      if (focused) elements.push(rectAt(at.x - 8, at.y - 8, 16, 16, "none", TEXT, 3));
    } else if (node.value > 0) {
      elements.push(circleAt(at.x, at.y, at.r, paletteColor(node.group), focused ? TEXT : "#ffffff", focused ? 4 : 1.5));
    } else {
      elements.push(...zeroCross(at.x, at.y, paletteColor(node.group)));
      if (focused) elements.push(rectAt(at.x - 8, at.y - 8, 16, 16, "none", TEXT, 3));
    }
  });
  p.nodes.forEach((node, index) => {
    const at = pos[index]!;
    elements.push(textAt(spec, at.x, at.y + at.e + 11, displayLabel(node.label, 14), { align: "center" }));
    if (node.hop !== null) elements.push(textAt(spec, at.x + at.e + 3, at.y, `H${node.hop}`, { size: 9, color: MUTED }));
  });

  // Legend column: communities, edge status, direction, size and an explicit layout caveat.
  const groups = [...new Set(p.nodes.map(n => n.group))].sort((a, b) => a - b);
  let y = AREA.top + 4;
  elements.push(rectAt(LEGEND_X - 14, AREA.top - 6, 250, 470, "none", GRID, 1));
  elements.push(textAt(spec, LEGEND_X, y, "コミュニティ (色)", { weight: 600 }));
  for (const group of groups.slice(0, MAX_LEGEND_GROUPS)) {
    y += 18;
    elements.push(circleAt(LEGEND_X + 6, y, 5, paletteColor(group), "#ffffff", 1));
    elements.push(textAt(spec, LEGEND_X + 18, y, `グループ ${group}`, { size: 10 }));
  }
  if (groups.length > MAX_LEGEND_GROUPS) {
    y += 18;
    elements.push(textAt(spec, LEGEND_X, y, `ほか ${groups.length - MAX_LEGEND_GROUPS} グループ`, { size: 10, color: MUTED }));
  }
  y += 30;
  elements.push(textAt(spec, LEGEND_X, y, "線の状態", { weight: 600 }));
  for (const state of Object.keys(STATE_STYLE) as EdgeState[]) {
    y += 18;
    const style = STATE_STYLE[state];
    elements.push(lineAt(LEGEND_X, y, LEGEND_X + 40, y, style.color, 2, style.dash));
    elements.push(textAt(spec, LEGEND_X + 50, y, style.label, { size: 10 }));
  }
  y += 22;
  elements.push(arrowhead(LEGEND_X + 40, y, 1, 0, 10, LINE));
  elements.push(textAt(spec, LEGEND_X + 50, y, "矢印は向き", { size: 10 }));
  y += 30;
  for (const note of ["円の面積は活動量です", "×は活動量0 (面積なし)", "線の太さは値です", "太い枠は注目ノードです",
    "□は微小正値 (面積なし)", "配置は計算済みの座標を", "そのまま表示したレイアウトで、", "距離に意味はありません"]) {
    elements.push(textAt(spec, LEGEND_X, y, note, { size: 10, color: MUTED }));
    y += 16;
  }
  return frame(model, spec, p.nodes.length === 0, elements);
}
