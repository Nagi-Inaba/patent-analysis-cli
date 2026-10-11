import { createHash, randomUUID } from "node:crypto";
import { mkdir, readFile, rename, rm, writeFile } from "node:fs/promises";
import { dirname, isAbsolute, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { TextDecoder } from "node:util";
import { gzipSync } from "node:zlib";
import Ajv2020 from "ajv/dist/2020.js";
import standaloneCode from "ajv/dist/standalone/index.js";
import { validateLockData } from "./verify-lock.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const packageRoot = resolve(root, "../src/patent_analysis");
const sha256 = bytes => createHash("sha256").update(bytes).digest("hex");
const assert = (condition, message) => { if (!condition) throw new Error(message); };
const PROFILE = "advanced-svg-ja-jp-node22-echarts6.v1";
const TEMPLATE_SHA256 = "76ae2cf9164a6d7641cd9b44fc45edae818f025c0e7d403d4e198de52c9dbdef";
// Reviewed source support, not the growing Python presentation registry. M10 is JSON-only.
const BUILT_MARKS = Object.freeze([
  "growth-quadrant-svg.v1", "entry-exit-svg.v1", "citation-svg.v1",
  "matrix-composition-svg.v1", "new-entrants-svg.v1", "compara-svg.v1",
  "cooccurrence-svg.v1", "collaboration-network-svg.v1", "uniqueness-svg.v1",
  "shared-involvement-svg.v1", "inventor-tracking-svg.v1",
  "inventor-network-svg.v1", "inventor-ego-network-svg.v1", "inventor-technology-svg.v1",
  "inventor-activity-svg.v1", "inventor-cluster-flow-svg.v1", "inventor-similarity-svg.v1",
  "inventor-impact-svg.v1", "inventor-mobility-svg.v1", "inventor-mobility-flow-svg.v1"
]);
const PACKAGES = Object.freeze({
  "node_modules/@xmldom/xmldom": "0.9.12", "node_modules/echarts": "6.1.0",
  "node_modules/tslib": "2.3.0", "node_modules/zrender": "6.1.0"
});
const SOURCES = new Set([
  "src/advanced-index.ts", "src/advanced-options.ts", "src/advanced-payload.ts", "src/advanced-validation.ts",
  "src/advanced-types.ts", "src/generated/advanced-standalone-validators.js",
  "src/advanced-text.ts", "src/advanced-inventor-frame.ts", "src/advanced-inventor-options.ts",
  "src/advanced-inventor-validation.ts", "src/advanced-inventor-network.ts",
  "src/advanced-inventor-heatmap.ts", "src/advanced-inventor-timeline.ts",
  "src/advanced-inventor-alluvial.ts", "src/advanced-inventor-scatter.ts",
  "src/points-payload.ts", "src/generated/points-standalone-validators.js", "src/categorical-svg-normalize.ts"
]);
function normalizedStrings(source) {
  let text = source.replace(/\\x([0-9A-Fa-f]{2})/gu, (_, hex) => String.fromCodePoint(parseInt(hex, 16)))
    .replace(/\\u\{([0-9A-Fa-f]{1,6})\}/gu, (_, hex) => String.fromCodePoint(parseInt(hex, 16)))
    .replace(/\\u([0-9A-Fa-f]{4})/gu, (_, hex) => String.fromCodePoint(parseInt(hex, 16)));
  for (let pass = 0; pass < 16; pass++) {
    const next = text.replace(/(["'`])\s*\+\s*(["'`])/gu, "");
    if (next === text) return text;
    text = next;
  }
  return text;
}
function validateBundle(bytes) {
  assert(bytes.length > 0 && bytes.length <= 4 * 1024 * 1024, "Advanced bundle size invalid");
  const text = normalizedStrings(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
  for (const pattern of [
    /\bimport\s*\(/u, /\brequire\b/u, /\bmodule\s*(?:\.|\[)/u, /\bprocess\b/u,
    /\bgetBuiltinModule\b/u, /\b(?:stdout|stderr)\b/u, /\b(?:fetch|WebSocket|XMLHttpRequest)\b/u,
    /\b(?:new\s+)?Function\s*\(/u, /\bglobalThis\s*\[\s*["'`]Function["'`]\s*\]/u, /\beval\b/u,
    /(?:\.constructor|\[\s*["'`]constructor["'`]\s*\])\s*(?:\.constructor|\[\s*["'`]constructor["'`]\s*\])/u,
    /["'`]node:[A-Za-z0-9_./-]+/u, /node_modules[\\/]/u
  ]) assert(!pattern.test(text), `Forbidden advanced runtime marker: ${pattern}`);
  let urls = text;
  for (const uri of ["http://www.w3.org/1999/xhtml", "http://www.w3.org/1999/xlink", "http://www.w3.org/2000/svg",
    "http://www.w3.org/XML/1998/namespace", "http://www.w3.org/2000/xmlns/"]) urls = urls.split(uri).join("");
  assert(!/\b(?:https?|wss?):\/\//iu.test(urls), "Runtime network URL is forbidden");
}
function validateGraph(ids, lock) {
  for (const [path, version] of Object.entries(PACKAGES)) assert(lock.packages?.[path]?.version === version, `Unexpected package: ${path}`);
  const seen = new Set(), packages = new Set(), sources = new Set();
  let rolldown = false;
  for (const id of ids) {
    assert(typeof id === "string" && !seen.has(id), "Duplicate or invalid module ID"); seen.add(id);
    if (id === "\0rolldown/runtime.js") { rolldown = true; continue; }
    assert(!id.startsWith("\0") && !id.startsWith("node:") && isAbsolute(id.split("?", 1)[0]), "Unapproved module identity");
    const path = relative(root, id.split("?", 1)[0]).split(sep).join("/");
    if (SOURCES.has(path)) { sources.add(path); continue; }
    const pkg = Object.keys(PACKAGES).find(p => path === p || path.startsWith(p + "/"));
    assert(pkg !== undefined, `Unapproved runtime module: ${path}`); packages.add(pkg);
  }
  assert(rolldown, "Missing pinned Rolldown helper");
  for (const path of Object.keys(PACKAGES)) assert(packages.has(path), `Unreachable approved runtime package: ${path}`);
  for (const path of ["src/advanced-index.ts", "src/advanced-options.ts", "src/advanced-payload.ts", "src/advanced-validation.ts",
    "src/generated/advanced-standalone-validators.js", "src/categorical-svg-normalize.ts",
    "src/advanced-inventor-options.ts", "src/advanced-inventor-validation.ts", "src/advanced-inventor-frame.ts",
    "src/advanced-inventor-network.ts", "src/advanced-inventor-heatmap.ts", "src/advanced-inventor-timeline.ts",
    "src/advanced-inventor-alluvial.ts", "src/advanced-inventor-scatter.ts"]) {
    assert(sources.has(path), `Unreachable approved renderer source: ${path}`);
  }
}
function replaceOnce(text, before, after) {
  assert(text.split(before).length === 2, `Expected one exact bootstrap anchor: ${before}`);
  return text.replace(before, after);
}
function parseArguments(args) {
  const seen = new Set();
  let destination = packageRoot;
  for (let index = 0; index < args.length; index++) {
    const argument = args[index];
    assert(argument === "--stage-only" || argument === "--output-root", `Unknown advanced build argument: ${argument}`);
    assert(!seen.has(argument), "Duplicate advanced build argument"); seen.add(argument);
    if (argument === "--output-root") {
      const value = args[++index];
      assert(typeof value === "string" && isAbsolute(value), "Output root requires an absolute directory");
      destination = resolve(value);
      const path = relative(resolve(root, ".."), destination);
      assert(path !== "" && (path === ".." || path.startsWith(`..${sep}`) || isAbsolute(path)),
        "Explicit output root must be outside the checkout");
    }
  }
  return { stageOnly: seen.has("--stage-only"), destination };
}
async function advancedValidatorsSource() {
  // Generate in memory: isolated builds must not rewrite even generated TS assets.
  const schemaBytes = new Map();
  const read = async name => {
    const raw = await readFile(resolve(packageRoot, "schemas", name));
    assert(raw.length <= 16 * 1024, "Renderer schema size invalid");
    schemaBytes.set(name, raw);
    return JSON.parse(raw.toString("utf8"));
  };
  const [request, response, model, spec] = await Promise.all([
    read("renderer-request.schema.json"), read("advanced-renderer-response.schema.json"),
    read("advanced-chart-model-v1.schema.json"), read("advanced-render-spec-v1.schema.json")
  ]);
  const schemaMarks = model.anyOf.map(branch => branch.properties.mark.const);
  assert(schemaMarks.length === BUILT_MARKS.length && new Set(schemaMarks).size === schemaMarks.length &&
    BUILT_MARKS.every(mark => schemaMarks.includes(mark)), "Closed validator mark inventory changed; review required");
  const options = await readFile(resolve(root, "src/advanced-inventor-options.ts"), "utf8");
  const supported = options.match(/SUPPORTED_INVENTOR_MARKS[^=]*= Object\.freeze\(\[([^\]]+)\]\)/u);
  const inventorMarks = supported?.[1].match(/"[a-z-]+-svg\.v1"/gu)?.map(value => JSON.parse(value));
  assert(inventorMarks?.length === 9 && new Set(inventorMarks).size === 9 &&
    BUILT_MARKS.slice(11).every(mark => inventorMarks.includes(mark)),
    "Inventor source mark inventory changed; review required");
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
  assert(replacements === 1 && !/\brequire\s*\(|ajv\/dist|\bFunction\s*\(/u.test(source),
    "Unexpected AJV standalone runtime dependency");
  return { validators: `/* eslint-disable */\n/* Generated closed advanced SVG validators. */\n${source}`, schemaBytes };
}
export async function buildAdvancedBundle(args = []) {
  const { stageOnly, destination } = parseArguments(args);
  const outputRoot = resolve(destination, "renderer");
  assert(process.version === "v22.19.0" && process.arch === "x64", "Requires Node 22.19.0 x64");
  const { build } = await import("vite");
  const [pkg, lock, template] = await Promise.all([
    readFile(resolve(root, "package.json"), "utf8").then(JSON.parse),
    readFile(resolve(root, "package-lock.json"), "utf8").then(JSON.parse),
    readFile(resolve(root, "src/points-bootstrap.ts"))
  ]);
  validateLockData(pkg, lock);
  assert(sha256(template) === TEMPLATE_SHA256, "Trusted bootstrap template changed; review required");
  const { validators, schemaBytes } = await advancedValidatorsSource();
  const validatorsPath = resolve(root, "src/generated/advanced-standalone-validators.js");
  const built = await build({ root, configFile: resolve(root, "vite.advanced.config.ts"), logLevel: "error",
    plugins: [{ name: "closed-advanced-validators", enforce: "pre",
      load(id) { return resolve(id.split("?", 1)[0]) === validatorsPath ? validators : null; }
    }]
  });
  const outputs = Array.isArray(built) ? built.flatMap(item => item.output) : built.output;
  assert(outputs.length === 1 && outputs[0].type === "chunk" && outputs[0].fileName === "advanced-renderer.bundle.js", "Expected one self-contained advanced chunk");
  const chunk = outputs[0];
  validateGraph(Object.keys(chunk.modules), lock);
  const bundle = Buffer.from(chunk.code, "utf8"); validateBundle(bundle);
  // Standard gzip at rest reduces distribution size. VM input stays the exact
  // verified JavaScript bundle; mtime and OS header bytes are platform-neutral.
  const archive = gzipSync(bundle, { level: 9 });
  archive.fill(0, 4, 8); archive[9] = 255;
  let bootstrapText = template.toString("utf8");
  for (const [before, after] of [
    ["__RENDERER_BUNDLE_SHA256__", sha256(bundle)],
    ["points-svg-ja-jp-node22-echarts6.v1", PROFILE],
    ["patent-analysis-points-renderer", "patent-analysis-advanced-renderer"],
    ["points-renderer.bundle.js", "advanced-renderer.bundle.js"]
  ]) bootstrapText = replaceOnce(bootstrapText, before, after);
  const bootstrap = Buffer.from(bootstrapText, "utf8");
  assert(bootstrap.length <= 64 * 1024, "Bootstrap size invalid");
  const manifest = {
    bootstrap_sha256: sha256(bootstrap), build_tool_id: "patent-analysis.renderer-bundler", build_tool_version: "1.0.0",
    echarts_version: "6.1.0", renderer_build_manifest_version: "1.0.0", renderer_bundle_sha256: sha256(bundle), renderer_protocol_version: "1.0.0"
  };
  const manifestBytes = Buffer.from(JSON.stringify(manifest, null, 2) + "\n");
  const pins = { archive_sha256: sha256(archive), manifest_sha256: sha256(manifestBytes), bootstrap_sha256: sha256(bootstrap), bundle_sha256: sha256(bundle),
    build_digest: sha256(JSON.stringify(manifest)), built_marks: [...BUILT_MARKS] };
  for (const name of ["advanced-chart-model-v1.schema.json", "advanced-render-spec-v1.schema.json", "advanced-renderer-response.schema.json"]) {
    pins[name] = sha256(schemaBytes.get(name));
  }
  const verifySchemas = async () => Promise.all([...schemaBytes].map(async ([name, expected]) => {
    assert((await readFile(resolve(packageRoot, "schemas", name))).equals(expected),
      `Advanced schema changed during build: ${name}`);
  }));
  await verifySchemas();
  await mkdir(outputRoot, { recursive: true });
  await Promise.all([
    writeFile(resolve(outputRoot, "advanced-renderer.bundle.js.gz"), archive),
    writeFile(resolve(outputRoot, "advanced-bootstrap.js"), bootstrap),
    writeFile(resolve(outputRoot, "advanced-renderer-build-manifest.json"), manifestBytes)
  ]);
  const candidatePins = { ...pins, candidate_pin_version: "1.0.0", render_profile_id: PROFILE };
  const candidateBytes = Buffer.from(JSON.stringify(candidatePins, null, 2) + "\n");
  await writeFile(resolve(outputRoot, "advanced-renderer-candidate-pins.json"), candidateBytes);
  // Successful writes alone are not verification: re-read every publication output.
  const verifyOutputs = async () => Promise.all([
    ["advanced-renderer.bundle.js.gz", archive], ["advanced-bootstrap.js", bootstrap],
    ["advanced-renderer-build-manifest.json", manifestBytes],
    ["advanced-renderer-candidate-pins.json", candidateBytes]
  ].map(async ([name, expected]) => {
    const actual = await readFile(resolve(outputRoot, name));
    assert(actual.equals(expected), `Advanced output verification failed: ${name}`);
  }));
  await verifyOutputs();
  if (stageOnly) {
    console.log(`advanced renderer staged: ${bundle.length} bytes; ${pins.build_digest}`);
    return pins;
  }
  // Keep generated Python within the same line budget as hand-authored code.
  const pythonPins = "{\n" + Object.entries(pins).map(([key, value]) => {
    const prefix = `    ${JSON.stringify(key)}: `;
    if (Array.isArray(value)) return prefix + "[\n" + value.map(mark => `        ${JSON.stringify(mark)},`).join("\n") + "\n    ],";
    const literal = JSON.stringify(value);
    return (prefix + literal + ",").length <= 100
      ? prefix + literal + ","
      : prefix + "(\n        " + literal + "\n    ),";
  }).join("\n") + "\n}";
  // Verify a sibling temporary record before the final atomic activation rename.
  const activationPath = resolve(destination, "advanced_renderer_build.py");
  const pendingPath = `${activationPath}.${randomUUID()}.tmp`;
  const activation = Buffer.from(
    '"""Generated by the pinned advanced renderer build; review alongside its assets."""\n' +
    'from __future__ import annotations\n\nADVANCED_BUILD: dict[str, str | list[str]] | None = ' + pythonPins + '\n', "utf8");
  try {
    await writeFile(pendingPath, activation, { flag: "wx" });
    assert((await readFile(pendingPath)).equals(activation), "Advanced activation verification failed");
    await Promise.all([verifyOutputs(), verifySchemas()]);
    await rename(pendingPath, activationPath);
  } finally {
    await rm(pendingPath, { force: true });
  }
  console.log(`advanced renderer built: ${bundle.length} bytes; ${pins.build_digest}`);
  return pins;
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await buildAdvancedBundle(process.argv.slice(2));
}
