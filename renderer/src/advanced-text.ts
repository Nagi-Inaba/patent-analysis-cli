const segmenter = new Intl.Segmenter("ja-JP", { granularity: "grapheme" });

export function truncateAdvancedLabel(value: string, maximum: number): string {
  const result: string[] = [];
  for (const part of segmenter.segment(value)) {
    if (result.length === maximum) return result.slice(0, maximum - 1).join("") + "…";
    result.push(part.segment);
  }
  return result.join("");
}
/** Grapheme count as segmented for display; layout decisions must not split characters. */
export function graphemeLength(value: string): number {
  return [...segmenter.segment(value)].length;
}
/** Display text only: identifiers are never normalized, labels are NFC and bounded. */
export function displayLabel(value: string, maximum: number): string {
  return truncateAdvancedLabel(value.normalize("NFC"), maximum);
}
/** Two-decimal rounding that never yields negative zero, so SVG numbers stay canonical. */
export function fixed(value: number): number {
  return Math.round(value * 100) / 100 || 0;
}
