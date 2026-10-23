import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, isAbsolute, relative, resolve, sep } from "node:path";
import process from "node:process";
import { TextDecoder } from "node:util";
import { fileURLToPath } from "node:url";
import { build } from "vite";
import { generateMatrixStandaloneValidators } from "./generate-matrix-standalone-validators.mjs";
import { validateLockData } from "./verify-lock.mjs";

const rendererRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const repositoryRoot = resolve(rendererRoot, "..");
const packageOutputRoot = resolve(repositoryRoot, "src", "patent_analysis", "renderer");
const MAX_BUNDLE_BYTES = 4 * 1024 * 1024;
const BOOTSTRAP_PLACEHOLDER = "__RENDERER_BUNDLE_SHA256__";
const EXACT_ROLLDOWN_RUNTIME_ID = "\0rolldown/runtime.js";
const APPROVED_RUNTIME_LOCK_PATHS = Object.freeze({
  "node_modules/@xmldom/xmldom": "0.9.12",
  "node_modules/echarts": "6.1.0",
  "node_modules/tslib": "2.3.0",
  "node_modules/zrender": "6.1.0"
});
const APPROVED_RENDERER_MODULES = Object.freeze([
  "src/generated/matrix-standalone-validators.js",
  "src/matrix-index.ts",
  "src/matrix-payload.ts",
  "src/matrix-pie.ts",
  "src/palette.ts",
  "src/svg-normalize.ts"
]);
const SAFE_NAMESPACE_URIS = Object.freeze([
  "http://www.w3.org/1999/xhtml",
  "http://www.w3.org/1999/xlink",
  "http://www.w3.org/2000/svg",
  "http://www.w3.org/XML/1998/namespace",
  "http://www.w3.org/2000/xmlns/"
]);
const MANIFEST_KEYS = Object.freeze([
  "bootstrap_sha256",
  "build_tool_id",
  "build_tool_version",
  "echarts_version",
  "renderer_build_manifest_version",
  "renderer_bundle_sha256",
  "renderer_protocol_version"
]);

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function sha256(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

function stableJson(value) {
  return `${JSON.stringify(value, null, 2)}\n`;
}

function normalizeComputedStrings(source) {
  let normalized = source
    .replace(/\\x([0-9A-Fa-f]{2})/gu, (_match, hex) => String.fromCodePoint(Number.parseInt(hex, 16)))
    .replace(/\\u\{([0-9A-Fa-f]{1,6})\}/gu, (_match, hex) => String.fromCodePoint(Number.parseInt(hex, 16)))
    .replace(/\\u([0-9A-Fa-f]{4})/gu, (_match, hex) => String.fromCodePoint(Number.parseInt(hex, 16)));
  for (let pass = 0; pass < 16; pass += 1) {
    const folded = normalized.replace(/(["'`])\s*\+\s*(["'`])/gu, "");
    if (folded === normalized) return normalized;
    normalized = folded;
  }
  return normalized;
}

function validateRuntimeBundle(bundle) {
  assert(Buffer.isBuffer(bundle), "Expected renderer bundle bytes");
  assert(bundle.byteLength > 0, "Expected non-empty renderer bundle");
  assert(bundle.byteLength <= MAX_BUNDLE_BYTES, "Renderer bundle exceeds 4 MiB");
  const source = new TextDecoder("utf-8", { fatal: true }).decode(bundle);
  const normalizedSource = normalizeComputedStrings(source);
  let networkScanSource = normalizedSource;
  for (const allowedUri of SAFE_NAMESPACE_URIS) {
    networkScanSource = networkScanSource.split(allowedUri).join("");
  }
  const forbidden = [
    /\bimport\s*\(/u,
    /\brequire\b/u,
    /\bmodule\s*(?:\.|\[)/u,
    /\bprocess\b/u,
    /\bgetBuiltinModule\b/u,
    /\b(?:stdout|stderr)\b/u,
    /\b(?:fetch|WebSocket|XMLHttpRequest)\b/u,
    /\b(?:new\s+)?Function\s*\(/u,
    /\bglobalThis\s*\[\s*["'`]Function["'`]\s*\]/u,
    /\beval\b/u,
    /(?:\.constructor|\[\s*["'`]constructor["'`]\s*\])\s*(?:\.constructor|\[\s*["'`]constructor["'`]\s*\])/u,
    /["'`]node:[A-Za-z0-9_./-]+/u,
    /node_modules[\\/]/u
  ];
  for (const pattern of forbidden) {
    assert(!pattern.test(normalizedSource), `Forbidden runtime marker: ${pattern}`);
  }
  assert(!/\b(?:https?|wss?):\/\//iu.test(networkScanSource), "Forbidden runtime network URL");
}

function normalizeModuleId(root, moduleId) {
  const withoutQuery = moduleId.split("?", 1)[0];
  return relative(root, withoutQuery).split(sep).join("/");
}

function validateModuleGraph({ moduleIds, packageLock }) {
  const approvedLockPaths = Object.keys(APPROVED_RUNTIME_LOCK_PATHS);
  for (const [lockPath, version] of Object.entries(APPROVED_RUNTIME_LOCK_PATHS)) {
    assert(packageLock.packages?.[lockPath]?.version === version, `Unexpected approved runtime package ${lockPath}`);
  }
  const included = new Set();
  const seenRendererModules = new Set();
  const seenModuleIds = new Set();
  let sawRolldownRuntime = false;
  for (const moduleId of moduleIds) {
    assert(typeof moduleId === "string", "Expected string module ID");
    assert(!seenModuleIds.has(moduleId), `Duplicate renderer module ${JSON.stringify(moduleId)}`);
    seenModuleIds.add(moduleId);
    if (moduleId === EXACT_ROLLDOWN_RUNTIME_ID) {
      sawRolldownRuntime = true;
      continue;
    }
    assert(!moduleId.startsWith("\0"), `Unexpected virtual renderer module ${JSON.stringify(moduleId)}`);
    assert(!moduleId.startsWith("node:"), `Unexpected Node builtin renderer module ${moduleId}`);
    assert(isAbsolute(moduleId.split("?", 1)[0]), `Expected absolute renderer module ID ${moduleId}`);
    const relativeId = normalizeModuleId(rendererRoot, moduleId);
    if (APPROVED_RENDERER_MODULES.includes(relativeId)) {
      seenRendererModules.add(relativeId);
      continue;
    }
    const lockPath = approvedLockPaths.find((candidate) =>
      relativeId === candidate || relativeId.startsWith(`${candidate}/`)
    );
    assert(lockPath !== undefined, `Unexpected renderer module ${relativeId}`);
    included.add(lockPath);
  }
  for (const lockPath of approvedLockPaths) {
    assert(included.has(lockPath), `Approved runtime package is unreachable: ${lockPath}`);
  }
  assert(sawRolldownRuntime, "Exact Rolldown runtime helper is unreachable");
  for (const moduleId of APPROVED_RENDERER_MODULES) {
    assert(seenRendererModules.has(moduleId), `Approved renderer entry is unreachable: ${moduleId}`);
  }
}

function validateBuildArtifacts(bootstrap, bundle, manifest) {
  validateRuntimeBundle(bundle);
  assert(Buffer.isBuffer(bootstrap) && bootstrap.byteLength > 0, "Expected bootstrap bytes");
  assert(
    JSON.stringify(Object.keys(manifest).sort()) === JSON.stringify(MANIFEST_KEYS),
    "Expected exact seven-field renderer build manifest"
  );
  assert(manifest.renderer_build_manifest_version === "1.0.0", "Unexpected manifest version");
  assert(manifest.bootstrap_sha256 === sha256(bootstrap), "Bootstrap digest mismatch");
  assert(manifest.renderer_bundle_sha256 === sha256(bundle), "Bundle digest mismatch");
  assert(manifest.renderer_protocol_version === "1.0.0", "Unexpected protocol version");
  assert(manifest.echarts_version === "6.1.0", "Unexpected ECharts version");
  assert(manifest.build_tool_id === "patent-analysis.renderer-bundler", "Unexpected build tool ID");
  assert(manifest.build_tool_version === "1.0.0", "Unexpected build tool version");
}

function chunkFromBuildResult(result) {
  const outputs = Array.isArray(result) ? result.flatMap((item) => item.output) : result.output;
  const chunks = outputs.filter((item) => item.type === "chunk");
  const assets = outputs.filter((item) => item.type === "asset");
  assert(chunks.length === 1, "Expected exactly one renderer chunk");
  assert(assets.length === 0, "Expected no renderer assets");
  assert(chunks[0].fileName === "matrix-renderer.bundle.js", "Unexpected renderer bundle filename");
  return chunks[0];
}

async function main() {
  assert(process.version === "v24.22.1", `Expected Node v24.22.1, received ${process.version}`);
  assert(process.arch === "x64" || (process.platform === "darwin" && process.arch === "arm64"),
    `Expected x64 or macOS arm64 Node, received ${process.platform}/${process.arch}`);
  const [packageJson, packageLock, bootstrapTemplate] = await Promise.all([
    readFile(resolve(rendererRoot, "package.json"), "utf8").then(JSON.parse),
    readFile(resolve(rendererRoot, "package-lock.json"), "utf8").then(JSON.parse),
    readFile(resolve(rendererRoot, "src", "matrix-bootstrap.ts"), "utf8")
  ]);
  validateLockData(packageJson, packageLock);
  await generateMatrixStandaloneValidators();
  const result = await build({
    configFile: resolve(rendererRoot, "vite.matrix.config.ts"),
    root: rendererRoot,
    logLevel: "error"
  });
  const chunk = chunkFromBuildResult(result);
  validateModuleGraph({ moduleIds: Object.keys(chunk.modules), packageLock });
  const bundle = Buffer.from(chunk.code, "utf8");
  validateRuntimeBundle(bundle);
  const bundleDigest = sha256(bundle);
  assert(bootstrapTemplate.split(BOOTSTRAP_PLACEHOLDER).length === 2, "Expected one bootstrap digest placeholder");
  const bootstrap = Buffer.from(bootstrapTemplate.replace(BOOTSTRAP_PLACEHOLDER, bundleDigest), "utf8");
  const manifest = {
    bootstrap_sha256: sha256(bootstrap),
    build_tool_id: "patent-analysis.renderer-bundler",
    build_tool_version: "1.0.0",
    echarts_version: "6.1.0",
    renderer_build_manifest_version: "1.0.0",
    renderer_bundle_sha256: bundleDigest,
    renderer_protocol_version: "1.0.0"
  };
  validateBuildArtifacts(bootstrap, bundle, manifest);
  await mkdir(packageOutputRoot, { recursive: true });
  await Promise.all([
    writeFile(resolve(packageOutputRoot, "matrix-bootstrap.js"), bootstrap),
    writeFile(resolve(packageOutputRoot, "matrix-renderer.bundle.js"), bundle),
    writeFile(
      resolve(packageOutputRoot, "matrix-renderer-build-manifest.json"),
      Buffer.from(stableJson(manifest), "utf8")
    )
  ]);
  console.log(`matrix renderer bundle built ${bundle.byteLength} bytes ${bundleDigest}`);
}

if (process.argv[1] !== undefined && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await main();
}
