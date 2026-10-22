import { createHash } from "node:crypto";
import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const rendererRoot = dirname(fileURLToPath(new URL("../package.json", import.meta.url)));
const packageRoot = join(rendererRoot, "..", "src", "patent_analysis", "renderer");
const bootstrapPath = join(packageRoot, "bootstrap.js");
const bundlePath = join(packageRoot, "renderer.bundle.js");
const manifestPath = join(packageRoot, "renderer-build-manifest.json");
const MAX_BUNDLE_BYTES = 4 * 1024 * 1024;
const MAX_REQUEST_BYTES = 3 * 1024 * 1024;
const MAX_FRAME_BYTES = 7 * 1024 * 1024;
const EXACT_BOOTSTRAP_PREFIX = [
  "--permission",
  "--max-old-space-size=192",
  "--disable-proto=throw"
];

function sha256(bytes: string | Buffer): string {
  return createHash("sha256").update(bytes).digest("hex");
}

function canonicalize(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, nested]) => [key, canonicalize(nested)])
    );
  }
  return value;
}

function frame(
  bundle: Uint8Array,
  request: Uint8Array = Buffer.from("{}", "utf8")
): Buffer {
  const header = Buffer.alloc(20);
  header.write("PARSVG01", 0, "ascii");
  header.writeUInt32BE(1, 8);
  header.writeUInt32BE(bundle.byteLength, 12);
  header.writeUInt32BE(request.byteLength, 16);
  return Buffer.concat([header, bundle, request]);
}

function canonicalJsonBytes(value: unknown): Buffer {
  return Buffer.from(JSON.stringify(canonicalize(value)), "utf8");
}

function validRendererRequest(): Buffer {
  const model = canonicalJsonBytes({
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
  });
  const spec = canonicalJsonBytes({
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
  });
  return canonicalJsonBytes({
    protocol_version: "1.0.0",
    chart_model_b64: model.toString("base64"),
    chart_model_sha256: sha256(model),
    render_spec_b64: spec.toString("base64"),
    render_spec_sha256: sha256(spec)
  });
}

function runBootstrapWithArgv(source: string, input: Buffer, execArgv: string[]) {
  return spawnSync(process.execPath, execArgv, {
    input,
    encoding: "utf8",
    maxBuffer: 16 * 1024 * 1024
  });
}

function runBootstrap(source: string, input: Buffer) {
  return runBootstrapWithArgv(source, input, [...EXACT_BOOTSTRAP_PREFIX, "--eval", source]);
}

function outputJson(result: ReturnType<typeof runBootstrap>) {
  expect(result.status).toBe(0);
  expect(result.stderr).toBe("");
  return JSON.parse(result.stdout) as {
    ok: boolean;
    runtime: { renderer_build_digest: string };
    error?: { code: string; message: string };
  };
}

function expectFailure(result: ReturnType<typeof runBootstrap>, code: string, message: string) {
  expect(outputJson(result)).toMatchObject({ ok: false, error: { code, message } });
}

function bootstrapForBundle(bootstrap: string, currentBundle: Buffer, replacementBundle: Buffer) {
  const currentDigest = sha256(currentBundle);
  if (bootstrap.split(currentDigest).length !== 2) throw new Error("Expected one embedded bundle digest");
  return bootstrap.replace(currentDigest, sha256(replacementBundle));
}

function expectSingleSafeRenderFailure(result: ReturnType<typeof runBootstrap>) {
  expect(result.status).toBe(0);
  expect(result.stderr).toBe("");
  expect(result.stdout.endsWith("\n")).toBe(true);
  const withoutTerminator = result.stdout.slice(0, -1);
  expect(withoutTerminator).not.toContain("\n");
  expect(JSON.parse(withoutTerminator)).toEqual({
    protocol_version: "1.0.0",
    ok: false,
    runtime: {
      node_version: "22.23.4",
      echarts_version: "6.1.0",
      renderer_build_digest: expect.stringMatching(/^[0-9a-f]{64}$/u),
      render_profile_id: "ranking-svg-ja-jp-node22-echarts6.v1"
    },
    error: { code: "render.failed", message: "Renderer failed" }
  });
}

function capabilityProbe(attack: string) {
  return Buffer.from(`${attack}
var PatentAnalysisRenderer={renderRequest:function(_request,runtimeJson){
  var runtime=typeof runtimeJson==="string"?JSON.parse(runtimeJson):runtimeJson;
  return JSON.stringify({protocol_version:"1.0.0",ok:false,runtime:runtime,error:{code:"render.failed",message:"COMPROMISED"}});
}};`, "utf8");
}

describe("fixed renderer bootstrap", () => {
  it("has all bootstrap runtime artifacts before contract checks run", () => {
    const missing = [bootstrapPath, bundlePath, manifestPath].filter((path) => !existsSync(path));

    expect(missing).toEqual([]);
  });

  it("reconstructs the exact self hash and seven-field build digest from --eval bytes", async () => {
    if (![bootstrapPath, bundlePath, manifestPath].every(existsSync)) return;
    const [bootstrap, bundle, manifestText] = await Promise.all([
      readFile(bootstrapPath, "utf8"),
      readFile(bundlePath),
      readFile(manifestPath, "utf8")
    ]);
    const manifest = JSON.parse(manifestText) as Record<string, string>;
    const alteredBootstrap = `${bootstrap};`;
    const alteredManifest = {
      ...manifest,
      bootstrap_sha256: sha256(alteredBootstrap)
    };
    const expectedBuildDigest = sha256(JSON.stringify(canonicalize(alteredManifest)));

    expect(Object.keys(manifest).sort()).toEqual([
      "bootstrap_sha256",
      "build_tool_id",
      "build_tool_version",
      "echarts_version",
      "renderer_build_manifest_version",
      "renderer_bundle_sha256",
      "renderer_protocol_version"
    ]);
    expect(manifest.bootstrap_sha256).toBe(sha256(bootstrap));
    expect(manifest.renderer_bundle_sha256).toBe(sha256(bundle));
    expect(outputJson(runBootstrap(alteredBootstrap, frame(bundle))).runtime.renderer_build_digest)
      .toBe(expectedBuildDigest);
  });

  it("requires the exact ordered five-element runtime execArgv", async () => {
    if (![bootstrapPath, bundlePath].every(existsSync)) return;
    const [bootstrap, bundle] = await Promise.all([
      readFile(bootstrapPath, "utf8"),
      readFile(bundlePath)
    ]);
    const input = frame(bundle);
    const invalidArgv = [
      ["--eval", bootstrap],
      ["--permission", "--max-old-space-size=192", "--eval", bootstrap],
      ["--max-old-space-size=192", "--permission", "--disable-proto=throw", "--eval", bootstrap],
      [...EXACT_BOOTSTRAP_PREFIX, "--no-warnings", "--eval", bootstrap]
    ];

    expect(runBootstrap(bootstrap, input).status).toBe(0);
    for (const argv of invalidArgv) {
      const result = runBootstrapWithArgv(bootstrap, input, argv);
      expect(result.status).not.toBe(0);
      expect(result.stdout).toBe("");
    }
  });

  it("verifies the bundle digest before executing untrusted frame bytes", async () => {
    if (![bootstrapPath, bundlePath].every(existsSync)) return;
    const bootstrap = await readFile(bootstrapPath, "utf8");
    const maliciousBundle = Buffer.from(
      "globalThis.__renderer_digest_bypass__=true;throw new Error('executed');",
      "utf8"
    );
    const response = outputJson(runBootstrap(bootstrap, frame(maliciousBundle)));

    expect(response).toMatchObject({
      ok: false,
      error: { code: "digest.mismatch", message: "Renderer payload digest does not match" }
    });
    expect(response.error?.message).not.toContain("executed");
  });

  it("executes the verified IIFE in memory and passes only request bytes plus runtime binding", async () => {
    if (![bootstrapPath, bundlePath].every(existsSync)) return;
    const [bootstrap, bundle] = await Promise.all([
      readFile(bootstrapPath, "utf8"),
      readFile(bundlePath)
    ]);
    const response = outputJson(runBootstrap(bootstrap, frame(bundle, Buffer.from('{"probe":true}'))));

    expect(response).toMatchObject({
      ok: false,
      error: { code: "protocol.invalid", message: "Renderer protocol is invalid" }
    });
    expect(bootstrap).toContain('process.getBuiltinModule("node:vm")');
    expect(bootstrap).not.toMatch(/(?:readFile|writeFile|import\s*\(|require\s*\(\s*["'](?:\.|\/|[A-Za-z]:))/u);
  });

  it("transfers request and runtime only as primitive JSON strings and returns one context-serialized response", async () => {
    if (![bootstrapPath, bundlePath].every(existsSync)) return;
    const [bootstrap, currentBundle] = await Promise.all([
      readFile(bootstrapPath, "utf8"),
      readFile(bundlePath)
    ]);
    const probeBundle = Buffer.from(`var PatentAnalysisRenderer={renderRequest:function(requestJson,runtimeJson){
  if(typeof requestJson!=="string"||typeof runtimeJson!=="string"){
    return JSON.stringify({compromised:true});
  }
  var runtime=JSON.parse(runtimeJson);
  return JSON.stringify({protocol_version:"1.0.0",ok:false,runtime:runtime,error:{code:"render.failed",message:"Renderer failed"}});
}};`, "utf8");
    const probeBootstrap = bootstrapForBundle(bootstrap, currentBundle, probeBundle);

    expectSingleSafeRenderFailure(runBootstrap(probeBootstrap, frame(probeBundle, Buffer.from('{"probe":true}'))));
  });

  it("blocks ambient Node, network, code-generation, prototype-eval, and output capabilities", async () => {
    if (![bootstrapPath, bundlePath].every(existsSync)) return;
    const [bootstrap, currentBundle] = await Promise.all([
      readFile(bootstrapPath, "utf8"),
      readFile(bundlePath)
    ]);
    const attacks = [
      'process.getBuiltinModule("node:fs");',
      'if(typeof globalThis["fetch"]!=="function")throw new Error("fetch absent");',
      'process.stdout.write("LEAK");',
      'require("node:fs");',
      "module.exports;",
      'Buffer.from("LEAK");',
      'console.log("LEAK");',
      'process.getBuiltinModule("node:child_process");',
      'Function("return process")();',
      '({}).constructor.constructor("return process")();',
      "new WebAssembly.Module(new Uint8Array([0,97,115,109,1,0,0,0]));",
      'process.stdout.write("{\\"extra\\":1}\\n{\\"extra\\":2}\\n");'
    ];

    for (const attack of attacks) {
      const maliciousBundle = capabilityProbe(attack);
      const maliciousBootstrap = bootstrapForBundle(bootstrap, currentBundle, maliciousBundle);
      expectSingleSafeRenderFailure(runBootstrap(maliciousBootstrap, frame(maliciousBundle)));
    }
  });

  it("maps wrong magic/version and truncated/trailing/concatenated frames to protocol.invalid", async () => {
    if (![bootstrapPath, bundlePath].every(existsSync)) return;
    const [bootstrap, bundle] = await Promise.all([
      readFile(bootstrapPath, "utf8"),
      readFile(bundlePath)
    ]);
    const valid = frame(bundle);
    const wrongMagic = Buffer.from(valid);
    wrongMagic[0] = "X".charCodeAt(0);
    const wrongVersion = Buffer.from(valid);
    wrongVersion.writeUInt32BE(2, 8);
    const headerOnly = valid.subarray(0, 20);
    const trailing = Buffer.concat([valid, Buffer.from([0])]);
    const multiple = Buffer.concat([valid, valid]);

    for (const invalid of [wrongMagic, wrongVersion, headerOnly, trailing, multiple]) {
      expectFailure(
        runBootstrap(bootstrap, invalid),
        "protocol.invalid",
        "Renderer protocol is invalid"
      );
    }
  });

  it("maps only bundle, request, and total frame size excess to payload.too_large", async () => {
    if (![bootstrapPath, bundlePath].every(existsSync)) return;
    const bootstrap = await readFile(bootstrapPath, "utf8");
    const oversizedBundleHeader = Buffer.alloc(20);
    oversizedBundleHeader.write("PARSVG01", 0, "ascii");
    oversizedBundleHeader.writeUInt32BE(1, 8);
    oversizedBundleHeader.writeUInt32BE(MAX_BUNDLE_BYTES + 1, 12);
    oversizedBundleHeader.writeUInt32BE(0, 16);
    const oversizedRequestHeader = Buffer.from(oversizedBundleHeader);
    oversizedRequestHeader.writeUInt32BE(0, 12);
    oversizedRequestHeader.writeUInt32BE(MAX_REQUEST_BYTES + 1, 16);
    const overTotalHeader = Buffer.from(oversizedBundleHeader);
    overTotalHeader.writeUInt32BE(MAX_BUNDLE_BYTES, 12);
    overTotalHeader.writeUInt32BE(MAX_FRAME_BYTES - MAX_BUNDLE_BYTES, 16);

    for (const invalid of [oversizedBundleHeader, oversizedRequestHeader, overTotalHeader]) {
      expectFailure(
        runBootstrap(bootstrap, invalid),
        "payload.too_large",
        "Renderer payload is too large"
      );
    }
  });

  it("accepts exact 4 MiB bundle, 3 MiB request, and 7 MiB total boundaries before one-over", async () => {
    if (![bootstrapPath, bundlePath].every(existsSync)) return;
    const [bootstrap, bundle] = await Promise.all([
      readFile(bootstrapPath, "utf8"),
      readFile(bundlePath)
    ]);
    const exactBundle = Buffer.alloc(MAX_BUNDLE_BYTES, 0x20);
    expectFailure(
      runBootstrap(bootstrap, frame(exactBundle, Buffer.alloc(0))),
      "digest.mismatch",
      "Renderer payload digest does not match"
    );

    const exactRequest = Buffer.alloc(MAX_REQUEST_BYTES, 0x20);
    expectFailure(
      runBootstrap(bootstrap, frame(bundle, exactRequest)),
      "protocol.invalid",
      "Renderer protocol is invalid"
    );

    const totalRequestLength = MAX_FRAME_BYTES - 20 - MAX_BUNDLE_BYTES;
    const exactTotalFrame = frame(exactBundle, Buffer.alloc(totalRequestLength, 0x20));
    expect(exactTotalFrame.byteLength).toBe(MAX_FRAME_BYTES);
    expectFailure(
      runBootstrap(bootstrap, exactTotalFrame),
      "digest.mismatch",
      "Renderer payload digest does not match"
    );

    const oneOverTotalHeader = Buffer.alloc(20);
    oneOverTotalHeader.write("PARSVG01", 0, "ascii");
    oneOverTotalHeader.writeUInt32BE(1, 8);
    oneOverTotalHeader.writeUInt32BE(MAX_BUNDLE_BYTES, 12);
    oneOverTotalHeader.writeUInt32BE(MAX_FRAME_BYTES - MAX_BUNDLE_BYTES - 19, 16);
    expectFailure(
      runBootstrap(bootstrap, oneOverTotalHeader),
      "payload.too_large",
      "Renderer payload is too large"
    );
  });

  it("produces byte-identical responses and normalized SVG across ten cold processes", async () => {
    if (![bootstrapPath, bundlePath].every(existsSync)) return;
    const [bootstrap, bundle] = await Promise.all([
      readFile(bootstrapPath, "utf8"),
      readFile(bundlePath)
    ]);
    const input = frame(Buffer.from(bundle), validRendererRequest());
    const responses: string[] = [];
    const svgs: Buffer[] = [];

    for (let invocation = 0; invocation < 10; invocation += 1) {
      const result = runBootstrap(bootstrap, input);
      expect(result.status).toBe(0);
      expect(result.stderr).toBe("");
      responses.push(result.stdout);
      const response = JSON.parse(result.stdout) as { ok: boolean; svg_b64?: string };
      expect(response.ok, result.stdout).toBe(true);
      svgs.push(Buffer.from(response.svg_b64 ?? "", "base64"));
    }

    expect(new Set(responses).size).toBe(1);
    expect(new Set(svgs.map((svg) => svg.toString("base64"))).size).toBe(1);
    expect(new Set(svgs.map(sha256)).size).toBe(1);
    const svg = svgs[0]!.toString("utf8");
    expect(svg).not.toMatch(/<(?:style|script)\b|\s(?:style|class|pointer-events|ecmeta_[a-z_]+)=/u);
    expect(svg.endsWith("\n")).toBe(true);
  });
});
