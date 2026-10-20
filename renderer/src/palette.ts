/**
 * Closed colour palettes for every SVG family.
 *
 * "standard" is deliberately not defined here: each family keeps its existing literal colours,
 * so a default render stays byte-identical. Only the alternates below pass through this module.
 * Values were checked for WCAG contrast against white and, for the categorical sets, for
 * pairwise CIEDE2000 distance under simulated protan/deutan/tritan vision.
 */

export const PALETTE_IDS = ["standard", "colorblind", "monochrome", "high-contrast"] as const;
export type PaletteId = (typeof PALETTE_IDS)[number];

export type LineStyle = {
  readonly type: "solid" | "dashed" | "dotted" | readonly number[];
  readonly symbol: "circle" | "rect" | "triangle" | "diamond";
};

export type Palette = {
  readonly id: Exclude<PaletteId, "standard">;
  /** Fill colours in a fixed order; callers cycle with `cycle()`. */
  readonly categorical: readonly string[];
  /** Line colours; thin lines need darker values than fills. */
  readonly lineColors: readonly string[];
  /** Redundant, colour-independent encoding per series index. */
  readonly lineStyles: readonly LineStyle[];
  readonly lineWidth: number;
  /** Count scale, low to high; the high end is dark on a white background. */
  readonly sequential: readonly [string, string, string];
  /** Signed scale: negative, neutral, positive. */
  readonly diverging: readonly [string, string, string];
  /** Ordered life-cycle stages. */
  readonly stage: Readonly<Record<"growth" | "stable" | "slowing" | "decline", string>>;
  readonly positive: string;
  readonly negative: string;
  readonly remainder: string;
  readonly text: string;
  readonly muted: string;
  /** Decorative grid lines. */
  readonly grid: string;
  /** Axis lines and zero baselines. */
  readonly axis: string;
  /** Network edges and secondary strokes. */
  readonly edge: string;
  /** Inactive / unknown marks. */
  readonly soft: string;
  /** Light neutral fill (separators, "not observed" areas). */
  readonly neutralLight: string;
  /**
   * Opaque outline for bars and pie slices only. Round markers are drawn through a scale transform,
   * which turns an outline into a stroke width with endless decimals that the SVG policy rejects.
   */
  readonly outline: string;
  readonly outlineWidth: number;
  /** Fill opacity of round markers (no outline, so partial opacity stays lossless). */
  readonly bubbleOpacity: number;
};

const SERIES_STYLES: readonly LineStyle[] = Object.freeze([
  { type: "solid", symbol: "circle" },
  { type: "dashed", symbol: "rect" },
  { type: "dotted", symbol: "triangle" },
  { type: Object.freeze([8, 3, 2, 3]), symbol: "diamond" }
]);

const COLORBLIND: Palette = Object.freeze({
  id: "colorblind",
  // Okabe-Ito, reordered so index 1 reads as "recovery" (green) and index 2 as "decline" (vermillion).
  categorical: Object.freeze(["#0072b2", "#009e73", "#d55e00", "#cc79a7", "#e69f00", "#56b4e9", "#f0e442", "#000000"]),
  lineColors: Object.freeze(["#0072b2", "#009e73", "#d55e00", "#cc79a7", "#e69f00", "#56b4e9", "#f0e442", "#000000"]),
  lineStyles: SERIES_STYLES,
  lineWidth: 3,
  sequential: Object.freeze(["#eaf2f9", "#6baed6", "#08519c"] as const),
  diverging: Object.freeze(["#d55e00", "#f7f7f7", "#0072b2"] as const),
  stage: Object.freeze({ growth: "#009e73", stable: "#0072b2", slowing: "#e69f00", decline: "#d55e00" }),
  positive: "#0072b2",
  negative: "#d55e00",
  remainder: "#8a8a8a",
  text: "#0f172a",
  muted: "#475569",
  grid: "#cbd5e1",
  axis: "#64748b",
  edge: "#64748b",
  soft: "#94a3b8",
  neutralLight: "#e2e8f0",
  outline: "#1e293b",
  outlineWidth: 1,
  bubbleOpacity: 0.85
});

const MONOCHROME: Palette = Object.freeze({
  id: "monochrome",
  categorical: Object.freeze(["#1a1a1a", "#595959", "#8c8c8c", "#bfbfbf"]),
  lineColors: Object.freeze(["#1a1a1a", "#333333", "#4d4d4d", "#666666"]),
  lineStyles: SERIES_STYLES,
  lineWidth: 3,
  sequential: Object.freeze(["#f2f2f2", "#9a9a9a", "#1a1a1a"] as const),
  diverging: Object.freeze(["#262626", "#f5f5f5", "#8c8c8c"] as const),
  // Ordered by lightness, light to dark; every step is at least 3:1 against white.
  stage: Object.freeze({ growth: "#8c8c8c", stable: "#666666", slowing: "#404040", decline: "#1a1a1a" }),
  positive: "#1a1a1a",
  negative: "#8c8c8c",
  remainder: "#bfbfbf",
  text: "#111111",
  muted: "#404040",
  grid: "#bfbfbf",
  axis: "#595959",
  edge: "#595959",
  soft: "#8c8c8c",
  neutralLight: "#e0e0e0",
  outline: "#1a1a1a",
  outlineWidth: 1.25,
  bubbleOpacity: 0.9
});

const HIGH_CONTRAST: Palette = Object.freeze({
  id: "high-contrast",
  // Every colour is at least 4.5:1 against white.
  categorical: Object.freeze(["#4477bb", "#228833", "#cc4466", "#993366", "#775500", "#444444", "#571919", "#0e6241"]),
  lineColors: Object.freeze(["#4477bb", "#228833", "#cc4466", "#993366", "#775500", "#444444", "#571919", "#0e6241"]),
  lineStyles: SERIES_STYLES,
  lineWidth: 4,
  sequential: Object.freeze(["#e3eaf5", "#5b84c4", "#0b2e66"] as const),
  diverging: Object.freeze(["#bb5566", "#f7f7f7", "#004488"] as const),
  stage: Object.freeze({ growth: "#228833", stable: "#4477bb", slowing: "#775500", decline: "#cc4466" }),
  positive: "#004488",
  negative: "#cc4466",
  remainder: "#595959",
  text: "#0b0b0b",
  muted: "#1f2937",
  grid: "#8a8a8a",
  axis: "#333333",
  edge: "#444444",
  soft: "#595959",
  neutralLight: "#bdbdbd",
  outline: "#0b0b0b",
  outlineWidth: 1.5,
  bubbleOpacity: 0.95
});

const ALTERNATES: Readonly<Record<Palette["id"], Palette>> = Object.freeze({
  colorblind: COLORBLIND,
  monochrome: MONOCHROME,
  "high-contrast": HIGH_CONTRAST
});

/** The alternate palette for an id, or null for "standard" / absent (keep the family's own colours). */
export function alternatePalette(id: PaletteId | undefined): Palette | null {
  return id === undefined || id === "standard" ? null : ALTERNATES[id];
}

export function cycle<T>(items: readonly T[], index: number): T {
  return items[((index % items.length) + items.length) % items.length]!;
}

const channels = (hex: string): [number, number, number] => [
  parseInt(hex.slice(1, 3), 16),
  parseInt(hex.slice(3, 5), 16),
  parseInt(hex.slice(5, 7), 16)
];
const toHex = (parts: readonly number[]): string =>
  `#${parts.map((value) => Math.round(Math.min(255, Math.max(0, value))).toString(16).padStart(2, "0")).join("")}`;

export function relativeLuminance(hex: string): number {
  const [r, g, b] = channels(hex).map((value) => {
    const unit = value / 255;
    return unit <= 0.04045 ? unit / 12.92 : ((unit + 0.055) / 1.055) ** 2.4;
  }) as [number, number, number];
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

export function contrastRatio(a: string, b: string): number {
  const [high, low] = [relativeLuminance(a), relativeLuminance(b)].sort((x, y) => y - x) as [number, number];
  return (high + 0.05) / (low + 0.05);
}

/** Text colour with the higher contrast on `background`: `dark`, or white. */
export function inkOn(background: string, dark: string): string {
  return contrastRatio(background, "#ffffff") > contrastRatio(background, dark) ? "#ffffff" : dark;
}

export function mix(from: string, to: string, amount: number): string {
  const a = channels(from);
  const b = channels(to);
  return toHex(a.map((value, index) => value + (b[index]! - value) * amount));
}

/** Pale version of a colour, for fills that sit behind an opaque stroke of the original colour. */
export function tint(hex: string, amount = 0.78): string {
  return mix(hex, "#ffffff", amount);
}

/** Position `t` (0..1) on a three-stop scale, interpolated linearly in sRGB like ECharts does. */
export function scaleAt(stops: readonly [string, string, string], t: number): string {
  const clamped = Math.min(1, Math.max(0, t));
  return clamped < 0.5 ? mix(stops[0], stops[1], clamped * 2) : mix(stops[1], stops[2], (clamped - 0.5) * 2);
}

/** Steps of a piecewise visualMap that has no explicit pieces (ECharts' default `splitNumber`). */
export const HEATMAP_PIECES = 5;

/**
 * The piece ECharts puts `value` in for a piecewise visualMap of `count` equal steps over
 * [min, max]: a value on a boundary belongs to the lower piece, and `min` to the first.
 * The step arithmetic follows ECharts so cell colours and the ink chosen for them agree.
 */
export function pieceIndexOf(value: number, min: number, max: number, count: number = HEATMAP_PIECES): number {
  let precision = 0;
  let step = (max - min) / count;
  while (+step.toFixed(precision) !== step && precision < 5) precision += 1;
  step = +step.toFixed(precision);
  let upper = min;
  for (let index = 0; index < count - 1; index += 1) {
    upper += step;
    if (value <= upper) return index;
  }
  return count - 1;
}

/** Colour ECharts paints piece `index` of `count`: pieces sit at evenly spaced positions of the scale. */
export function pieceColor(stops: readonly [string, string, string], index: number, count: number = HEATMAP_PIECES): string {
  return scaleAt(stops, count <= 1 ? 0 : index / (count - 1));
}

/**
 * Maps every standard colour literal used by the advanced family to this palette.
 * The advanced charts spell their colours as literals in many modules, so they are recoloured
 * in one pass over the finished option; a test asserts the table covers every literal.
 */
export function advancedColorMap(p: Palette): ReadonlyMap<string, string> {
  const c = (index: number): string => cycle(p.categorical, index);
  return new Map<string, string>([
    // Categorical hues of the standard palette, by position.
    ["#0f766e", c(0)], ["#2563eb", c(1)], ["#b45309", c(2)], ["#7e22ce", c(3)], ["#be123c", c(4)],
    ["#0369a1", c(5)], ["#4d7c0f", c(6)], ["#a21caf", c(7)],
    // Event strokes that share a hue family with a categorical colour.
    ["#c2410c", c(2)], ["#1d4ed8", c(5)], ["#15803d", c(1)],
    ["#a16207", p.stage.slowing],
    // Tints used as fills behind those strokes.
    ["#99f6e4", tint(c(0))], ["#bfdbfe", tint(c(5))], ["#bbf7d0", tint(c(1))], ["#fed7aa", tint(c(2))],
    ["#e9d5ff", tint(c(3))], ["#fecdd3", tint(c(4))], ["#fde68a", tint(c(7))],
    // Legacy heatmap ramp (low and mid stops; the high stop is #0f766e above).
    ["#f0fdfa", p.sequential[0]], ["#5eead4", p.sequential[1]],
    // Neutrals.
    ["#0f172a", p.text], ["#475569", p.muted], ["#64748b", p.edge], ["#94a3b8", p.soft],
    ["#cbd5e1", p.grid], ["#e2e8f0", p.neutralLight]
  ]);
}

/** Deep copy of an option tree with every mapped colour string replaced; functions pass through. */
export function recolor<T>(value: T, map: ReadonlyMap<string, string>): T {
  if (typeof value === "string") return (map.get(value.toLowerCase()) ?? value) as T;
  if (Array.isArray(value)) return value.map((item) => recolor(item, map)) as T;
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, recolor(item, map)])) as T;
  }
  return value;
}
