import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import Ajv2020 from "ajv/dist/2020.js";
import standaloneCode from "ajv/dist/standalone/index.js";

const rendererRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const schemaRoot = resolve(rendererRoot, "..", "src", "patent_analysis", "schemas");
const outputPath = resolve(rendererRoot, "src", "generated", "matrix-standalone-validators.js");

async function readSchema(name) {
  return JSON.parse(await readFile(resolve(schemaRoot, name), "utf8"));
}

function withoutSchemaAnnotation(schema) {
  const compiled = { ...schema };
  delete compiled.$schema;
  return compiled;
}

function inlineAjvRuntime(source) {
  const ucs2Pattern = /const (func[0-9]+) = require\("ajv\/dist\/runtime\/ucs2length"\)\.default;/gu;
  const equalPattern = /const (func[0-9]+) = require\("ajv\/dist\/runtime\/equal"\)\.default;/gu;
  let ucs2Replacements = 0;
  let equalReplacements = 0;
  let inlined = source.replace(ucs2Pattern, (_match, name) => {
    ucs2Replacements += 1;
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
  inlined = inlined.replace(equalPattern, (_match, name) => {
    equalReplacements += 1;
    return `function ${name}(left, right) {
  if (left === right) return true;
  if (
    left === null ||
    right === null ||
    typeof left !== "object" ||
    typeof right !== "object"
  ) return false;
  const leftIsArray = Array.isArray(left);
  if (leftIsArray !== Array.isArray(right)) return false;
  if (leftIsArray) {
    if (left.length !== right.length) return false;
    for (let index = 0; index < left.length; index += 1) {
      if (!${name}(left[index], right[index])) return false;
    }
    return true;
  }
  const leftKeys = Object.keys(left);
  const rightKeys = Object.keys(right);
  if (leftKeys.length !== rightKeys.length) return false;
  for (const key of leftKeys) {
    if (!Object.prototype.hasOwnProperty.call(right, key) || !${name}(left[key], right[key])) {
      return false;
    }
  }
  return true;
}`;
  });
  if (ucs2Replacements !== 1 || equalReplacements > 1) {
    throw new Error(
      `Expected one AJV ucs2 helper and at most one equal helper, received ${ucs2Replacements}/${equalReplacements}`,
    );
  }
  if (/\brequire\s*\(|ajv\/dist|\bFunction\s*\(/u.test(inlined)) {
    throw new Error("Standalone validator source retains a runtime code-generation dependency");
  }
  return inlined;
}

function addSemanticValidators(source) {
  const rawNames = [
    "validateRendererRequestRaw",
    "validateRendererRuntimeRaw",
    "validateMatrixChartModelRaw",
    "validateMatrixRenderSpecRaw"
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
const matrixSegmenter = new Intl.Segmenter("ja-JP", { granularity: "grapheme" });

function matrixGraphemeCount(value) {
  let count = 0;
  for (const _segment of matrixSegmenter.segment(value)) count += 1;
  return count;
}

function matrixSafeText(value) {
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
  if (!validateMatrixChartModelRaw(value)) return false;
  if (!matrixSafeText(value.title)) return false;
  let displayGraphemes = matrixGraphemeCount(value.title);
  const xIds = new Set();
  const yIds = new Set();
  for (let index = 0; index < value.x_axis.categories.length; index += 1) {
    const category = value.x_axis.categories[index];
    if (
      category.index !== index ||
      category.id !== "x:" + index ||
      xIds.has(category.id) ||
      !matrixSafeText(category.label)
    ) return false;
    xIds.add(category.id);
    displayGraphemes += matrixGraphemeCount(category.label);
  }
  for (let index = 0; index < value.y_axis.categories.length; index += 1) {
    const category = value.y_axis.categories[index];
    if (
      category.index !== index ||
      category.id !== "y:" + index ||
      yIds.has(category.id) ||
      !matrixSafeText(category.label)
    ) return false;
    yIds.add(category.id);
    displayGraphemes += matrixGraphemeCount(category.label);
  }
  const pairs = new Set();
  for (const cell of value.cells) {
    if (
      cell.x_index >= value.x_axis.categories.length ||
      cell.y_index >= value.y_axis.categories.length ||
      cell.x_label !== value.x_axis.categories[cell.x_index].label ||
      cell.y_label !== value.y_axis.categories[cell.y_index].label ||
      cell.value !== cell.row_count ||
      cell.row_count > value.population.analyzed_rows
    ) return false;
    const pair = String(cell.y_index) + "\\u0000" + String(cell.x_index);
    if (pairs.has(pair)) return false;
    pairs.add(pair);
  }
  for (const warning of value.warnings) {
    if (!matrixSafeText(warning)) return false;
    displayGraphemes += matrixGraphemeCount(warning);
  }
  if (displayGraphemes > 20_000) return false;
  const population = value.population;
  return population.input_rows === population.analyzed_rows + population.excluded_rows;
}

export function validateRenderSpec(value) {
  return validateMatrixRenderSpecRaw(value);
}
`;
}

export async function generateMatrixStandaloneValidators() {
  const [request, response, chartModel, renderSpec] = await Promise.all([
    readSchema("renderer-request.schema.json"),
    readSchema("matrix-renderer-response.schema.json"),
    readSchema("matrix-chart-model-v1.schema.json"),
    readSchema("matrix-render-spec-v1.schema.json")
  ]);
  const runtime = {
    $id: "urn:patent-analysis:matrix-renderer-runtime:1.0.0",
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
    validateMatrixChartModelRaw: chartModel.$id,
    validateMatrixRenderSpecRaw: renderSpec.$id
  });
  const source = `/* eslint-disable */
/* Generated validators enforce the closed neutral Matrix ChartModel contract. */
${addSemanticValidators(inlineAjvRuntime(generated))}`;
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, source, "utf8");
  return source;
}

if (process.argv[1] !== undefined && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await generateMatrixStandaloneValidators();
}
