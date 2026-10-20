import { mix, type Palette } from "./palette.js";
import type { MatrixChartModel, MatrixPieCategory, MatrixRenderSpec } from "./matrix-payload.js";

/** Right-hand margin that holds the pie legend. */
export const PIE_GRID_RIGHT = 230;

const LEGEND_WIDTH = 190;
const LEGEND_TOP = 108;
const LEGEND_ROW = 24;
const LEGEND_GRAPHEMES = 12;
const SWATCH = 12;
/** Gap from the bubble's top edge to the middle of its count label. */
const COUNT_LABEL_OFFSET = 8;
const MAX_RADIUS = 30;
const MIN_RADIUS = 5;
const FIRST_SLICE_ANGLE = -Math.PI / 2;

// The categorical hues of the other fixed charts, so the pie reads like the rest of the family.
const STANDARD_SLICES = Object.freeze([
  "#0f766e", "#2563eb", "#b45309", "#7e22ce", "#be123c", "#0369a1", "#4d7c0f", "#a21caf"
]);
const STANDARD_OTHER = "#94a3b8";

type Point = readonly [number, number];

/** The part of ECharts' custom-series API the fixed renderer relies on. */
type RenderApi = {
  value(dimension: number): number;
  coord(point: Point): Point;
  size(point: Point): Point;
  getWidth(): number;
};

type Element = { readonly type: string; readonly [key: string]: unknown };

export type PieInk = {
  /** Fill per pie category index. */
  readonly fills: readonly string[];
  readonly separator: string;
  readonly separatorWidth: number;
  readonly ring: string;
  readonly text: string;
  readonly muted: string;
};

function round2(value: number): number {
  return Math.round(value * 100) / 100;
}

function clip(label: string, limit: number): string {
  const characters = Array.from(label);
  return characters.length <= limit ? label : `${characters.slice(0, limit - 1).join("")}…`;
}

export function pieCountKey(role: string, maximum: number): string {
  return `件数は円の面積、円内は「${clip(role, 16)}」の構成比で表現（最大 ${maximum}）`;
}

function sliceFills(categories: readonly MatrixPieCategory[], alt: Palette | null): string[] {
  const named = categories.filter((category) => !category.is_other).length;
  return categories.map((category) => {
    if (category.is_other) {
      if (alt === null) return STANDARD_OTHER;
      return alt.id === "monochrome" ? "#ffffff" : alt.remainder;
    }
    if (alt === null) return STANDARD_SLICES[category.index % STANDARD_SLICES.length]!;
    // Four greys cannot tell eight slices apart, so the monochrome palette spreads them over a ramp.
    if (alt.id === "monochrome") {
      return mix("#1a1a1a", "#d0d0d0", named <= 1 ? 0 : category.index / (named - 1));
    }
    return alt.categorical[category.index % alt.categorical.length]!;
  });
}

export function pieInk(
  categories: readonly MatrixPieCategory[],
  alt: Palette | null,
  text: string,
  muted: string
): PieInk {
  return {
    fills: sliceFills(categories, alt),
    separator: alt === null ? "#ffffff" : alt.outline,
    separatorWidth: alt === null ? 1 : alt.outlineWidth,
    ring: alt === null ? muted : alt.outline,
    text,
    muted
  };
}

function bubbleElements(
  model: MatrixChartModel,
  spec: MatrixRenderSpec,
  ink: PieInk,
  maximum: number,
  cellIndex: number,
  center: Point,
  band: Point
): Element[] {
  const cell = model.cells[cellIndex]!;
  const slices = cell.slices ?? [];
  // Every coordinate is rounded here: the SVG policy accepts at most twelve decimals, and
  // ECharts passes text coordinates through as computed (a third of a pixel is endless).
  const cx = round2(center[0]);
  const cy = round2(center[1]);
  // A bubble never grows past its own cell, so neighbours cannot overlap.
  const largest = Math.max(2, Math.min(0.46 * Math.min(Math.abs(band[0]), Math.abs(band[1])), MAX_RADIUS));
  const smallest = Math.min(largest, Math.max(MIN_RADIUS, 0.3 * largest));
  const radius = round2(smallest + (largest - smallest) * Math.sqrt(Math.max(0, cell.value) / maximum));

  const total = slices.reduce((sum, slice) => sum + slice.count, 0);
  const elements: Element[] = [];
  if (slices.length === 1) {
    elements.push({
      type: "circle",
      shape: { cx, cy, r: radius },
      style: { fill: ink.fills[slices[0]!.index], stroke: ink.separator, lineWidth: ink.separatorWidth },
      silent: true
    });
  } else {
    let start = FIRST_SLICE_ANGLE;
    for (const slice of slices) {
      const end = start + (slice.count / total) * 2 * Math.PI;
      elements.push({
        type: "sector",
        shape: { cx, cy, r: radius, r0: 0, startAngle: start, endAngle: end, clockwise: true },
        style: { fill: ink.fills[slice.index], stroke: ink.separator, lineWidth: ink.separatorWidth },
        silent: true
      });
      start = end;
    }
  }
  elements.push({
    type: "circle",
    shape: { cx, cy, r: radius },
    style: { fill: "none", stroke: ink.ring, lineWidth: 1 },
    silent: true
  });
  if (spec.value_labels === "shown") {
    // Middle-aligned: ECharts offsets bottom-aligned text by a measured height, which leaves
    // endless decimals that the SVG policy rejects.
    elements.push({
      type: "text",
      style: {
        text: String(cell.value),
        x: cx,
        y: round2(cy - radius - COUNT_LABEL_OFFSET),
        fill: ink.text,
        fontSize: 12,
        fontFamily: spec.font_family,
        align: "center",
        verticalAlign: "middle"
      },
      silent: true
    });
  }
  return elements;
}

function legendElements(
  model: MatrixChartModel,
  spec: MatrixRenderSpec,
  ink: PieInk,
  width: number
): Element[] {
  const pie = model.pie!;
  const left = width - LEGEND_WIDTH;
  const label = (text: string, y: number, fill: string, weight: number): Element => ({
    type: "text",
    style: {
      text,
      x: left + SWATCH + 6,
      y,
      fill,
      fontSize: 13,
      fontWeight: weight,
      fontFamily: spec.font_family,
      align: "left",
      verticalAlign: "middle"
    },
    silent: true
  });
  const elements: Element[] = [
    {
      type: "text",
      style: {
        text: `円内：${clip(pie.role, LEGEND_GRAPHEMES)}`,
        x: left,
        y: LEGEND_TOP,
        fill: ink.muted,
        fontSize: 13,
        fontWeight: 600,
        fontFamily: spec.font_family,
        align: "left",
        verticalAlign: "middle"
      },
      silent: true
    }
  ];
  pie.categories.forEach((category, row) => {
    const middle = LEGEND_TOP + LEGEND_ROW * (row + 1);
    elements.push({
      type: "rect",
      shape: { x: left, y: middle - SWATCH / 2, width: SWATCH, height: SWATCH },
      style: { fill: ink.fills[category.index], stroke: ink.ring, lineWidth: 1 },
      silent: true
    });
    elements.push(label(clip(category.label, LEGEND_GRAPHEMES), middle, ink.text, 500));
  });
  return elements;
}

/** Fixed custom series: one pie bubble per cell, and the legend in the right margin. */
export function pieBubbleSeries(
  model: MatrixChartModel,
  spec: MatrixRenderSpec,
  ink: PieInk,
  maximum: number
): Array<{ type: "custom"; data: unknown[]; [key: string]: unknown }> {
  return [
    {
      type: "custom",
      name: "matrix pie bubbles",
      silent: true,
      coordinateSystem: "cartesian2d",
      data: model.cells.map((cell, index) => [cell.x_index, cell.y_index, cell.value, index]),
      renderItem: (_params: unknown, api: RenderApi) => ({
        type: "group",
        children: bubbleElements(
          model,
          spec,
          ink,
          maximum,
          api.value(3),
          api.coord([api.value(0), api.value(1)]),
          api.size([1, 1])
        )
      })
    },
    {
      type: "custom",
      name: "matrix pie legend",
      silent: true,
      coordinateSystem: "none",
      data: [[0]],
      renderItem: (_params: unknown, api: RenderApi) => ({
        type: "group",
        children: legendElements(model, spec, ink, api.getWidth())
      })
    }
  ];
}
