import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { buildAdvancedOption } from "../src/advanced-options.js";
import { renderAdvancedModelToRawSvg } from "../src/advanced-index.js";
import type { AdvancedModel, AdvancedSpec } from "../src/advanced-types.js";
import { estimateLabelSize, type Rect } from "../src/label-layout.js";

const fixtures = JSON.parse(readFileSync(new URL("./fixtures/advanced-models.json", import.meta.url), "utf8")) as {
  spec: AdvancedSpec; models: AdvancedModel[];
};
const fixtureOf = (id: string): AdvancedModel => structuredClone(fixtures.models.find((model) => model.analysis_id === id)!);

// Points that crowd each other the way real data does: coincident pairs in two corners,
// a tight column of bubbles at the right edge, and two points that stand alone.
const CROWD = [
  { id: "0", label: "Old", x: 2018, y: 12, size: 3, category: "active" },
  { id: "1", label: "Older", x: 2018, y: 12, size: 6, category: "active" },
  { id: "2", label: "New", x: 2024, y: 12, size: 4, category: "active" },
  { id: "3", label: "C", x: 2024, y: 12, size: 2, category: "active" },
  { id: "4", label: "Col1", x: 2024, y: 7, size: 5, category: "active" },
  { id: "5", label: "Col2", x: 2024, y: 6, size: 4, category: "active" },
  { id: "6", label: "Col3", x: 2024, y: 5, size: 3, category: "active" },
  { id: "7", label: "Solo", x: 2021, y: 3, size: 2, category: "active" },
  { id: "8", label: "Alone", x: 2020, y: 9, size: 8, category: "active" }
];

function crowded(kind: "scatter" | "quadrant"): AdvancedModel {
  const model = fixtureOf(kind === "scatter" ? "citation.v1" : "growth-quadrant.v1");
  const projection = model.projection;
  if (projection.kind !== "scatter" && projection.kind !== "quadrant") throw new Error("fixture");
  projection.points = kind === "quadrant"
    ? CROWD.map((point) => ({ ...point, x: point.x - 2021, y: point.y - 6 }))
    : CROWD.map((point) => ({ ...point }));
  return model;
}

type Text = { text: string; rect: Rect };

/** Every unrotated text in the SVG, boxed with the module's own size estimate. */
function textBoxes(svg: string): Text[] {
  const boxes: Text[] = [];
  for (const match of svg.matchAll(/<text\b([^>]*)>([^<]*)<\/text>/gu)) {
    const attrs = match[1]!;
    const read = (name: string): string | undefined => new RegExp(`(?<![\\w-])${name}="([^"]*)"`, "u").exec(attrs)?.[1];
    const transform = read("transform") ?? "";
    if (transform.startsWith("matrix")) continue;
    const moved = /^translate\((-?[\d.]+),(-?[\d.]+)\)$/u.exec(transform);
    const x = (moved ? Number(moved[1]) : 0) + Number(read("x") ?? 0);
    const y = (moved ? Number(moved[2]) : 0) + Number(read("y") ?? 0);
    const size = Number(read("font-size") ?? 12);
    const { width, height } = estimateLabelSize(match[2]!, size);
    const anchor = read("text-anchor");
    const left = anchor === "middle" ? x - width / 2 : anchor === "end" ? x - width : x;
    boxes.push({ text: match[2]!, rect: { left, top: y - height / 2, right: left + width, bottom: y + height / 2 } });
  }
  return boxes;
}
const INSET = 2;
const crosses = (a: Rect, b: Rect): boolean =>
  a.left + INSET < b.right - INSET && b.left + INSET < a.right - INSET &&
  a.top + INSET < b.bottom - INSET && b.top + INSET < a.bottom - INSET;

describe("scatter and quadrant point labels", () => {
  for (const kind of ["scatter", "quadrant"] as const) {
    it(`${kind}: no point label lands on another label or on chart text`, () => {
      const model = crowded(kind);
      const all = textBoxes(renderAdvancedModelToRawSvg(model, fixtures.spec));
      const p = model.projection;
      if (p.kind !== "scatter" && p.kind !== "quadrant") throw new Error("fixture");
      const wanted = new Set(p.points.map((point) => point.label));
      const labels = all.filter((item) => wanted.has(item.text));
      const clashes: string[] = [];

      expect(labels.map((item) => item.text).sort()).toEqual([...wanted].sort());
      all.forEach((first, a) => all.slice(a + 1).forEach((second) => {
        const isLabel = wanted.has(first.text) || wanted.has(second.text);
        if (isLabel && crosses(first.rect, second.rect)) clashes.push(`${first.text} / ${second.text}`);
      }));
      expect(clashes).toEqual([]);
    });
  }

  it("renders the small fixtures, with and without points, without error", () => {
    for (const id of ["entry-exit.v1", "citation.v1", "growth-quadrant.v1"]) {
      expect(() => renderAdvancedModelToRawSvg(fixtureOf(id), fixtures.spec)).not.toThrow();
    }
  });

  it("hides the labels in the measuring pass and shows them with slots otherwise", () => {
    const shown = (placement: Parameters<typeof buildAdvancedOption>[2]) => {
      const series = buildAdvancedOption(crowded("scatter"), fixtures.spec, placement).series as Array<{ data: Array<{ label: { show: boolean } }> }>;
      return series[0]!.data.map((item) => item.label.show);
    };

    expect(shown("hidden").every((flag) => flag === false)).toBe(true);
    expect(shown([]).every((flag) => flag === true)).toBe(true);
  });

  it("applies a slot's side and offset to the label of that point", () => {
    const series = buildAdvancedOption(crowded("scatter"), fixtures.spec, [
      { position: "right" }, { position: "top", offset: [0, -16] }
    ]).series as Array<{ data: Array<{ label: { position: string; offset?: number[] } }> }>;

    expect(series[0]!.data[0]!.label.position).toBe("right");
    expect(series[0]!.data[1]!.label.position).toBe("top");
    expect(series[0]!.data[1]!.label.offset).toEqual([0, -16]);
    expect(series[0]!.data[2]!.label.position).toBe("top");
  });
});
