import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import Ajv2020 from "ajv/dist/2020.js";
import standaloneCode from "ajv/dist/standalone/index.js";

const rendererRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const schemaRoot = resolve(rendererRoot, "..", "src", "patent_analysis", "schemas");
const outputPath = resolve(rendererRoot, "src", "generated", "standalone-validators.js");

async function readSchema(name) {
  return JSON.parse(await readFile(resolve(schemaRoot, name), "utf8"));
}

function withoutSchemaAnnotation(schema) {
  const compiled = { ...schema };
  delete compiled.$schema;
  return compiled;
}

function inlineAjvRuntime(source) {
  const runtimePattern = /const (func[0-9]+) = require\("ajv\/dist\/runtime\/ucs2length"\)\.default;/gu;
  let replacements = 0;
  const inlined = source.replace(runtimePattern, (_match, name) => {
    replacements += 1;
    return `function ${name}(value) {
  let length = 0;
  for (let index = 0; index < value.length; index += 1) {
    length += 1;
    const unit = value.charCodeAt(index);
    if (unit >= 0xD800 && unit <= 0xDBFF && index + 1 < value.length) {
      const next = value.charCodeAt(index + 1);
      if ((next & 0xFC00) === 0xDC00) index += 1;
    }
  }
  return length;
}`;
  });
  if (replacements !== 1) throw new Error(`Expected one AJV runtime helper, received ${replacements}`);
  if (/\brequire\s*\(|ajv\/dist|\bFunction\s*\(/u.test(inlined)) {
    throw new Error("Standalone validator source retains a runtime code-generation dependency");
  }
  return inlined;
}

function addSemanticValidators(source) {
  const rawNames = [
    "validateRendererRequestRaw",
    "validateRendererRuntimeRaw",
    "validateChartModelRaw",
    "validateRenderSpecRaw"
  ];
  let internal = source;
  for (const name of rawNames) {
    const declaration = `export const ${name} =`;
    if (internal.split(declaration).length !== 2) {
      throw new Error(`Expected one generated export for ${name}`);
    }
    internal = internal.replace(declaration, `const ${name} =`);
  }
  return `${internal}
const chartSegmenter = new Intl.Segmenter("ja-JP", { granularity: "grapheme" });
const chartTitleSuffix = "のランキング";

function chartGraphemes(value) {
  return Array.from(chartSegmenter.segment(value), ({ segment }) => segment);
}

function chartGraphemeCount(value) {
  let count = 0;
  for (const _segment of chartSegmenter.segment(value)) count += 1;
  return count;
}

function chartGraphemeRange(value, minimum, maximum) {
  const count = chartGraphemeCount(value);
  return count >= minimum && count <= maximum;
}

function chartExpectedTitle(displayLabel) {
  const clusters = chartGraphemes(displayLabel);
  return clusters.length + chartGraphemeCount(chartTitleSuffix) <= 256
    ? displayLabel + chartTitleSuffix
    : clusters.slice(0, 249).join("") + "…" + chartTitleSuffix;
}

function chartSafeText(value) {
  if (value.normalize("NFC") !== value) return false;
  for (const character of value) {
    const codePoint = character.codePointAt(0);
    if (
      codePoint <= 0x1F ||
      (codePoint >= 0x7F && codePoint <= 0x9F) ||
      (codePoint >= 0xD800 && codePoint <= 0xDFFF) ||
      (codePoint >= 0xFDD0 && codePoint <= 0xFDEF) ||
      (codePoint & 0xFFFF) === 0xFFFE ||
      (codePoint & 0xFFFF) === 0xFFFF ||
      (codePoint >= 0x202A && codePoint <= 0x202E) ||
      (codePoint >= 0x2066 && codePoint <= 0x2069)
    ) return false;
  }
  return true;
}

export function validateRendererRequest(value) {
  return validateRendererRequestRaw(value);
}

export function validateRendererRuntime(value) {
  return validateRendererRuntimeRaw(value);
}

export function validateChartModel(value) {
  if (!validateChartModelRaw(value)) return false;
  if (
    !chartGraphemeRange(value.title, 1, 256) ||
    !chartGraphemeRange(value.dimension.source_label, 1, 256) ||
    !chartGraphemeRange(value.dimension.display_label, 1, 256) ||
    (value.dimension.description !== null && !chartGraphemeRange(value.dimension.description, 0, 256)) ||
    (value.measure.column !== null && !chartGraphemeRange(value.measure.column, 1, 256)) ||
    value.title !== chartExpectedTitle(value.dimension.display_label)
  ) return false;
  const rows = value.rows;
  const analyzedRows = value.population.analyzed_rows;
  let countTotal = 0;
  let sawRemainder = false;
  for (let index = 0; index < rows.length; index += 1) {
    const row = rows[index];
    if (
      row.index !== index ||
      row.count > analyzedRows ||
      !chartGraphemeRange(row.display_label, 1, 256) ||
      (row.description !== null && !chartGraphemeRange(row.description, 0, 256))
    ) return false;
    countTotal += row.count;
    if (row.row_kind === "dimension_value") {
      if (row.semantic_label !== "データ中の分類値") return false;
    } else {
      if (
        sawRemainder ||
        index !== rows.length - 1 ||
        row.source_label !== "その他" ||
        row.semantic_label !== "上位表示外の合計"
      ) return false;
      sawRemainder = true;
    }
  }
  if (countTotal > analyzedRows) return false;
  if ((analyzedRows === 0) !== (rows.length === 0)) return false;
  const displayTexts = [
    value.title,
    value.dimension.source_label,
    value.dimension.display_label
  ];
  if (value.dimension.description !== null) displayTexts.push(value.dimension.description);
  if (value.measure.column !== null) displayTexts.push(value.measure.column);
  for (const row of rows) {
    displayTexts.push(row.source_label, row.display_label, row.semantic_label);
    if (row.description !== null) displayTexts.push(row.description);
  }
  displayTexts.push(...value.warnings);
  let displayGraphemes = 0;
  for (const text of displayTexts) {
    if (!chartSafeText(text)) return false;
    displayGraphemes += chartGraphemeCount(text);
    if (displayGraphemes > 20_000) return false;
  }
  return true;
}

export function validateRenderSpec(value) {
  if (!validateRenderSpecRaw(value)) return false;
  if (value.height === 675) return true;
  const rowCount = (value.height - 160) / 36;
  return Number.isInteger(rowCount) && rowCount >= 15 && rowCount <= 101;
}
`;
}

export async function generateStandaloneValidators() {
  const [request, response, chartModel, renderSpec] = await Promise.all([
    readSchema("renderer-request.schema.json"),
    readSchema("renderer-response.schema.json"),
    readSchema("chart-model.schema.json"),
    readSchema("render-spec.schema.json")
  ]);
  const runtime = {
    $id: "urn:patent-analysis:renderer-runtime:1.0.0",
    ...response.$defs.runtime
  };
  const compiledRequest = withoutSchemaAnnotation(request);
  const compiledChartModel = withoutSchemaAnnotation(chartModel);
  const compiledRenderSpec = withoutSchemaAnnotation(renderSpec);
  const ajv = new Ajv2020({
    strict: true,
    allErrors: false,
    code: { source: true, esm: true, lines: true }
  });
  for (const schema of [compiledRequest, runtime, compiledChartModel, compiledRenderSpec]) {
    ajv.addSchema(schema);
  }
  const generated = standaloneCode(ajv, {
    validateRendererRequestRaw: request.$id,
    validateRendererRuntimeRaw: runtime.$id,
    validateChartModelRaw: chartModel.$id,
    validateRenderSpecRaw: renderSpec.$id
  });
  const source = `/* eslint-disable */
/*
 * Generated validators enforce authoritative Python ChartModel semantics.
 * The renderer-only NFC restriction is an explicit policy divergence:
 * Python accepts exactly derived NFD models, while SVG rendering rejects them without normalization.
 */
${addSemanticValidators(inlineAjvRuntime(generated))}`;
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, source, "utf8");
  return source;
}

if (process.argv[1] !== undefined && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await generateStandaloneValidators();
}
