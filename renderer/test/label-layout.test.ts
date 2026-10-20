import { describe, expect, it } from "vitest";
import {
  LABEL_DISTANCE,
  estimateLabelSize,
  placeLabels,
  type LabelSlot,
  type LabelSubject,
  type Rect
} from "../src/label-layout.js";

const BOUNDS: Rect = { left: 0, top: 0, right: 1000, bottom: 600 };
const subject = (x: number, y: number, radius = 8, width = 30, height = 14): LabelSubject => ({
  x, y, radius, width, height
});

/** The rectangle a slot gives a label, rebuilt independently of the module under test. */
function rectOf(item: LabelSubject, slot: LabelSlot): Rect {
  const reach = item.radius + LABEL_DISTANCE;
  const [dx, dy] = slot.offset ?? [0, 0];
  const at: Record<LabelSlot["position"], Rect> = {
    top: { left: item.x - item.width / 2, top: item.y - reach - item.height, right: item.x + item.width / 2, bottom: item.y - reach },
    bottom: { left: item.x - item.width / 2, top: item.y + reach, right: item.x + item.width / 2, bottom: item.y + reach + item.height },
    right: { left: item.x + reach, top: item.y - item.height / 2, right: item.x + reach + item.width, bottom: item.y + item.height / 2 },
    left: { left: item.x - reach - item.width, top: item.y - item.height / 2, right: item.x - reach, bottom: item.y + item.height / 2 }
  };
  const rect = at[slot.position];
  return { left: rect.left + dx, top: rect.top + dy, right: rect.right + dx, bottom: rect.bottom + dy };
}
const crosses = (a: Rect, b: Rect): boolean =>
  a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
const hitsBubble = (rect: Rect, bubble: LabelSubject): boolean => {
  const nearestX = Math.min(Math.max(bubble.x, rect.left), rect.right);
  const nearestY = Math.min(Math.max(bubble.y, rect.top), rect.bottom);
  return Math.hypot(nearestX - bubble.x, nearestY - bubble.y) < bubble.radius;
};

describe("estimateLabelSize", () => {
  it("counts a full-width glyph as one em and other glyphs as about 0.6 em", () => {
    expect(estimateLabelSize("成長", 12)).toEqual({ width: 12 * 2 + 4, height: 14 });
    expect(estimateLabelSize("Old", 10).width).toBeCloseTo(10 * 0.6 * 3 + 4);
    expect(estimateLabelSize("", 12).width).toBe(4);
  });
});

describe("placeLabels", () => {
  it("keeps every label above its point when nothing collides", () => {
    const slots = placeLabels([subject(100, 300), subject(400, 300), subject(700, 100)], BOUNDS);

    expect(slots).toEqual([{ position: "top" }, { position: "top" }, { position: "top" }]);
  });

  it("moves labels of points at the same coordinates apart", () => {
    const items = [subject(500, 300, 10), subject(500, 300, 8), subject(500, 300, 6)];
    const slots = placeLabels(items, BOUNDS);
    const rects = items.map((item, index) => rectOf(item, slots[index]!));

    expect(slots[0]).toEqual({ position: "top" });
    expect(new Set(slots.map((slot) => JSON.stringify(slot))).size).toBe(3);
    for (let a = 0; a < rects.length; a += 1) {
      for (let b = a + 1; b < rects.length; b += 1) expect(crosses(rects[a]!, rects[b]!)).toBe(false);
    }
  });

  it("stacks the labels of many coincident points instead of overlapping them", () => {
    const items = Array.from({ length: 7 }, () => subject(500, 300));
    const slots = placeLabels(items, BOUNDS);
    const rects = items.map((item, index) => rectOf(item, slots[index]!));

    for (let a = 0; a < rects.length; a += 1) {
      for (let b = a + 1; b < rects.length; b += 1) expect(crosses(rects[a]!, rects[b]!)).toBe(false);
    }
  });

  it("keeps a label off the bubble of a neighbouring point", () => {
    // Three bubbles in a column, closer than a label is tall: a label above the lower two
    // would sit on the bubble above it.
    const items = [subject(500, 200, 14), subject(500, 233, 14), subject(500, 266, 14)];
    const slots = placeLabels(items, BOUNDS);

    items.forEach((item, index) => {
      const rect = rectOf(item, slots[index]!);
      items.forEach((other, at) => {
        if (at !== index) expect(hitsBubble(rect, other), `label ${index} on bubble ${at}`).toBe(false);
      });
    });
  });

  it("keeps a label off text the chart already draws", () => {
    const title: Rect = { left: 480, top: 270, right: 520, bottom: 290 };
    const [slot] = placeLabels([subject(500, 300)], BOUNDS, [title]);

    expect(crosses(rectOf(subject(500, 300), slot!), title)).toBe(false);
  });

  it("keeps labels inside the bounds when there is room", () => {
    const edge = subject(995, 300);
    const [slot] = placeLabels([edge], BOUNDS);
    const rect = rectOf(edge, slot!);

    expect(rect.right).toBeLessThanOrEqual(BOUNDS.right);
    expect(rect.left).toBeGreaterThanOrEqual(BOUNDS.left);
  });

  it("falls back to the least-overlapping slot when every slot is blocked", () => {
    const blocked: Rect = { left: 0, top: 0, right: 1000, bottom: 600 };
    const slots = placeLabels([subject(500, 300)], BOUNDS, [blocked]);

    expect(slots).toHaveLength(1);
    expect(slots[0]).toBeDefined();
  });

  it("is deterministic and does not modify its input", () => {
    const items = [subject(500, 300, 10), subject(500, 300, 8), subject(520, 310)];
    const before = JSON.stringify(items);

    expect(placeLabels(items, BOUNDS)).toEqual(placeLabels(items, BOUNDS));
    expect(JSON.stringify(items)).toBe(before);
    expect(placeLabels([], BOUNDS)).toEqual([]);
  });
});
