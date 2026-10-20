import { graphic } from "echarts/core";
import {
  AREA, GRID, LINE, MUTED, SUBPIXEL_HALF, SUBPIXEL_RADIUS, TEXT, areaRadius, circleAt, extentOf,
  frame, lineAt, paletteColor, polygonAt, rectAt, shape, textAt, tinyPositive, zeroCross, type Graphic
} from "./advanced-inventor-frame.js";
import { displayLabel } from "./advanced-text.js";
import type { AdvancedModel, AdvancedSpec, InventorTimelineProjection } from "./advanced-types.js";

type Band = InventorTimelineProjection["bands"][number];
const PLOT_LEFT = 230;
const PLOT_RIGHT = 1150;
const LANE_BOTTOM = 596;
const SEPARATOR = "#e2e8f0";
const UNKNOWN = "#94a3b8";
const UNKNOWN_RADIUS = 6;
const BAND_KINDS: Readonly<Record<Band["kind"], { fill: string; stroke: string; label: string }>> = Object.freeze({
  acquisition: { fill: "#fed7aa", stroke: "#c2410c", label: "買収" },
  merger: { fill: "#bfdbfe", stroke: "#1d4ed8", label: "合併" },
  name_change: { fill: "#e9d5ff", stroke: "#7e22ce", label: "社名変更" },
  group_change: { fill: "#bbf7d0", stroke: "#15803d", label: "グループ再編" },
  rights_transfer: { fill: "#fecdd3", stroke: "#be123c", label: "権利移転" },
  organizational_transfer: { fill: "#e2e8f0", stroke: "#475569", label: "組織移管" }
});

/** Greedy interval packing so overlapping corporate events never share a row. */
function bandRows(bands: readonly Band[]): number[] {
  const rowEnds: number[] = [];
  const rows = new Array<number>(bands.length).fill(0);
  bands.map((band, index) => ({ band, index })).sort((a, b) => a.band.start - b.band.start || a.index - b.index)
    .forEach(({ band, index }) => {
      let row = rowEnds.findIndex(end => band.start >= end);
      if (row < 0) row = rowEnds.length;
      rowEnds[row] = band.end;
      rows[index] = row;
    });
  return rows;
}
const LABEL_MARGIN = 6;
/** Measure with the same installed SSR text engine and font as the actual SVG. */
const labelWidth = (text: string, spec: AdvancedSpec) => new graphic.Text({ style: {
  text, fontFamily: spec.font_family, fontSize: 9, fontWeight: 400
} }).getBoundingRect().width;
const dashed = (dash?: number[]) => (dash ? { lineDash: dash } : {});

export function buildTimeline(model: AdvancedModel, spec: AdvancedSpec, p: InventorTimelineProjection): Record<string, unknown> {
  const count = p.years.length, first = p.years[0] ?? 0;
  const columnWidth = count ? (PLOT_RIGHT - PLOT_LEFT) / count : 0;
  const xOf = (year: number) => PLOT_LEFT + (year - first) * columnWidth;
  const rows = bandRows(p.bands);
  const rowCount = p.bands.length ? Math.max(...rows) + 1 : 0;
  const rowHeight = rowCount ? Math.min(16, Math.floor(84 / rowCount)) : 0;
  const bandsTop = AREA.top + 8;
  const yearsY = bandsTop + rowCount * rowHeight + (rowCount ? 14 : 4);
  const laneTop = yearsY + 14;
  const laneHeight = p.lanes.length ? Math.min(60, (LANE_BOTTOM - laneTop) / p.lanes.length) : 0;
  const laneBottom = laneTop + p.lanes.length * laneHeight;
  const maximum = Math.max(0, ...p.nodes.map(node => node.size));
  const elements: Graphic[] = [];

  // Calendar frame: every year column is drawn, whether or not anything was observed in it.
  p.years.forEach((year, index) => {
    elements.push(textAt(spec, xOf(year) + columnWidth / 2, yearsY, String(year), { align: "center", size: count > 15 ? 9 : 10 }));
    elements.push(lineAt(xOf(year), yearsY + 8, xOf(year), laneBottom, GRID, 1));
    if (index === count - 1) elements.push(lineAt(xOf(year + 1), yearsY + 8, xOf(year + 1), laneBottom, GRID, 1));
  });
  p.lanes.forEach((lane, index) => {
    const top = laneTop + index * laneHeight;
    elements.push(lineAt(AREA.left, top, PLOT_RIGHT, top, SEPARATOR, 1));
    elements.push(textAt(spec, PLOT_LEFT - 10, top + laneHeight / 2, displayLabel(lane, 14), { align: "right", size: 10 }));
  });
  if (p.lanes.length) elements.push(lineAt(AREA.left, laneBottom, PLOT_RIGHT, laneBottom, SEPARATOR, 1));

  // Corporate events: facts about companies, never an employment span.
  if (p.bands.length) {
    elements.push(textAt(spec, AREA.left, bandsTop + 8, "企業イベント", { size: 10, weight: 600 }));
    p.bands.forEach((band, index) => {
      const style = BAND_KINDS[band.kind];
      const left = xOf(band.start), width = Math.max(2, xOf(band.end) - left), top = bandsTop + rows[index]! * rowHeight;
      elements.push(shape("rect", { x: left, y: top, width, height: rowHeight - 2 },
        { fill: style.fill, stroke: style.stroke, lineWidth: 1, ...dashed(band.status === "announced" ? [5, 3] : undefined) }));
      elements.push(textAt(spec, left + 3, top + (rowHeight - 2) / 2, displayLabel(`${style.label} ${band.label}`, Math.max(3, Math.floor(width / 9))),
        { size: 9 }));
    });
  }

  // r is the area radius (0 for a known zero); e is the visual extent used to clip links and offset labels.
  const node = p.nodes.map(item => {
    const r = areaRadius(item.size, maximum, 12);
    return { x: xOf(item.x), y: laneTop + (item.y + 0.5) * laneHeight, r,
      e: item.state === "unknown" ? UNKNOWN_RADIUS
        : item.size > 0 && r < SUBPIXEL_RADIUS ? SUBPIXEL_HALF : extentOf(r) };
  });
  for (const link of p.links) {
    const a = node[link.source]!, b = node[link.target]!;
    const length = Math.hypot(b.x - a.x, b.y - a.y) || 1;
    const dx = (b.x - a.x) / length, dy = (b.y - a.y) / length;
    const confirmed = link.state === "confirmed";
    const reach = (at: typeof a, index: number) => {
      const item = p.nodes[index]!;
      return item.state !== "unknown" && item.size > 0 && at.r < SUBPIXEL_RADIUS
        ? at.e / (Math.max(Math.abs(dx), Math.abs(dy)) || 1) : at.e;
    };
    const startReach = reach(a, link.source), endReach = reach(b, link.target);
    elements.push(lineAt(a.x + dx * startReach, a.y + dy * startReach, b.x - dx * endReach, b.y - dy * endReach,
      confirmed ? TEXT : LINE, confirmed ? 3 : 2, link.state === "inferred" ? [6, 4] : undefined, link.gap ? 0.55 : undefined));
    const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
    if (confirmed) elements.push(rectAt(mx - 3, my - 3, 6, 6, TEXT));
    if (link.gap) {
      elements.push(lineAt(mx - 2, my + 5, mx + 2, my - 5, LINE, 1));
      elements.push(lineAt(mx + 3, my + 5, mx + 7, my - 5, LINE, 1));
    }
  }
  // Label geometry is decided before the marks so a white patch can sit under each label: lane links
  // run along the lane centre where labels sit and must not strike through them.
  const labels = p.nodes.map((item, index) => {
    const at = node[index]!;
    // Labels sit right of the node; where that would run past the canvas edge they sit on its left, right-aligned.
    let text = displayLabel(item.label, 18);
    const rightX = at.x + at.e + 3, leftX = at.x - at.e - 3;
    const rightSpace = spec.width - LABEL_MARGIN - rightX, leftSpace = leftX - LABEL_MARGIN;
    const onRight = labelWidth(text, spec) <= rightSpace || rightSpace >= leftSpace;
    const available = onRight ? rightSpace : leftSpace;
    for (let limit = 17; labelWidth(text, spec) > available && limit >= 1; limit--) {
      text = displayLabel(item.label, limit);
    }
    if (labelWidth(text, spec) > available) text = "…";
    const width = labelWidth(text, spec);
    return { at, text, onRight, x: onRight ? rightX : leftX, width };
  });
  for (const label of labels) {
    elements.push(rectAt(label.onRight ? label.x - 2 : label.x - label.width - 2,
      label.at.y - 5, label.width + 4, 10, "#ffffff"));
  }
  p.nodes.forEach((item, index) => {
    const at = node[index]!, color = paletteColor(item.category);
    if (item.state === "unknown") {
      // Missing placeholder: fixed nonquantitative dotted outline, matching the legend.
      elements.push({ ...circleAt(at.x, at.y, UNKNOWN_RADIUS, "#ffffff", UNKNOWN, 1.5), style: {
        fill: "#ffffff", stroke: UNKNOWN, lineWidth: 1.5, lineDash: [1, 2] } });
    } else if (item.size > 0 && at.r < SUBPIXEL_RADIUS) {
      elements.push(tinyPositive(at.x, at.y, color, item.state === "inferred" ? [2, 2] : undefined));
      if (item.state === "confirmed") {
        elements.push(polygonAt([[at.x, at.y - 8], [at.x + 8, at.y], [at.x, at.y + 8], [at.x - 8, at.y]], "none", TEXT, 2));
      }
    } else if (item.size === 0) {
      // Known zero: a fixed cross; inference remains dashed and confirmation has a diamond outline.
      elements.push(...zeroCross(at.x, at.y, color,
        item.state === "inferred" ? [2, 2] : undefined));
      if (item.state === "confirmed") {
        elements.push(polygonAt([[at.x, at.y - 8], [at.x + 8, at.y], [at.x, at.y + 8], [at.x - 8, at.y]], "none", TEXT, 2));
      }
    } else if (item.state === "confirmed") {
      const r = at.r * 1.25;
      elements.push(polygonAt([[at.x, at.y - r], [at.x + r, at.y], [at.x, at.y + r], [at.x - r, at.y]], color, TEXT, 2));
    } else if (item.state === "inferred") {
      elements.push({ ...circleAt(at.x, at.y, at.r, "#ffffff", color, 2), style: {
        fill: "#ffffff", stroke: color, lineWidth: 2, lineDash: [4, 3] } });
    } else {
      elements.push(circleAt(at.x, at.y, at.r, color, "#ffffff", 1.5));
    }
  });
  for (const label of labels) {
    elements.push(textAt(spec, label.x, label.at.y, label.text,
      { size: 9, align: label.onRight ? "left" : "right" }));
  }

  // Legend rows: marks, then explicit statements about what the picture does not claim.
  let x = AREA.left;
  const legendY = 614;
  const note = (width: number, draw: (y: number) => Graphic[], label: string) => {
    elements.push(...draw(legendY));
    elements.push(textAt(spec, x + 22, legendY, label, { size: 10 }));
    x += width;
  };
  note(80, y => [circleAt(x + 8, y, 6, "#64748b", "#ffffff", 1.5)], "観測");
  note(80, y => [{ ...circleAt(x + 8, y, 6, "#ffffff", "#64748b", 2), style: {
    fill: "#ffffff", stroke: "#64748b", lineWidth: 2, lineDash: [4, 3] } }], "推定");
  note(80, y => [polygonAt([[x + 8, y - 8], [x + 16, y], [x + 8, y + 8], [x, y]], "#64748b", TEXT, 2)], "確認");
  note(80, y => [{ ...circleAt(x + 8, y, 6, "#ffffff", UNKNOWN, 1.5), style: {
    fill: "#ffffff", stroke: UNKNOWN, lineWidth: 1.5, lineDash: [1, 2] } }], "不明");
  note(210, y => [lineAt(x, y, x + 18, y, LINE, 2, [6, 4])], "破線の線は推定の遷移");
  note(190, y => [lineAt(x, y, x + 18, y, TEXT, 3), rectAt(x + 6, y - 3, 6, 6, TEXT)], "太線と■は確認の遷移");
  note(200, y => [lineAt(x, y, x + 18, y, LINE, 1, undefined, 0.55), lineAt(x + 7, y + 5, x + 11, y - 5, LINE, 1)],
    "// は観測の空白年をまたぐ");
  const notes = ["円の面積は件数 (×は0件、□は微小正値、いずれも面積なし)、色はカテゴリです。",
    "観測のない年も表示しています。空白は0件や退職を意味しません。"];
  if (p.bands.length) {
    notes.push("企業イベントは企業側の事実で、発明者の在籍の確認ではありません (破線枠=発表済み、実線枠=完了)。");
  }
  notes.forEach((text, index) => elements.push(textAt(spec, AREA.left, legendY + 18 * (index + 1), text, { size: 10, color: MUTED })));
  return frame(model, spec, p.lanes.length === 0 || p.years.length === 0, elements);
}
