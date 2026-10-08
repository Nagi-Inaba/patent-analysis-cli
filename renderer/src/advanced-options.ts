import type { AdvancedModel, AdvancedProjection, AdvancedSpec } from "./advanced-types.js";

const TEXT = "#0f172a";
const MUTED = "#475569";
const GRID = "#cbd5e1";
const TEAL = "#0f766e";
const PALETTE: Readonly<Record<string, string>> = Object.freeze({
  active: TEAL, inactive: "#94a3b8", citation: TEAL,
  sustained_growth: TEAL, recovery: "#2563eb", slowing: "#a16207", decline: "#b45309"
});
const segmenter = new Intl.Segmenter("ja-JP", { granularity: "grapheme" });

export function truncateAdvancedLabel(value: string, maximum: number): string {
  const result: string[] = [];
  for (const part of segmenter.segment(value)) {
    if (result.length === maximum) return result.slice(0, maximum - 1).join("") + "…";
    result.push(part.segment);
  }
  return result.join("");
}
function number(value: number): string {
  return value.toLocaleString("ja-JP", { maximumFractionDigits: 2 });
}
function symbolSize(value: number, maximum: number): number {
  // Fixed minimum makes zero-valued citation records visible without changing data.
  return maximum <= 0 ? 12 : 12 + 24 * Math.sqrt(Math.max(0, value) / maximum);
}
function empty(p: AdvancedProjection): boolean {
  switch (p.kind) {
    case "scatter": case "quadrant": return p.points.length === 0;
    case "heatmap": return p.x.length === 0 || p.y.length === 0;
    case "bars": return p.items.length === 0;
    case "network": case "tracking": return p.nodes.length === 0;
  }
}
function axis(label: string, spec: AdvancedSpec, year: boolean): Record<string, unknown> {
  return {
    type: "value", name: label, scale: year,
    ...(year ? { minInterval: 1 } : {}),
    axisLabel: { color: TEXT, fontFamily: spec.font_family },
    axisLine: { lineStyle: { color: MUTED } },
    splitLine: { lineStyle: { color: GRID } }
  };
}

export function buildAdvancedOption(model: AdvancedModel, spec: AdvancedSpec): Record<string, unknown> {
  const p = model.projection;
  const omitted = p.kind === "quadrant" && p.unplottable.length > 0
    ? `増減率未定義: 座標表示対象外 ${p.unplottable.length} 件 (${p.unplottable.slice(0, 3).map(v => truncateAdvancedLabel(v.label, 12)).join("、")}${p.unplottable.length > 3 ? " ほか" : ""})` : "";
  const population = `入力 ${model.population.input_rows} / 分析 ${model.population.analyzed_rows} / 除外 ${model.population.excluded_rows}`;
  const note = [empty(p) ? "対象データなし" : "", omitted, truncateAdvancedLabel(p.context, 80), population,
    model.warnings.length ? `注意 ${model.warnings.length}件: ${truncateAdvancedLabel(model.warnings[0]!, 80)}` : ""].filter(Boolean).join("\n");
  const option: Record<string, unknown> = {
    animation: false, backgroundColor: "#ffffff",
    textStyle: { fontFamily: spec.font_family, color: TEXT },
    title: { text: model.title, subtext: note, left: "center", top: 12,
      textStyle: { fontFamily: spec.font_family, fontSize: 22, fontWeight: 600, color: TEXT },
      subtextStyle: { fontFamily: spec.font_family, fontSize: 12, lineHeight: 18, color: MUTED } },
    grid: { left: 120, right: 110, top: 158, bottom: 90, containLabel: true },
    series: []
  };
  if (p.kind === "scatter" || p.kind === "quadrant") {
    const maximum = Math.max(0, ...p.points.map(v => v.size));
    option.xAxis = axis(p.x_label, spec, p.kind === "scatter" && p.x_year);
    option.yAxis = axis(p.y_label, spec, p.kind === "scatter" && p.y_year);
    const data = p.points.map(point => ({
      id: point.id, name: point.label, value: [point.x, point.y, point.size],
      symbolSize: symbolSize(point.size, maximum),
      itemStyle: { color: PALETTE[point.category] ?? TEAL, opacity: 0.82 },
      label: { show: true, position: "top", color: TEXT, fontSize: 11,
        fontFamily: spec.font_family,
        formatter: () => truncateAdvancedLabel(point.label, spec.axis_label_max_graphemes) }
    }));
    option.series = [{ type: "scatter", data, animation: false, emphasis: { disabled: true },
      ...(p.kind === "quadrant" ? { markLine: { silent: true, symbol: "none",
        label: { show: false }, lineStyle: { color: MUTED, type: "dashed" },
        data: [{ xAxis: 0 }, { yAxis: 0 }] } } : {}) }];
  } else if (p.kind === "heatmap") {
    const values = new Map(p.cells.map(c => [`${c.x}:${c.y}`, c.value]));
    const data = p.y.flatMap((_, y) => p.x.map((__, x) => [x, y, values.get(`${x}:${y}`) ?? 0]));
    const maximum = Math.max(1, ...p.cells.map(c => Math.abs(c.value)));
    const categories = (labels: string[]) => ({
      type: "category", data: labels, axisTick: { show: false },
      axisLabel: { color: TEXT, fontFamily: spec.font_family,
        formatter: (value: string) => truncateAdvancedLabel(value, 14) }
    });
    option.xAxis = { ...categories(p.x), name: p.x_label, axisLabel: {
      color: TEXT, fontFamily: spec.font_family, rotate: 25,
      formatter: (value: string) => truncateAdvancedLabel(value, 12) } };
    option.yAxis = { ...categories(p.y), inverse: true, name: p.y_label };
    option.visualMap = { type: "piecewise", min: p.signed ? -maximum : 0, max: maximum,
      splitNumber: 5, calculable: false,
      orient: "horizontal", left: "center", bottom: 10, precision: 0,
      text: p.signed ? ["A優位", "B優位"] : ["多", "少"],
      inRange: { color: p.signed ? ["#2563eb", "#f8fafc", "#b45309"] : ["#f0fdfa", "#5eead4", TEAL] } };
    option.series = [{ type: "heatmap", data, animation: false,
      itemStyle: { borderColor: "#ffffff", borderWidth: 1 }, emphasis: { disabled: true },
      label: { show: true, fontSize: 10, fontFamily: spec.font_family, color: TEXT,
        formatter: (params: { value: number[] }) => number(params.value[2]!) } }];
  } else if (p.kind === "bars") {
    option.grid = { left: 180, right: 300, top: 158, bottom: 55, containLabel: true };
    option.xAxis = axis(p.value_label, spec, false);
    option.yAxis = { type: "category", inverse: true, data: p.items.map(v => v.label),
      axisLabel: { color: TEXT, fontFamily: spec.font_family,
        formatter: (value: string) => truncateAdvancedLabel(value, 18) } };
    option.series = [{ type: "bar", animation: false, emphasis: { disabled: true },
      data: p.items.map(item => ({ value: item.value, name: item.label, itemStyle: { color: TEAL },
        label: { show: true, position: "right", color: TEXT, fontFamily: spec.font_family, fontSize: 11,
          formatter: () => `${number(item.value)} / ${number(item.denominator)} (${number(item.share * 100)}%)` +
            (item.involvement_count === null ? "" : ` 関与 ${number(item.involvement_count)}件`) } })) }];
  } else if (p.kind === "tracking") {
    const colors = ["#0f766e", "#2563eb", "#b45309", "#7e22ce", "#be123c", "#0369a1",
      "#4d7c0f", "#a21caf", "#c2410c", "#475569"];
    option.grid = { left: 150, right: 75, top: 165, bottom: 55, containLabel: true };
    option.xAxis = { type: "category", data: p.years.map(String), position: "top",
      axisLabel: { color: TEXT, fontFamily: spec.font_family },
      splitLine: { show: true, lineStyle: { color: GRID, type: "dotted" } } };
    option.yAxis = { type: "category", data: p.inventors, inverse: true,
      axisLabel: { color: TEXT, fontFamily: spec.font_family,
        formatter: (value: string) => truncateAdvancedLabel(value, 16) },
      splitLine: { show: true, lineStyle: { color: "#e2e8f0" } } };
    const labelLimit = p.years.length > 8 ? 7 : p.years.length > 5 ? 11 : 20;
    option.series = [
      ...p.links.map(link => ({ type: "scatter", data: [], animation: false,
        markLine: { silent: true, symbol: "none", label: { show: false },
          lineStyle: { color: "#94a3b8", width: 2, type: link.gap ? "dashed" : "solid" },
          data: [[{ coord: [p.nodes[link.source]!.x, p.nodes[link.source]!.y] },
            { coord: [p.nodes[link.target]!.x, p.nodes[link.target]!.y] }]] } })),
      { type: "scatter", animation: false, emphasis: { disabled: true },
        data: p.nodes.map(node => ({ value: [node.x, node.y], symbolSize: 10,
          symbol: node.unknown ? "emptyCircle" : node.changed ? "diamond" : "circle",
          itemStyle: { color: colors[node.cluster % colors.length], opacity: 1 },
          label: { show: true, position: "bottom", distance: 2, color: TEXT, fontSize: 10,
            fontFamily: spec.font_family,
            formatter: () => truncateAdvancedLabel(`C${node.cluster + 1} ${node.applicants || "不明"}`, labelLimit) }
        })) }
    ];
  } else {
    const maximum = Math.max(1, ...p.nodes.map(n => n.value));
    const maxLink = Math.max(1, ...p.edges.map(e => e.value));
    const nodes = p.nodes.map((node, index) => {
        const angle = 2 * Math.PI * index / Math.max(1, p.nodes.length) - Math.PI / 2;
        const x = Math.round(400 * Math.cos(angle) * 1e6) / 1e6;
        const y = Math.round(200 * Math.sin(angle) * 1e6) / 1e6;
        return { id: String(index), name: node.label, sourceValue: node.value,
          value: [x, y, node.value],
          symbolSize: symbolSize(node.value, maximum), itemStyle: { color: TEAL },
          label: { show: true, position: "top", color: TEXT, fontSize: 11,
            fontFamily: spec.font_family,
            textBorderWidth: 0,
            formatter: () => truncateAdvancedLabel(node.label, 18) } };
      });
    option.xAxis = { type: "value", min: -450, max: 450, show: false };
    option.yAxis = { type: "value", min: -250, max: 250, show: false };
    option.series = [
      { type: "scatter", data: nodes, animation: false, emphasis: { disabled: true } },
      ...p.edges.map(edge => ({ type: "scatter", data: [], animation: false,
        markLine: { silent: true, symbol: "none", label: { show: false },
          lineStyle: { width: Math.round((1 + 3 * edge.value / maxLink) * 1e6) / 1e6,
            color: "#94a3b8", opacity: 0.75 },
          data: [[
            { coord: nodes[edge.source]!.value.slice(0, 2) },
            { coord: nodes[edge.target]!.value.slice(0, 2) }
          ]] } }))
    ];
  }
  return option;
}
