import { DOMParser } from "@xmldom/xmldom";
import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import {
  renderChartModelToMeasuredCssSvg,
  renderChartModelToRawSvg
} from "../src/index.js";
import type { ChartModel, RenderSpec } from "../src/payload.js";

const model: ChartModel = {
  chart_model_contract_version: "1.0.0",
  chart_type: "ranking.horizontal_bar",
  analysis_result_sha256: "a".repeat(64),
  label_overlay_sha256: null,
  title: "出願人のランキング",
  dimension: { source_label: "applicant", display_label: "出願人", description: null },
  measure: { mode: "count", column: null },
  population: { input_rows: 8, analyzed_rows: 8 },
  rows: [
    {
      index: 0,
      row_kind: "dimension_value",
      source_label: "甲社",
      display_label: "甲社",
      description: null,
      semantic_label: "データ中の分類値",
      value: 5,
      count: 5,
      share: 0.625
    },
    {
      index: 1,
      row_kind: "remainder",
      source_label: "その他",
      display_label: "その他",
      description: null,
      semantic_label: "上位表示外の合計",
      value: 3,
      count: 3,
      share: 0.375
    }
  ],
  warnings: []
};

const spec: RenderSpec = {
  render_spec_contract_version: "1.0.0",
  renderer_kind: "ranking.horizontal_bar.svg",
  locale: "ja-JP",
  timezone: "UTC",
  width: 1200,
  height: 675,
  font_family: "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif",
  animation: false,
  axis_label_max_graphemes: 28,
  echarts_version: "6.1.0",
  render_profile_id: "ranking-svg-ja-jp-node22-echarts6.v1"
};

async function loadNormalizer() {
  try {
    const modulePath = "../src/svg-normalize.ts";
    return { loaded: true, module: await import(modulePath) } as const;
  } catch {
    return { loaded: false } as const;
  }
}

function allElements(svg: string) {
  const document = new DOMParser({ onError: () => { throw new Error("invalid normalized XML"); } })
    .parseFromString(svg, "image/svg+xml");
  return Array.from(document.getElementsByTagName("*"));
}

function wrapSvg(content: string, extraRoot = ""): string {
  return `<svg width="1200" height="675" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" baseProfile="full" viewBox="0 0 1200 675"${extraRoot}>${content}</svg>`;
}

function nestedGroups(depthIncludingRoot: number): string {
  const nested = Math.max(0, depthIncludingRoot - 1);
  return wrapSvg(`${"<g>".repeat(nested)}${"</g>".repeat(nested)}`);
}

function exactPathBytes(target: number): string {
  const prefix = "M0 0";
  const segment = "L1000000.000000000000 1000000.000000000000";
  const segmentCount = Math.floor((target - prefix.length) / segment.length);
  const partial = prefix + segment.repeat(segmentCount);
  return partial + " ".repeat(target - partial.length);
}

describe("lossless ECharts SVG normalization", () => {
  it("preserves ECharts whitespace on text nodes in both closed SVG policies", async () => {
    const ranking = await import("../src/svg-normalize.js");
    const categorical = await import("../src/categorical-svg-normalize.js");
    const raw = renderChartModelToRawSvg({ ...model, title: '出願人 <&> "引用"' }, spec);
    expect(raw).toContain('xml:space="preserve"');
    for (const normalize of [ranking.normalizeEChartsSvg, categorical.normalizeEChartsSvg]) {
      const svg = normalize(raw);
      expect(svg).toContain('xml:space="preserve"');
      expect(allElements(svg).some(element => element.textContent?.includes('出願人 <&> "引用"'))).toBe(true);
      for (const bad of [
        '<text xml:space="default">A B</text>',
        '<g xml:space="preserve"/>',
        '<text xml:lang="ja">A B</text>',
        '<text xmlns:p="https://example.invalid" p:space="preserve">A B</text>'
      ]) expect(() => normalize(wrapSvg(bad))).toThrow();
    }
  });

  it("proves the actual ECharts 6.1.0 SSR fixture emits CSS-bearing markup", async () => {
    const raw = renderChartModelToMeasuredCssSvg(model, spec);
    const loaded = await loadNormalizer();
    expect(loaded.loaded).toBe(true);
    if (!loaded.loaded) return;

    expect(raw).toContain("<style");
    expect(raw).toMatch(/\sclass="/u);
    expect(raw).toMatch(/\sstyle="/u);
    expect(raw).toContain("<![CDATA[");
    expect(() => loaded.module.normalizeEChartsSvg(raw)).toThrow(/forbidden XML construct|CDATA/u);
  });

  it("materializes static presentation and removes only proven ECharts metadata", async () => {
    const loaded = await loadNormalizer();
    expect(loaded).toEqual({
      loaded: true,
      module: expect.objectContaining({ normalizeEChartsSvg: expect.any(Function) })
    });
    if (!loaded.loaded) return;
    const raw = renderChartModelToRawSvg(model, spec);
    expect(raw).not.toContain("<![CDATA[");

    const normalized = loaded.module.normalizeEChartsSvg(raw);
    const elements = allElements(normalized);
    const attributeNames = elements.flatMap((element) =>
      Array.from(element.attributes, (attribute) => attribute.name)
    );

    expect(elements.map(({ localName }) => localName)).not.toContain("style");
    for (const forbidden of [
      "style", "class", "pointer-events", "version", "baseProfile", "xmlns:xlink",
      "ecmeta_series_index", "ecmeta_data_index", "ecmeta_ssr_type"
    ]) expect(attributeNames).not.toContain(forbidden);
    for (const preserved of [
      "#FFFFFF", "#2563EB", "#94A3B8", "#0F172A", "#E2E8F0",
      "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif", "甲社", "その他", "5", "3"
    ]) expect(normalized).toContain(preserved);
    expect(normalized.indexOf("甲社")).toBeLessThan(normalized.indexOf("その他"));
    expect(normalized).toContain('stroke-dasharray="4 2"');
    expect(normalized).toContain('font-family="Yu Gothic UI, Yu Gothic, Meiryo, sans-serif"');
  });

  it("reduces the measured plain-text ECharts hover subset without CDATA", async () => {
    const loaded = await loadNormalizer();
    expect(loaded.loaded).toBe(true);
    if (!loaded.loaded) return;
    const raw = wrapSvg('<rect class="zr0-cls-0" width="1" height="1" x="0" y="0" fill="#2563EB"/><style>.zr0-cls-0:hover {pointer-events:none;}</style>');

    const normalized = loaded.module.normalizeEChartsSvg(raw);

    expect(normalized).not.toContain("<style");
    expect(normalized).not.toContain(' class="');
    expect(normalized).toContain('fill="#2563EB"');
  });

  it("normalizes IDs once in document order and updates each internal fragment reference", async () => {
    const loaded = await loadNormalizer();
    expect(loaded.loaded).toBe(true);
    if (!loaded.loaded) return;
    const raw = `<svg width="1200" height="675" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" baseProfile="full" viewBox="0 0 1200 675"><defs><clipPath id="zr0-clip-9"><rect width="20" height="20" x="0" y="0"/></clipPath><clipPath id="zr0-clip-2"><rect width="10" height="10" x="0" y="0"/></clipPath></defs><g clip-path="url(#zr0-clip-2)"><rect clip-path="url(#zr0-clip-9)" width="10" height="10" x="0" y="0" fill="#2563EB"/></g></svg>`;

    const normalized = loaded.module.normalizeEChartsSvg(raw);

    expect(normalized).toContain('id="pa-svg-0"');
    expect(normalized).toContain('id="pa-svg-1"');
    expect(normalized).toContain('clip-path="url(#pa-svg-1)"');
    expect(normalized).toContain('clip-path="url(#pa-svg-0)"');
    expect(normalized).not.toContain("zr0-clip");
  });

  it("rejects unsupported CSS, URLs, elements, namespaces, and broken ID graphs rather than stripping", async () => {
    const loaded = await loadNormalizer();
    expect(loaded.loaded).toBe(true);
    if (!loaded.loaded) return;
    const wrap = (content: string, extraRoot = "") =>
      `<svg width="1200" height="675" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" baseProfile="full" viewBox="0 0 1200 675"${extraRoot}>${content}</svg>`;
    const adversarial = [
      wrap('<rect class="zr0-cls-0" width="1" height="1" x="0" y="0" fill="#2563EB"/><style><![CDATA[.zr0-cls-0:focus {fill:rgba(1,2,3,1);}]]></style>'),
      wrap('<rect class="zr0-cls-0" width="1" height="1" x="0" y="0" fill="#2563EB"/><style><![CDATA[.zr0-cls-0:hover {opacity:0;}]]></style>'),
      wrap('<rect class="zr0-cls-0" width="1" height="1" x="0" y="0" fill="#2563EB"/><style><![CDATA[.zr0-cls-0:hover {fill:red;}]]></style>'),
      wrap('<rect class="zr0-cls-0" width="1" height="1" x="0" y="0" fill="#2563EB"/><style><![CDATA[.zr0-cls-0:hover {cursor:pointer !important;}]]></style>'),
      wrap('<rect class="zr0-cls-0" width="1" height="1" x="0" y="0" fill="#2563EB"/><style><![CDATA[.zr0-cls-0 {fill:#DC2626;}]]></style>'),
      wrap('<text style="font-size:12px" font-size="13" x="0" y="0">x</text>'),
      wrap('<rect width="1" height="1" x="0" y="0" clip-path="url(https://example.invalid/a)"/>'),
      wrap('<rect width="1" height="1" x="0" y="0" clip-path="u\\72l(#zr0-clip-0)"/>'),
      wrap('<script/>'),
      wrap('<evil:rect width="1" height="1"/>', ' xmlns:evil="urn:evil"'),
      wrap('<defs><clipPath id="dup"/><clipPath id="dup"/></defs>'),
      wrap('<rect width="1" height="1" x="0" y="0" clip-path="url(#missing)"/>'),
      wrap('<rect width="1" height="1" x="0" y="0" fill="red"/>'),
      wrap('<text x="0" y="0" font-size="7">x</text>'),
      wrap('<path d="M0 0L1e3 2" fill="#2563EB"/>'),
      wrap('<path d="ML0 0" fill="#2563EB"/>'),
      wrap('<g transform="translate(1000001,0)"/>'),
      wrap('<path d="M0 0L1 1" stroke="#2563EB" stroke-opacity="0.5"/>'),
      wrap('<rect width="1" height="1" x="-0" y="0"/>'),
      wrap('<path d="M0 0L1 1" stroke="#2563EB" stroke-dasharray="1000001,2"/>')
    ];
    for (const raw of adversarial) {
      expect(() => loaded.module.normalizeEChartsSvg(raw), raw).toThrow(/SVG normalization rejected/u);
    }
  });

  it("rejects attributes on the transient style element before removing it", async () => {
    const loaded = await loadNormalizer();
    expect(loaded.loaded).toBe(true);
    if (!loaded.loaded) return;
    const raw = '<svg width="1200" height="675" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" baseProfile="full" viewBox="0 0 1200 675"><style type="text/css"><![CDATA[.zr0-cls-0:hover {pointer-events:none;}]]></style></svg>';

    expect(() => loaded.module.normalizeEChartsSvg(raw)).toThrow(/SVG normalization rejected/u);
  });

  it("rejects comments, processing instructions, DTD/entities, and every CDATA section", async () => {
    const loaded = await loadNormalizer();
    expect(loaded.loaded).toBe(true);
    if (!loaded.loaded) return;
    const forbidden = [
      wrapSvg("<!--comment--><g/>"),
      wrapSvg("<?probe data?><g/>"),
      `<!DOCTYPE svg>${wrapSvg("<g/>")}`,
      `<!DOCTYPE svg [<!ENTITY x "value">]>${wrapSvg("<text x=\"0\" y=\"0\">&x;</text>")}`,
      `<!DOCTYPE svg SYSTEM "https://example.invalid/entity">${wrapSvg("<g/>")}`,
      wrapSvg('<text x="0" y="0"><![CDATA[value]]></text>'),
      wrapSvg('<style><![CDATA[.zr0-cls-0:hover {pointer-events:none;}]]></style>')
    ];

    for (const raw of forbidden) {
      expect(() => loaded.module.normalizeEChartsSvg(raw), raw).toThrow(/SVG normalization rejected/u);
    }
  });

  it("enforces exact depth, text, transform, and point counters", async () => {
    const loaded = await loadNormalizer();
    expect(loaded.loaded).toBe(true);
    if (!loaded.loaded) return;
    const normalize = loaded.module.normalizeEChartsSvg;
    const transforms = (count: number) =>
      Array.from({ length: count }, () => "translate(0)").join(" ");
    const textNodes = (lengths: number[]) => wrapSvg(
      lengths.map((length, index) => `<text x="0" y="${index}">${"a".repeat(length)}</text>`).join("")
    );
    const points = (count: number) => Array.from({ length: count }, () => "0,0").join(" ");

    expect(() => normalize(nestedGroups(64))).not.toThrow();
    expect(() => normalize(nestedGroups(65))).toThrow(/budget/u);
    expect(() => normalize(wrapSvg(`<g transform="${transforms(16)}"/>`))).not.toThrow();
    expect(() => normalize(wrapSvg(`<g transform="${transforms(17)}"/>`))).toThrow(/transform/u);
    expect(() => normalize(textNodes([4096]))).not.toThrow();
    expect(() => normalize(textNodes([4097]))).toThrow(/text/u);
    expect(() => normalize(textNodes([4000, 4000, 4000, 4000, 4000]))).not.toThrow();
    expect(() => normalize(textNodes([4000, 4000, 4000, 4000, 4001]))).toThrow(/text/u);
    expect(() => normalize(wrapSvg(`<polyline points="${points(50_000)}"/>`))).not.toThrow();
    expect(() => normalize(wrapSvg(`<polyline points="${points(50_001)}"/>`))).toThrow(/point/u);
  });

  it("enforces exact node and attribute counters with generated markup", async () => {
    const loaded = await loadNormalizer();
    expect(loaded.loaded).toBe(true);
    if (!loaded.loaded) return;
    const common = '<rect x="0" y="0" width="0" height="0" fill="none"/>';
    const prefix = common.repeat(49_998);
    const exact = wrapSvg(`${prefix}<rect x="0" y="0" width="0"/>`);
    const nodeOver = wrapSvg(`${prefix}<rect x="0" y="0" width="0"/><rect/>`);
    const attributeOver = wrapSvg(`${prefix}<rect x="0" y="0" width="0" height="0"/>`);

    expect(() => loaded.module.normalizeEChartsSvg(exact)).not.toThrow();
    expect(() => loaded.module.normalizeEChartsSvg(nodeOver)).toThrow(/node budget/u);
    expect(() => loaded.module.normalizeEChartsSvg(attributeOver)).toThrow(/attribute budget/u);
  });

  it("enforces exact path byte, aggregate, and command counters", async () => {
    const loaded = await loadNormalizer();
    expect(loaded.loaded).toBe(true);
    if (!loaded.loaded) return;
    const normalize = loaded.module.normalizeEChartsSvg;
    const oneMiB = exactPathBytes(1024 * 1024);
    const commandPath = (lines: number) => `M0 0${"L0 0".repeat(lines)}`;

    expect(() => normalize(wrapSvg(`<path d="${oneMiB}"/>`))).not.toThrow();
    expect(() => normalize(wrapSvg(`<path d="${oneMiB} "/>`))).toThrow(/path/u);
    expect(() => normalize(wrapSvg(Array.from({ length: 4 }, () => `<path d="${oneMiB}"/>`).join("")))).not.toThrow();
    expect(() => normalize(wrapSvg(`${Array.from({ length: 4 }, () => `<path d="${oneMiB}"/>`).join("")}<path d="M0 0"/>`))).toThrow(/path budget/u);
    expect(() => normalize(wrapSvg(`<path d="${commandPath(49_999)}"/>`))).not.toThrow();
    expect(() => normalize(wrapSvg(`<path d="${commandPath(50_000)}"/>`))).toThrow(/path budget/u);
  });

  it("measures the raw SVG limit in UTF-8 bytes rather than UTF-16 code units", async () => {
    const loaded = await loadNormalizer();
    expect(loaded.loaded).toBe(true);
    if (!loaded.loaded) return;
    const shell = wrapSvg('<g data-pad=""/>');
    const prefix = shell.indexOf('"/>');
    const available = 8 * 1024 * 1024 - Buffer.byteLength(shell, "utf8");
    const padding = "界".repeat(Math.floor(available / 3) + 1);
    const raw = `${shell.slice(0, prefix)}${padding}${shell.slice(prefix)}`;
    expect(raw.length).toBeLessThan(8 * 1024 * 1024);
    expect(Buffer.byteLength(raw, "utf8")).toBeGreaterThan(8 * 1024 * 1024);

    expect(() => loaded.module.normalizeEChartsSvg(raw)).toThrow(/UTF-8 byte budget/u);
  });

  it("never rewrites the raw SVG string with regex or string replacement", async () => {
    const source = await readFile(new URL("../src/svg-normalize.ts", import.meta.url), "utf8");

    expect(source).not.toMatch(/rawSvg\.(?:replace|replaceAll|match|matchAll|search|split)\s*\(/u);
  });
});
