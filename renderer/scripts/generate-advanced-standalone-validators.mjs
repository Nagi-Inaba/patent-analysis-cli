import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import Ajv2020 from "ajv/dist/2020.js";
import standaloneCode from "ajv/dist/standalone/index.js";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const schemas = resolve(root, "../src/patent_analysis/schemas");
const read = async name => JSON.parse(await readFile(resolve(schemas, name), "utf8"));

export async function generateAdvancedStandaloneValidators() {
  const [request, response, model, spec] = await Promise.all([
    read("renderer-request.schema.json"), read("advanced-renderer-response.schema.json"),
    read("advanced-chart-model-v1.schema.json"), read("advanced-render-spec-v1.schema.json")
  ]);
  const runtime = { $id: "urn:patent-analysis:advanced-runtime:1.0.0", ...response.$defs.runtime };
  const ajv = new Ajv2020({ strict: true, allErrors: false, code: { source: true, esm: true, lines: true } });
  for (const schema of [request, runtime, model, spec]) {
    const copied = { ...schema }; delete copied.$schema; ajv.addSchema(copied);
  }
  let source = standaloneCode(ajv, {
    validateRequestRaw: request.$id, validateRuntimeRaw: runtime.$id,
    validateModelRaw: model.$id, validateSpecRaw: spec.$id
  });
  let replacements = 0;
  source = source.replace(/const (func[0-9]+) = require\("ajv\/dist\/runtime\/ucs2length"\)\.default;/gu, (_, name) => {
    replacements++;
    return `function ${name}(value) {
  let length = 0;
  for (let index = 0; index < value.length; index++) {
    length++;
    const unit = value.charCodeAt(index);
    if (unit >= 0xD800 && unit <= 0xDBFF && index + 1 < value.length &&
        (value.charCodeAt(index + 1) & 0xFC00) === 0xDC00) index++;
  }
  return length;
}`;
  });
  if (replacements !== 1 || /\brequire\s*\(|ajv\/dist|\bFunction\s*\(/u.test(source)) {
    throw new Error("Unexpected AJV standalone runtime dependency");
  }
  const output = resolve(root, "src/generated/advanced-standalone-validators.js");
  await mkdir(dirname(output), { recursive: true });
  await writeFile(output, `/* eslint-disable */\n/* Generated closed advanced SVG validators. */\n${source}`, "utf8");
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await generateAdvancedStandaloneValidators();
}
