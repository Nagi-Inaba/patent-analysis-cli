/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck -- emitted verbatim as the fixed JavaScript --eval source.
/* eslint-enable @typescript-eslint/ban-ts-comment */
(() => {
  "use strict";

  const EXPECTED_BUNDLE_SHA256 = "d9ec2822aa39b247be4b28049e703b77ad4eea421c2c99ae4be6cd9e291effe3";
  const MAX_BUNDLE_BYTES = 4 * 1024 * 1024;
  const MAX_REQUEST_BYTES = 3 * 1024 * 1024;
  const MAX_FRAME_BYTES = 7 * 1024 * 1024;
  const { createHash } = process.getBuiltinModule("node:crypto");
  const { createContext, Script } = process.getBuiltinModule("node:vm");

  /** @param {Uint8Array | string} value */
  const sha256 = (value) => createHash("sha256").update(value).digest("hex");
  /** @param {unknown} value @returns {unknown} */
  const canonicalize = (value) => {
    if (Array.isArray(value)) return value.map(canonicalize);
    if (value !== null && typeof value === "object") {
      return Object.fromEntries(
        Object.entries(/** @type {Record<string, unknown>} */ (value))
          .sort(([left], [right]) => (left < right ? -1 : left > right ? 1 : 0))
          .map(([key, nested]) => [key, canonicalize(nested)])
      );
    }
    return value;
  };
  const evalSource =
    process.execArgv.length === 5 &&
    process.execArgv[0] === "--permission" &&
    process.execArgv[1] === "--max-old-space-size=192" &&
    process.execArgv[2] === "--disable-proto=throw" &&
    process.execArgv[3] === "--eval"
      ? process.execArgv[4]
      : undefined;
  if (typeof evalSource !== "string") throw new Error("invalid bootstrap invocation");
  const buildManifest = {
    renderer_build_manifest_version: "1.0.0",
    bootstrap_sha256: sha256(evalSource),
    renderer_bundle_sha256: EXPECTED_BUNDLE_SHA256,
    renderer_protocol_version: "1.0.0",
    echarts_version: "6.1.0",
    build_tool_id: "patent-analysis.renderer-bundler",
    build_tool_version: "1.0.0"
  };
  const runtime = Object.freeze({
    node_version: process.versions.node,
    echarts_version: "6.1.0",
    renderer_build_digest: sha256(JSON.stringify(canonicalize(buildManifest))),
    render_profile_id: "ranking-svg-ja-jp-node22-echarts6.v1"
  });
  const failures = Object.freeze({
    protocol: { code: "protocol.invalid", message: "Renderer protocol is invalid" },
    tooLarge: { code: "payload.too_large", message: "Renderer payload is too large" },
    digest: { code: "digest.mismatch", message: "Renderer payload digest does not match" },
    render: { code: "render.failed", message: "Renderer failed" }
  });
  /** @param {{ code: string, message: string }} error */
  const fail = (error) => {
    process.stdout.write(`${JSON.stringify({ protocol_version: "1.0.0", ok: false, runtime, error })}\n`);
  };

  /** @type {Buffer[]} */
  const chunks = [];
  let receivedBytes = 0;
  let inputTooLarge = false;
  process.stdin.on("data", (chunk) => {
    receivedBytes += chunk.byteLength;
    if (receivedBytes > MAX_FRAME_BYTES) {
      inputTooLarge = true;
      return;
    }
    chunks.push(chunk);
  });
  process.stdin.on("end", () => {
    if (inputTooLarge) return fail(failures.tooLarge);
    const input = Buffer.concat(chunks, receivedBytes);
    if (input.byteLength < 20 || input.subarray(0, 8).toString("ascii") !== "PARSVG01") {
      return fail(failures.protocol);
    }
    const frameVersion = input.readUInt32BE(8);
    const bundleLength = input.readUInt32BE(12);
    const requestLength = input.readUInt32BE(16);
    const declaredLength = 20 + bundleLength + requestLength;
    if (frameVersion !== 1) return fail(failures.protocol);
    if (
      bundleLength > MAX_BUNDLE_BYTES ||
      requestLength > MAX_REQUEST_BYTES ||
      declaredLength > MAX_FRAME_BYTES
    ) {
      return fail(failures.tooLarge);
    }
    if (declaredLength !== input.byteLength) return fail(failures.protocol);
    const bundle = input.subarray(20, 20 + bundleLength);
    if (sha256(bundle) !== EXPECTED_BUNDLE_SHA256) return fail(failures.digest);
    const request = input.subarray(20 + bundleLength);
    try {
      const context = createContext(undefined, {
        name: "patent-analysis-renderer",
        codeGeneration: { strings: false, wasm: false }
      });
      new Script(`"use strict";
for (const name of [
  "process","require","module","exports","console","Buffer","fetch","WebSocket",
  "XMLHttpRequest","getBuiltinModule","stdout","stderr","setTimeout","setInterval",
  "setImmediate","queueMicrotask","Function","eval"
]) {
  Object.defineProperty(globalThis, name, { value: undefined, writable: false, configurable: false });
}`, { filename: "renderer-context.js" }).runInContext(context);
      new Script(bundle.toString("utf8"), { filename: "renderer.bundle.js" }).runInContext(context);
      context.__requestBase64 = request.toString("base64");
      context.__runtimeJson = JSON.stringify(runtime);
      const responseJson = new Script(`"use strict";
(() => {
  const entry = globalThis.PatentAnalysisRenderer;
  if (entry === null || typeof entry !== "object" || typeof entry.renderRequest !== "function") {
    throw new Error("renderer entry unavailable");
  }
  const serialized = entry.renderRequest(globalThis.__requestBase64, globalThis.__runtimeJson);
  if (typeof serialized !== "string") throw new Error("renderer response is not serialized");
  JSON.parse(serialized);
  return serialized;
})()`, { filename: "renderer-invoke.js" }).runInContext(context);
      if (typeof responseJson !== "string") return fail(failures.render);
      const response = JSON.parse(responseJson);
      if (response === null || typeof response !== "object" || Array.isArray(response)) {
        return fail(failures.render);
      }
      process.stdout.write(`${JSON.stringify(response)}\n`);
    } catch {
      fail(failures.render);
    }
  });
  process.stdin.resume();
})();
