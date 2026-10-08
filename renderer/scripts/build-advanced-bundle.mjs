import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, isAbsolute, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { TextDecoder } from "node:util";
import { build } from "vite";
import { gzipSync } from "node:zlib";
import { validateLockData } from "./verify-lock.mjs";
import { generateAdvancedStandaloneValidators } from "./generate-advanced-standalone-validators.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const packageRoot = resolve(root, "../src/patent_analysis");
const outputRoot = resolve(packageRoot, "renderer");
const sha256 = bytes => createHash("sha256").update(bytes).digest("hex");
const assert = (condition, message) => { if (!condition) throw new Error(message); };
const PROFILE = "advanced-svg-ja-jp-node22-echarts6.v1";
const TEMPLATE_SHA256 = "76ae2cf9164a6d7641cd9b44fc45edae818f025c0e7d403d4e198de52c9dbdef";
const PACKAGES = Object.freeze({
  "node_modules/@xmldom/xmldom": "0.9.12", "node_modules/echarts": "6.1.0",
  "node_modules/tslib": "2.3.0", "node_modules/zrender": "6.1.0"
});
const SOURCES = new Set([
  "src/advanced-index.ts", "src/advanced-options.ts", "src/advanced-payload.ts", "src/advanced-validation.ts",
  "src/advanced-types.ts", "src/generated/advanced-standalone-validators.js",
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
    "src/generated/advanced-standalone-validators.js", "src/categorical-svg-normalize.ts"]) {
    assert(sources.has(path), `Unreachable approved renderer source: ${path}`);
  }
}
function replaceOnce(text, before, after) {
  assert(text.split(before).length === 2, `Expected one exact bootstrap anchor: ${before}`);
  return text.replace(before, after);
}
function parseArguments(args) {
  for (const argument of args) assert(argument === "--stage-only", `Unknown advanced build argument: ${argument}`);
  assert(new Set(args).size === args.length, "Duplicate advanced build argument");
  return { stageOnly: args.includes("--stage-only") };
}
export async function buildAdvancedBundle(args = []) {
  const { stageOnly } = parseArguments(args);
  assert(process.version === "v22.19.0" && process.arch === "x64", "Requires Node 22.19.0 x64");
  const [pkg, lock, template] = await Promise.all([
    readFile(resolve(root, "package.json"), "utf8").then(JSON.parse),
    readFile(resolve(root, "package-lock.json"), "utf8").then(JSON.parse),
    readFile(resolve(root, "src/points-bootstrap.ts"))
  ]);
  validateLockData(pkg, lock);
  assert(sha256(template) === TEMPLATE_SHA256, "Trusted bootstrap template changed; review required");
  await generateAdvancedStandaloneValidators();
  const built = await build({ root, configFile: resolve(root, "vite.advanced.config.ts"), logLevel: "error" });
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
    build_digest: sha256(JSON.stringify(manifest)) };
  for (const name of ["advanced-chart-model-v1.schema.json", "advanced-render-spec-v1.schema.json", "advanced-renderer-response.schema.json"]) {
    const raw = await readFile(resolve(packageRoot, "schemas", name));
    assert(raw.length <= 16 * 1024, "Renderer schema size invalid"); pins[name] = sha256(raw);
  }
  await mkdir(outputRoot, { recursive: true });
  await Promise.all([
    writeFile(resolve(outputRoot, "advanced-renderer.bundle.js.gz"), archive),
    writeFile(resolve(outputRoot, "advanced-bootstrap.js"), bootstrap),
    writeFile(resolve(outputRoot, "advanced-renderer-build-manifest.json"), manifestBytes)
  ]);
  if (stageOnly) {
    const candidatePins = { ...pins, candidate_pin_version: "1.0.0", render_profile_id: PROFILE };
    await writeFile(resolve(outputRoot, "advanced-renderer-candidate-pins.json"),
      Buffer.from(JSON.stringify(candidatePins, null, 2) + "\n"));
    console.log(`advanced renderer staged: ${bundle.length} bytes; ${pins.build_digest}`);
    return pins;
  }
  // Keep generated Python within the same line budget as hand-authored code.
  const pythonPins = "{\n" + Object.entries(pins).map(([key, value]) => {
    const prefix = `    ${JSON.stringify(key)}: `;
    const literal = JSON.stringify(value);
    return (prefix + literal + ",").length <= 100
      ? prefix + literal + ","
      : prefix + "(\n        " + literal + "\n    ),";
  }).join("\n") + "\n}";
  // Activation is the last write. Missing or interrupted builds remain fail-closed.
  await writeFile(resolve(packageRoot, "advanced_renderer_build.py"),
    '"""Generated by the pinned advanced renderer build; review alongside its assets."""\n' +
    'from __future__ import annotations\n\nADVANCED_BUILD: dict[str, str] | None = ' + pythonPins + '\n', "utf8");
  console.log(`advanced renderer built: ${bundle.length} bytes; ${pins.build_digest}`);
  return pins;
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await buildAdvancedBundle(process.argv.slice(2));
}
