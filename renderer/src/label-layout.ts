/**
 * Collision-free placement of point labels on a scatter plot.
 *
 * Every point asks for its label above it. A label that would land on another label, another
 * point's bubble, or text the chart already draws (titles, axis names, tick labels, the legend)
 * moves to the next free slot instead: right, below, left, then stacked higher above the point.
 * Labels that collide with nothing keep the requested slot, so a plot without overlaps is not
 * changed. The placement is a pure function of the pixel geometry, so it is deterministic.
 */

export type LabelSide = "top" | "right" | "bottom" | "left";
export type LabelSlot = { readonly position: LabelSide; readonly offset?: readonly [number, number] };
export type Rect = { readonly left: number; readonly top: number; readonly right: number; readonly bottom: number };
/** A point in pixels: its bubble (centre and radius) and the size its label needs. */
export type LabelSubject = {
  readonly x: number;
  readonly y: number;
  readonly radius: number;
  readonly width: number;
  readonly height: number;
};

/** Gap ECharts leaves between a symbol and its label. */
export const LABEL_DISTANCE = 5;
const STACK_TIERS = 3;
const STACK_GAP = 2;
const SIDES: readonly LabelSide[] = ["top", "right", "bottom", "left"];

/** Estimated label size: a full-width glyph is one em, anything else about 0.6 em, plus padding. */
export function estimateLabelSize(text: string, fontSize: number): { width: number; height: number } {
  let width = 0;
  for (const char of text) {
    const code = char.codePointAt(0)!;
    width += code >= 0x2e80 || (code >= 0xff00 && code <= 0xffef) ? fontSize : fontSize * 0.6;
  }
  return { width: width + 4, height: fontSize + 2 };
}

function labelRect(subject: LabelSubject, slot: LabelSlot): Rect {
  const { x, y, radius, width, height } = subject;
  const reach = radius + LABEL_DISTANCE;
  const [dx, dy] = slot.offset ?? [0, 0];
  let rect: Rect;
  switch (slot.position) {
    case "top": rect = { left: x - width / 2, top: y - reach - height, right: x + width / 2, bottom: y - reach }; break;
    case "bottom": rect = { left: x - width / 2, top: y + reach, right: x + width / 2, bottom: y + reach + height }; break;
    case "right": rect = { left: x + reach, top: y - height / 2, right: x + reach + width, bottom: y + height / 2 }; break;
    case "left": rect = { left: x - reach - width, top: y - height / 2, right: x - reach, bottom: y + height / 2 }; break;
  }
  return { left: rect.left + dx, top: rect.top + dy, right: rect.right + dx, bottom: rect.bottom + dy };
}

function overlapArea(a: Rect, b: Rect): number {
  const width = Math.min(a.right, b.right) - Math.max(a.left, b.left);
  const height = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
  return width > 0 && height > 0 ? width * height : 0;
}

/** Area of the rectangle that is inside the circle's bounding square, a cheap bound on the real overlap. */
function bubbleOverlap(rect: Rect, subject: LabelSubject): number {
  const { x, y, radius } = subject;
  const nearestX = Math.min(Math.max(x, rect.left), rect.right);
  const nearestY = Math.min(Math.max(y, rect.top), rect.bottom);
  if (Math.hypot(nearestX - x, nearestY - y) >= radius) return 0;
  return overlapArea(rect, { left: x - radius, top: y - radius, right: x + radius, bottom: y + radius });
}

function outsideArea(rect: Rect, area: Rect): number {
  const whole = (rect.right - rect.left) * (rect.bottom - rect.top);
  return whole - overlapArea(rect, area);
}

function candidateSlots(subject: LabelSubject): LabelSlot[] {
  const stacked = Array.from({ length: STACK_TIERS }, (_, tier): LabelSlot => ({
    position: "top",
    offset: [0, -(tier + 1) * (subject.height + STACK_GAP)]
  }));
  return [...SIDES.map((position): LabelSlot => ({ position })), ...stacked];
}

/**
 * One slot per subject, in order. `bounds` is where a label may sit and `obstacles` is text that is
 * already on the chart. A subject whose every slot collides takes the least-overlapping one.
 */
export function placeLabels(
  subjects: readonly LabelSubject[],
  bounds: Rect,
  obstacles: readonly Rect[] = []
): LabelSlot[] {
  const placed: Rect[] = [];
  return subjects.map((subject, index) => {
    let best: { slot: LabelSlot; rect: Rect; cost: number } | null = null;
    for (const slot of candidateSlots(subject)) {
      const rect = labelRect(subject, slot);
      let cost = outsideArea(rect, bounds);
      for (const other of placed) cost += overlapArea(rect, other);
      for (const other of obstacles) cost += overlapArea(rect, other);
      subjects.forEach((neighbour, at) => {
        if (at !== index) cost += bubbleOverlap(rect, neighbour);
      });
      if (best === null || cost < best.cost) best = { slot, rect, cost };
      if (cost === 0) break;
    }
    placed.push(best!.rect);
    return best!.slot;
  });
}

type Box = { x: number; y: number; width: number; height: number; clone(): Box; applyTransform(matrix: ArrayLike<number>): void };
type TextElement = { style?: { text?: unknown }; transform?: ArrayLike<number> | null; getBoundingRect(): Box };
type ChartWithStorage = { getZr(): { storage: { getDisplayList(update?: boolean, includeIgnore?: boolean): unknown[] } } };

/**
 * Pixel boxes of every piece of text the chart has drawn so far (titles, axis names, ticks, the
 * legend). Call it while the point labels are hidden so only the fixed text is returned.
 */
export function drawnTextBoxes(chart: unknown): Rect[] {
  const list = (chart as ChartWithStorage).getZr().storage.getDisplayList(true, true) as TextElement[];
  return list.flatMap((element) => {
    const text = element.style?.text;
    if (typeof text !== "string" || text === "") return [];
    const box = element.getBoundingRect().clone();
    if (element.transform) box.applyTransform(element.transform);
    return [{ left: box.x, top: box.y, right: box.x + box.width, bottom: box.y + box.height }];
  });
}
