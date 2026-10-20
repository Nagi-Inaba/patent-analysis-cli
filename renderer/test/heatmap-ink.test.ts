import { describe, expect, it } from "vitest";
import { renderAdvancedModelToRawSvg } from "../src/advanced-index.js";
import type { AdvancedModel, AdvancedSpec } from "../src/advanced-types.js";
import { PALETTE_IDS, contrastRatio, pieceColor, pieceIndexOf, type PaletteId } from "../src/palette.js";
import { SPEC, heatmapProjection, inventorModel } from "./inventor-models.js";

// On a mid-luminance cell neither near-black nor white reaches 4.5:1; the best either can do there is
// about 4.2:1 (dark ink #0f172a), so this is the floor an ink choice can honestly promise.
const BEST_WORST_CASE = 4.2;

describe("heatmap piece lookup", () => {
  it("puts a boundary value in the lower piece, like ECharts does", () => {
    // [0, 10] in five steps: [0,2] (2,4] (4,6] (6,8] (8,10]
    expect([0, 2, 2.0001, 4, 6, 8, 8.5, 10].map((value) => pieceIndexOf(value, 0, 10))).toEqual([0, 0, 1, 1, 2, 3, 4, 4]);
    expect(pieceIndexOf(1, 0, 1)).toBe(4);
    expect(pieceIndexOf(0, 0, 1)).toBe(0);
  });

  it("spaces the piece colours evenly from the first to the last stop", () => {
    const stops = ["#000000", "#808080", "#ffffff"] as const;
    expect([0, 1, 2, 3, 4].map((index) => pieceColor(stops, index))).toEqual([
      "#000000", "#404040", "#808080", "#c0c0c0", "#ffffff"
    ]);
  });
});

type Cell = { x0: number; y0: number; x1: number; y1: number; rgb: [number, number, number] };
type Label = { text: string; x: number; y: number; rgb: [number, number, number] };

function toRgb(value: string | undefined): [number, number, number] | null {
  if (value === undefined) return null;
  const hex = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/iu.exec(value);
  if (hex) return [parseInt(hex[1]!, 16), parseInt(hex[2]!, 16), parseInt(hex[3]!, 16)];
  const rgb = /^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/u.exec(value);
  return rgb ? [Number(rgb[1]), Number(rgb[2]), Number(rgb[3])] : null;
}
const asHex = (rgb: readonly number[]): string => `#${rgb.map((v) => v.toString(16).padStart(2, "0")).join("")}`;

function paintedCells(svg: string): { cells: Cell[]; labels: Label[] } {
  const cells: Cell[] = [];
  const labels: Label[] = [];
  for (const match of svg.matchAll(/<(path|text)\b([^>]*?)(?:\/>|>([^<]*)<\/text>)/gu)) {
    const attrs = match[2]!;
    const read = (name: string): string | undefined => new RegExp(`(?<![\\w-])${name}="([^"]*)"`, "u").exec(attrs)?.[1];
    if (match[1] === "path") {
      const box = /^M(-?[\d.]+) (-?[\d.]+)l(-?[\d.]+) 0l0 (-?[\d.]+)l-?[\d.]+ 0Z$/u.exec(read("d") ?? "");
      const rgb = toRgb(read("fill"));
      if (box && rgb) {
        const [x, y, w, h] = [Number(box[1]), Number(box[2]), Number(box[3]), Number(box[4])] as const;
        cells.push({ x0: x, y0: y, x1: x + w, y1: y + h, rgb });
      }
    } else {
      // ECharts text carries a translate(); the hand-drawn inventor charts carry plain x and y.
      const moved = /^translate\((-?[\d.]+)[ ,]\s*(-?[\d.]+)\)$/u.exec(read("transform") ?? "");
      const at = moved ? [Number(moved[1]), Number(moved[2])] : [Number(read("x")), Number(read("y"))];
      const rgb = toRgb(read("fill"));
      if (rgb && at.every(Number.isFinite) && /^-?\d/u.test(match[3] ?? "")) {
        labels.push({ text: match[3]!, x: at[0]!, y: at[1]!, rgb });
      }
    }
  }
  return { cells, labels };
}

function heatmapModel(values: number[], signed: boolean, palette: PaletteId): [AdvancedModel, AdvancedSpec] {
  const model: AdvancedModel = {
    chart_model_contract_version: "1.0.0", chart_type: "advanced.svg", analysis_id: signed ? "compara.v1" : "cooccurrence.v1",
    mark: signed ? "compara-svg.v1" : "cooccurrence-svg.v1", title: "synthetic", analysis_result_sha256: "0".repeat(63) + "1",
    projection: {
      kind: "heatmap", x: values.map((_, index) => `c${index}`), y: ["r"], x_label: "x", y_label: "y", signed,
      cells: values.map((value, index) => ({ x: index, y: 0, value, share: null })), context: "synthetic"
    },
    population: { input_rows: 1, analyzed_rows: 1, excluded_rows: 0 }, warnings: []
  };
  return [model, { ...SPEC, palette }];
}

function sampleValues(maximum: number, signed: boolean): number[] {
  const near = (centre: number) => [centre - 1, centre, centre + 1];
  const steps = [0, 1, 2, 3, 4, 5].flatMap((step) => near(Math.round((maximum * step) / 5)));
  const magnitudes = [...new Set([...steps, maximum].filter((value) => value >= 0 && value <= maximum))].sort((a, b) => a - b);
  return signed ? [...new Set([...magnitudes, ...magnitudes.map((value) => -value)])].sort((a, b) => a - b) : magnitudes;
}

describe("heatmap count ink", () => {
  // The scale's maximum is the largest |value|, so each case includes it.
  for (const palette of PALETTE_IDS) {
    for (const signed of [false, true]) {
      it(`keeps every count readable on its own cell (${palette}, ${signed ? "signed" : "unsigned"})`, () => {
        for (const maximum of [1, 2, 3, 5, 7, 10, 12, 100]) {
          const [model, spec] = heatmapModel(sampleValues(maximum, signed), signed, palette);
          const { cells, labels } = paintedCells(renderAdvancedModelToRawSvg(model, spec));
          expect(labels.length).toBeGreaterThan(0);
          const weak: string[] = [];
          for (const label of labels) {
            const cell = cells.find((item) => item.x0 <= label.x && label.x <= item.x1 && item.y0 <= label.y && label.y <= item.y1);
            expect(cell, `a cell under "${label.text}"`).toBeDefined();
            const ratio = contrastRatio(asHex(label.rgb), asHex(cell!.rgb));
            if (ratio < BEST_WORST_CASE) weak.push(`max ${maximum}: "${label.text}" ${ratio.toFixed(2)} on ${asHex(cell!.rgb)}`);
          }
          expect(weak).toEqual([]);
        }
      });
    }
  }

  for (const palette of PALETTE_IDS) {
    it(`keeps the inventor heatmap's counts readable on every shade (${palette})`, () => {
      const values = [0, 10, 20, 30, 40, 50, 55, 60, 70, 80, 90, 100];
      const base = heatmapProjection();
      const projection = {
        ...base, x: values.map((_, index) => `F${index}`), y: ["P"],
        cells: values.map((value, index) => ({ x: index, y: 0, value }))
      };
      const model = inventorModel("inventor-technology.v1", projection);
      const { cells, labels } = paintedCells(renderAdvancedModelToRawSvg(model, { ...SPEC, palette }));
      const weak: string[] = [];

      // The legend's own "0" and "100" sit outside the grid, so only counts over a cell are checked.
      const counts = labels.flatMap((label) => {
        const cell = cells.find((item) => item.x0 <= label.x && label.x <= item.x1 && item.y0 <= label.y && label.y <= item.y1);
        return cell === undefined ? [] : [{ label, cell }];
      });

      expect(counts).toHaveLength(values.length);
      for (const { label, cell } of counts) {
        const ratio = contrastRatio(asHex(label.rgb), asHex(cell.rgb));
        if (ratio < BEST_WORST_CASE) weak.push(`"${label.text}" ${ratio.toFixed(2)} on ${asHex(cell.rgb)}`);
      }
      expect(weak).toEqual([]);
    });
  }

  it("draws the darkest standard cells in white and the light ones in the dark ink", () => {
    const [model, spec] = heatmapModel([0, 1], false, "standard");
    const { cells, labels } = paintedCells(renderAdvancedModelToRawSvg(model, spec));
    const byText = new Map(labels.map((label) => [label.text, asHex(label.rgb)]));

    expect(cells.length).toBeGreaterThanOrEqual(2);
    expect(byText.get("1")).toBe("#ffffff");
    expect(byText.get("0")).toBe("#0f172a");
  });
});
