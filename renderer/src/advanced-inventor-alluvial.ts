import { AREA, LINE, MUTED, TEXT, frame, lineAt, shape, textAt, type Graphic } from "./advanced-inventor-frame.js";
import { displayLabel, fixed } from "./advanced-text.js";
import type { AdvancedModel, AdvancedSpec, InventorAlluvialProjection } from "./advanced-types.js";

type NodeKind = InventorAlluvialProjection["nodes"][number]["kind"];
type LinkKind = InventorAlluvialProjection["links"][number]["kind"];
const LEFT = 70;
const RIGHT = 1130;
const TOP = 188;
const HEIGHT = 372;
const GAP = 8;
/** Fixed non-quantitative slot of a zero-member marker, and the hairline marker for boxes below MARKER_BELOW px. */
const ZERO_SLOT = 3;
const MARKER_BELOW = 2;
const MARKER_WIDTH = 2;
const CURVE_STEPS = 12;
const LINK_STYLE: Readonly<Record<LinkKind, { fill: string; label: string; stroke?: string; dash?: number[] }>> = Object.freeze({
  continuation: { fill: "#99f6e4", label: "継続" },
  split: { fill: "#bfdbfe", label: "分岐" },
  merge: { fill: "#fde68a", label: "合流" },
  gap: { fill: "#f8fafc", label: "空白年をまたぐ", stroke: LINE, dash: [5, 3] },
  newly_observed: { fill: "#bbf7d0", label: "新規観測からの流入" },
  not_observed: { fill: "#e2e8f0", label: "観測なしへの流出" }
});
const BOX_STYLE: Readonly<Record<NodeKind, { fill: string; stroke: string; dash?: number[]; label: string; text: string }>> = Object.freeze({
  cluster: { fill: "#0f766e", stroke: "#ffffff", label: "協働グループ", text: "#ffffff" },
  newly_observed: { fill: "#ffffff", stroke: "#15803d", dash: [3, 2], label: "新規観測", text: TEXT },
  not_observed: { fill: "#ffffff", stroke: LINE, dash: [3, 2], label: "観測なし", text: TEXT }
});
const smooth = (t: number) => t * t * (3 - 2 * t);

export function buildAlluvial(model: AdvancedModel, spec: AdvancedSpec, p: InventorAlluvialProjection): Record<string, unknown> {
  const count = p.years.length;
  const boxWidth = count > 10 ? 28 : 40;
  const pitch = count > 1 ? (RIGHT - LEFT - boxWidth) / (count - 1) : 0;
  const columnX = (year: number) => LEFT + (year - (p.years[0] ?? year)) * pitch;
  const columns = new Map<number, number[]>();
  p.nodes.forEach((node, index) => columns.set(node.year, [...(columns.get(node.year) ?? []), index]));
  // One scale for every box and every ribbon: height = members * scale (no minimum), width = shared persons * scale.
  // Spacing between boxes and the fixed slot of a zero-member marker are non-quantitative; they are reserved per column
  // (shrunk to at most half of HEIGHT) before the scale is derived, so the last box always ends by TOP + HEIGHT.
  const nonQuantitative = (indices: number[]) => {
    const want = GAP * (indices.length - 1) + ZERO_SLOT * indices.filter(index => p.nodes[index]!.members === 0).length;
    const shrink = want > HEIGHT / 2 ? HEIGHT / 2 / want : 1;
    return { shrink, reserved: want * shrink };
  };
  let scale = 24;
  for (const indices of columns.values()) {
    const total = indices.reduce((sum, index) => sum + p.nodes[index]!.members, 0);
    scale = Math.min(scale, (HEIGHT - nonQuantitative(indices).reserved) / Math.max(1, total));
  }
  const box = new Array<{ x: number; y: number; h: number; slot: number }>(p.nodes.length);
  for (const indices of columns.values()) {
    const { shrink } = nonQuantitative(indices);
    let y = TOP;
    for (const index of indices) {
      const node = p.nodes[index]!;
      const h = node.members * scale, slot = node.members === 0 ? ZERO_SLOT * shrink : 0;
      box[index] = { x: columnX(node.year), y, h, slot };
      y += h + slot + GAP * shrink;
    }
  }

  const elements: Graphic[] = [];
  p.years.forEach(year => {
    elements.push(textAt(spec, columnX(year) + boxWidth / 2, AREA.top + 8, String(year), { align: "center", size: count > 15 ? 9 : 11, weight: 600 }));
  });

  // Ribbons stack inside each box in the order of the box they connect to, which limits crossings.
  const offsets = p.links.map(() => ({ out: 0, into: 0 }));
  p.nodes.forEach((_, index) => {
    for (const side of ["out", "into"] as const) {
      const own = p.links.map((link, at) => ({ link, at }))
        .filter(({ link }) => (side === "out" ? link.source : link.target) === index)
        .sort((a, b) => {
          const other = (item: typeof a) => box[side === "out" ? item.link.target : item.link.source]!.y;
          return other(a) - other(b) || a.at - b.at;
        });
      let used = 0;
      for (const { link, at } of own) {
        offsets[at]![side] = used;
        used += link.value * scale;
      }
    }
  });
  p.links.forEach((link, index) => {
    const from = box[link.source]!, to = box[link.target]!, style = LINK_STYLE[link.kind];
    const width = link.value * scale;
    const x0 = from.x + boxWidth, x1 = to.x;
    const y0 = from.y + offsets[index]!.out, y1 = to.y + offsets[index]!.into;
    const top: [number, number][] = [];
    for (let step = 0; step <= CURVE_STEPS; step++) {
      const t = step / CURVE_STEPS;
      top.push([x0 + (x1 - x0) * t, y0 + (y1 - y0) * smooth(t)]);
    }
    const outline = [...top, ...[...top].reverse().map(([x, y]): [number, number] => [x, y + width])];
    elements.push(shape("polygon", { points: outline.map(([x, y]) => [fixed(x), fixed(y)]) },
      { fill: style.fill, stroke: style.stroke ?? "none", lineWidth: style.stroke ? 1 : 0, ...(style.dash ? { lineDash: style.dash } : {}) }));
  });

  p.nodes.forEach((node, index) => {
    const at = box[index]!, style = BOX_STYLE[node.kind];
    // Only members > 0 is a quantitative box. A hairline marker (a path, never a box) keeps tiny or zero boxes findable.
    if (node.members > 0) {
      const corners: [number, number][] = [[at.x, at.y], [at.x + boxWidth, at.y], [at.x + boxWidth, at.y + at.h], [at.x, at.y + at.h]];
      elements.push(shape("polygon", { points: corners.map(([x, y]) => [fixed(x), fixed(y)]) },
        { fill: style.fill, stroke: style.stroke, lineWidth: node.kind === "cluster" ? 1 : 1.5, ...(style.dash ? { lineDash: style.dash } : {}) }));
    }
    if (at.h < MARKER_BELOW) {
      const my = at.y + (at.slot || at.h) / 2;
      elements.push(lineAt(at.x, my, at.x + boxWidth, my, node.kind === "cluster" ? style.fill : style.stroke,
        at.slot || MARKER_WIDTH, style.dash));
    }
    if (at.h >= 11) elements.push(textAt(spec, at.x + boxWidth / 2, at.y + at.h / 2, String(node.members), { align: "center", size: 9, color: style.text }));
    // Labels sit right of a box; the last column has no space there, so its labels sit on the left.
    const lastColumn = count > 1 && node.year === p.years[count - 1];
    const room = (count > 1 ? pitch : 1190 - at.x) - boxWidth - 8;
    if (room >= 40) {
      const text = displayLabel(node.label, Math.floor(room / 10));
      elements.push(lastColumn
        ? textAt(spec, at.x - 4, at.y + Math.min((at.slot || at.h) / 2, 8), text, { size: 10, align: "right" })
        : textAt(spec, at.x + boxWidth + 4, at.y + Math.min((at.slot || at.h) / 2, 8), text, { size: 10 }));
    }
  });

  // Legend: what the picture shows, and what it deliberately does not claim.
  let x = AREA.left;
  const row1 = 580, row2 = 598;
  elements.push(textAt(spec, x, row1, "リンク:", { size: 10, weight: 600 }));
  x += 52;
  for (const kind of Object.keys(LINK_STYLE) as LinkKind[]) {
    const style = LINK_STYLE[kind];
    elements.push(shape("polygon", { points: [[x, row1 - 5], [x + 24, row1 - 5], [x + 24, row1 + 5], [x, row1 + 5]] },
      { fill: style.fill, stroke: style.stroke ?? "none", lineWidth: style.stroke ? 1 : 0, ...(style.dash ? { lineDash: style.dash } : {}) }));
    elements.push(textAt(spec, x + 30, row1, style.label, { size: 10 }));
    x += 30 + style.label.length * 10 + 14;
  }
  x = AREA.left;
  elements.push(textAt(spec, x, row2, "ボックス:", { size: 10, weight: 600 }));
  x += 62;
  for (const kind of Object.keys(BOX_STYLE) as NodeKind[]) {
    const style = BOX_STYLE[kind];
    elements.push(shape("polygon", { points: [[x, row2 - 5], [x + 24, row2 - 5], [x + 24, row2 + 5], [x, row2 + 5]] },
      { fill: style.fill, stroke: style.stroke, lineWidth: 1, ...(style.dash ? { lineDash: style.dash } : {}) }));
    elements.push(textAt(spec, x + 30, row2, style.label, { size: 10 }));
    x += 30 + style.label.length * 10 + 14;
  }
  [
    "リンクの幅は、前後のボックスで共有して観測された人数です (確率や部門ではありません)。",
    "新規観測・観測なしは観測上の出入りで、入社や退職を意味しません。年をまたぐ空白は継続として描きません。",
    "ボックスの高さと数字は各年の観測人数で、全体で同じ縮尺です (細い線は位置の目印で、人数ではありません)。"
  ].forEach((text, index) => elements.push(textAt(spec, AREA.left, row2 + 20 * (index + 1), text, { size: 10, color: MUTED })));
  return frame(model, spec, p.nodes.length === 0, elements);
}
