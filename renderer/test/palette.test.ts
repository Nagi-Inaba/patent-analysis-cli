import { readdirSync, readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  PALETTE_IDS,
  advancedColorMap,
  alternatePalette,
  contrastRatio,
  cycle,
  inkOn,
  mix,
  recolor,
  relativeLuminance,
  scaleAt,
  tint,
  type Palette
} from "../src/palette.js";

const ALTERNATES = PALETTE_IDS.flatMap((id) => {
  const palette = alternatePalette(id);
  return palette === null ? [] : [palette];
});
const byId = (id: Palette["id"]): Palette => alternatePalette(id)!;
const WHITE = "#ffffff";

describe("palette registry", () => {
  it("keeps each family's own colours for the standard palette", () => {
    expect(alternatePalette("standard")).toBeNull();
    expect(alternatePalette(undefined)).toBeNull();
    expect(ALTERNATES.map((palette) => palette.id)).toEqual(["colorblind", "monochrome", "high-contrast"]);
  });

  it("gives every alternate distinct categorical colours and one line style per marker shape", () => {
    for (const palette of ALTERNATES) {
      expect(palette.categorical.length).toBeGreaterThanOrEqual(4);
      expect(new Set(palette.categorical).size).toBe(palette.categorical.length);
      expect(palette.lineColors).toHaveLength(palette.categorical.length);
      expect(new Set(palette.lineStyles.map((style) => style.symbol)).size).toBe(palette.lineStyles.length);
      expect(new Set(palette.lineStyles.map((style) => JSON.stringify(style.type))).size).toBe(
        palette.lineStyles.length
      );
    }
  });

  it("keeps text, axes and the first four line colours legible on white", () => {
    for (const palette of ALTERNATES) {
      expect(contrastRatio(palette.text, WHITE)).toBeGreaterThanOrEqual(7);
      expect(contrastRatio(palette.muted, WHITE)).toBeGreaterThanOrEqual(4.5);
      expect(contrastRatio(palette.axis, WHITE)).toBeGreaterThanOrEqual(3);
      expect(contrastRatio(palette.edge, WHITE)).toBeGreaterThanOrEqual(3);
      for (const color of palette.lineColors.slice(0, 4)) {
        expect(contrastRatio(color, WHITE)).toBeGreaterThanOrEqual(3);
      }
    }
  });

  it("makes every high-contrast colour at least 4.5:1 against white", () => {
    const palette = byId("high-contrast");
    for (const color of [...palette.categorical, ...Object.values(palette.stage), palette.positive, palette.negative]) {
      expect(contrastRatio(color, WHITE)).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("orders the monochrome life-cycle stages from light to dark", () => {
    const { stage } = byId("monochrome");
    const luminance = [stage.growth, stage.stable, stage.slowing, stage.decline].map(relativeLuminance);
    expect(luminance).toEqual([...luminance].sort((a, b) => b - a));
    expect(new Set(luminance).size).toBe(4);
  });

  it("darkens every sequential scale towards the high end", () => {
    for (const palette of ALTERNATES) {
      const [low, mid, high] = palette.sequential.map(relativeLuminance) as [number, number, number];
      expect(low).toBeGreaterThan(mid);
      expect(mid).toBeGreaterThan(high);
      expect(contrastRatio(palette.sequential[2], WHITE)).toBeGreaterThanOrEqual(7);
    }
  });

  it("picks white ink on dark cells and the dark text colour on light cells", () => {
    expect(inkOn("#08519c", "#0f172a")).toBe("#ffffff");
    expect(inkOn("#eaf2f9", "#0f172a")).toBe("#0f172a");
  });

  it("interpolates scales and tints without leaving the colour range", () => {
    const stops = byId("colorblind").sequential;
    expect(scaleAt(stops, 0)).toBe(stops[0]);
    expect(scaleAt(stops, 0.5)).toBe(stops[1]);
    expect(scaleAt(stops, 1)).toBe(stops[2]);
    expect(scaleAt(stops, 2)).toBe(stops[2]);
    expect(mix("#000000", "#ffffff", 0.5)).toBe("#808080");
    expect(relativeLuminance(tint("#0072b2"))).toBeGreaterThan(relativeLuminance("#0072b2"));
    expect(cycle(["a", "b", "c"], 4)).toBe("b");
    expect(cycle(["a", "b", "c"], -1)).toBe("c");
  });
});

describe("advanced recolouring", () => {
  it("replaces mapped colours deeply without touching the input, functions or other text", () => {
    const formatter = () => "#0f766e";
    const input = { a: "#0F766E", nested: [{ color: "#2563eb" }, "text #0f766e"], formatter, n: 3 };
    const map = advancedColorMap(byId("colorblind"));
    const output = recolor(input, map);

    expect(output.a).toBe("#0072b2");
    expect(output.nested).toEqual([{ color: "#009e73" }, "text #0f766e"]);
    expect(output.formatter).toBe(formatter);
    expect(output.n).toBe(3);
    expect(input.a).toBe("#0F766E");
  });

  it("maps every colour literal written in the advanced renderer modules", () => {
    const sourceRoot = new URL("../src/", import.meta.url);
    const identity = new Set(["#ffffff", "#f8fafc"]);
    const literals = new Set<string>();
    for (const name of readdirSync(sourceRoot).filter((file) => /^advanced.*\.ts$/u.test(file))) {
      const text = readFileSync(new URL(name, sourceRoot), "utf8");
      for (const match of text.matchAll(/#[0-9a-fA-F]{6}\b/gu)) literals.add(match[0].toLowerCase());
    }
    expect(literals.size).toBeGreaterThan(20);
    for (const palette of ALTERNATES) {
      const map = advancedColorMap(palette);
      const unmapped = [...literals].filter((literal) => !map.has(literal) && !identity.has(literal));
      expect(unmapped, `unmapped literals for ${palette.id}`).toEqual([]);
    }
  });

  it("produces only valid six-digit colours", () => {
    for (const palette of ALTERNATES) {
      const map = advancedColorMap(palette);
      for (const value of map.values()) expect(value).toMatch(/^#[0-9a-f]{6}$/u);
    }
  });
});
