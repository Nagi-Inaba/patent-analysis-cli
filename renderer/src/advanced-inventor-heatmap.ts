import { AREA, MUTED, TEXT, frame, lineAt, rectAt, textAt, shape, type Graphic } from "./advanced-inventor-frame.js";
import { displayLabel } from "./advanced-text.js";
import { alternatePalette, inkOn, scaleAt } from "./palette.js";
import type { AdvancedModel, AdvancedSpec, InventorHeatmapProjection } from "./advanced-types.js";

const LOW = [0xf0, 0xfd, 0xfa], HIGH = [0x0f, 0x76, 0x6e];
const MISSING_STROKE = "#94a3b8";
const GRID_LEFT = 230;
const GRID_TOP = 215;
const hex = (parts: number[]) => `#${parts.map(v => Math.round(v).toString(16).padStart(2, "0")).join("")}`;
const scale = (t: number) => hex(LOW.map((low, i) => low + (HIGH[i]! - low) * t));
// Values keep their own precision: 0.25 stays 0.25 and 12.5 stays 12.5.
const numberText = (value: number) => value.toLocaleString("ja-JP", { maximumFractionDigits: 2 });

function missingCell(x: number, y: number, width: number, height: number): Graphic[] {
  return [
    shape("rect", { x, y, width, height }, { fill: "#ffffff", stroke: MISSING_STROKE, lineWidth: 1, lineDash: [3, 2] }),
    lineAt(x + 2, y + 2, x + width - 2, y + height - 2, MISSING_STROKE, 1),
    lineAt(x + 2, y + height - 2, x + width - 2, y + 2, MISSING_STROKE, 1)
  ];
}

export function buildHeatmap(model: AdvancedModel, spec: AdvancedSpec, p: InventorHeatmapProjection): Record<string, unknown> {
  const columns = p.x.length, rows = p.y.length;
  const alt = alternatePalette(spec.palette);
  const colorAt = (t: number): string => alt === null ? scale(t) : scaleAt(alt.sequential, t);
  const cellW = columns ? Math.min(110, (AREA.right - GRID_LEFT) / columns) : 0;
  const cellH = rows ? Math.min(30, 300 / rows) : 0;
  const values = new Map(p.cells.map(cell => [`${cell.x}:${cell.y}`, cell.value]));
  const maximum = Math.max(0, ...p.cells.map(cell => cell.value ?? 0));
  const elements: Graphic[] = [];

  elements.push(textAt(spec, GRID_LEFT, GRID_TOP - 38, p.x_label, { weight: 600 }));
  elements.push(textAt(spec, AREA.left, GRID_TOP - 12, p.y_label, { weight: 600 }));
  const columnChars = Math.max(3, Math.floor(cellW / 11));
  p.x.forEach((label, x) => {
    elements.push(textAt(spec, GRID_LEFT + (x + 0.5) * cellW, GRID_TOP - 12, displayLabel(label, columnChars),
      { align: "center", size: 10 }));
  });
  p.y.forEach((label, y) => {
    elements.push(textAt(spec, GRID_LEFT - 8, GRID_TOP + (y + 0.5) * cellH, displayLabel(label, 14),
      { align: "right", size: 10 }));
  });
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < columns; x++) {
      const left = GRID_LEFT + x * cellW, top = GRID_TOP + y * cellH;
      const value = values.get(`${x}:${y}`) ?? null;
      if (value === null) {
        elements.push(...missingCell(left, top, cellW, cellH));
        continue;
      }
      const t = maximum > 0 ? value / maximum : 0;
      const fill = colorAt(t);
      elements.push(rectAt(left, top, cellW, cellH, fill, "#ffffff", 1));
      // Dark or white, whichever reads better on this cell's own colour.
      elements.push(textAt(spec, left + cellW / 2, top + cellH / 2, numberText(value),
        { align: "center", size: 10, color: inkOn(fill, TEXT) }));
    }
  }

  // Legend: the numeric scale of the supplied unit, plus a separate mark for unknown cells.
  const legendY = GRID_TOP + rows * cellH + 36;
  elements.push(textAt(spec, GRID_LEFT, legendY, p.value_label, { weight: 600 }));
  for (let step = 0; step < 5; step++) {
    elements.push(rectAt(GRID_LEFT + step * 40, legendY + 14, 40, 14, colorAt(step / 4)));
  }
  elements.push(textAt(spec, GRID_LEFT, legendY + 38, numberText(0), { size: 10 }));
  elements.push(textAt(spec, GRID_LEFT + 200, legendY + 38, numberText(maximum), { size: 10, align: "right" }));
  elements.push(...missingCell(GRID_LEFT + 260, legendY + 14, 40, 14));
  elements.push(textAt(spec, GRID_LEFT + 310, legendY + 21, "不明 (欠損値であり、0ではありません)", { size: 10, color: MUTED }));
  return frame(model, spec, columns === 0 || rows === 0, elements);
}
