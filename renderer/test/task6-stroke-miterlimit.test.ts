import { describe, expect, it } from "vitest";
import { normalizeEChartsSvg } from "../src/categorical-svg-normalize.js";
import { normalizeEChartsSvg as normalizeFrozenSvg } from "../src/svg-normalize.js";

function root(content: string): string {
  return `<svg width="1200" height="675" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" baseProfile="full" viewBox="0 0 1200 675">${content}</svg>`;
}

function pathSvg(pathAttributes = "", stroke = "#2563EB"): string {
  return root(
    `<path d="M0 0L10 10" fill="none" stroke="${stroke}" ${pathAttributes}/>`
  );
}

function polylineSvg(points: string): string {
  return root(`<polyline points="${points}" fill="none" stroke="#2563EB"/>`);
}

describe("categorical SVG sanitizer regressions", () => {
  it("keeps the frozen Ranking and Matrix sanitizer policy unchanged", () => {
    expect(() =>
      normalizeFrozenSvg(pathSvg('stroke-linejoin="miter" stroke-miterlimit="10"'))
    ).toThrow(/unknown attribute path\.stroke-miterlimit/u);
  });

  it("preserves a bounded ECharts path stroke-miterlimit", () => {
    const normalized = normalizeEChartsSvg(
      pathSvg('stroke-linejoin="miter" stroke-miterlimit="10"')
    );
    expect(normalized).toContain('stroke-miterlimit="10"');
  });

  it.each(["0", "-1", "1001", "NaN", "1e3"])(
    "rejects unsafe or noncanonical stroke-miterlimit %s",
    (value) => {
      expect(() => normalizeEChartsSvg(pathSvg(`stroke-miterlimit="${value}"`))).toThrow(
        /SVG normalization rejected/u
      );
    }
  );

  it("does not broaden stroke-miterlimit to unrelated elements", () => {
    const raw = root(
      '<rect x="0" y="0" width="10" height="10" stroke="#2563EB" stroke-miterlimit="10"/>'
    );
    expect(() => normalizeEChartsSvg(raw)).toThrow(
      /unknown attribute rect\.stroke-miterlimit/u
    );
  });

  it("accepts the three-digit hexadecimal paint emitted by ECharts", () => {
    const normalized = normalizeEChartsSvg(pathSvg("", "#000"));
    expect(normalized).toContain('stroke="#000"');
  });

  it.each(["#0000", "#00000000", "#GGG"])(
    "does not broaden hexadecimal paint syntax to %s",
    (value) => {
      expect(() => normalizeEChartsSvg(pathSvg("", value))).toThrow(/invalid paint/u);
    }
  );

  it.each(["chart", "legend"])(
    "accepts and removes the closed ECharts SSR item type %s",
    (value) => {
      const normalized = normalizeEChartsSvg(pathSvg(`ecmeta_ssr_type="${value}"`));
      expect(normalized).not.toContain("ecmeta_ssr_type");
    }
  );

  it.each(["", "axis", "Legend", "chart "])(
    "rejects unknown ECharts SSR item type %s",
    (value) => {
      expect(() => normalizeEChartsSvg(pathSvg(`ecmeta_ssr_type="${value}"`))).toThrow(
        /invalid ECharts metadata/u
      );
    }
  );

  it("accepts and canonicalizes the whitespace-only point list emitted by ECharts", () => {
    const normalized = normalizeEChartsSvg(
      polylineSvg("652 223.3 662.6 212.7 692.6 212.7")
    );
    expect(normalized).toContain('points="652,223.3 662.6,212.7 692.6,212.7"');
  });

  it("preserves the existing canonical comma-pair point-list form", () => {
    const normalized = normalizeEChartsSvg(polylineSvg("0,0 1,1"));
    expect(normalized).toContain('points="0,0 1,1"');
  });

  it.each([
    "0 0",
    "0 0 1",
    " 0 0 1 1",
    "0 0 1 1 ",
    "0,0 1 1",
    "0,0,1,1",
    "0,,0 1,1",
    "0 0 1e3 1",
    "-0 0 1 1",
    "0 0 1000001 1"
  ])("rejects malformed, mixed, or unbounded point list %s", (value) => {
    expect(() => normalizeEChartsSvg(polylineSvg(value))).toThrow(/invalid point/u);
  });
});
