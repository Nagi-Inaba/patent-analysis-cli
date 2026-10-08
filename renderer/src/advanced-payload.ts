import { decodeCanonicalBase64, encodeUtf8, encodeCanonicalBase64, sha256Hex } from "./points-payload.js";
import { validateAdvancedModel, validateAdvancedRequest, validateAdvancedRuntime, validateAdvancedSpec } from "./advanced-validation.js";
import type { AdvancedModel, AdvancedRuntime, AdvancedSpec } from "./advanced-types.js";
export { encodeUtf8, encodeCanonicalBase64 };
const MESSAGES = Object.freeze({
  "protocol.invalid": "Renderer protocol is invalid", "payload.too_large": "Renderer payload is too large",
  "digest.mismatch": "Renderer payload digest does not match", "schema.invalid": "Renderer input was rejected",
  "runtime.mismatch": "Renderer runtime does not match", "render.failed": "Renderer failed"
});
export type FailureCode = keyof typeof MESSAGES;
export function advancedFailure(runtime: AdvancedRuntime, code: FailureCode) {
  return { protocol_version: "1.0.0", ok: false, runtime, error: { code, message: MESSAGES[code] } } as const;
}
function decodeUtf8(bytes: Uint8Array): string {
  const chunks: string[] = [];
  const points: number[] = [];
  for (let i = 0; i < bytes.length;) {
    const first = bytes[i++]!;
    let value: number, count: number, minimum: number;
    if (first <= 0x7f) { value = first; count = 0; minimum = 0; }
    else if (first >= 0xc2 && first <= 0xdf) { value = first & 31; count = 1; minimum = 128; }
    else if (first >= 0xe0 && first <= 0xef) { value = first & 15; count = 2; minimum = 2048; }
    else if (first >= 0xf0 && first <= 0xf4) { value = first & 7; count = 3; minimum = 65536; }
    else throw new Error("invalid UTF-8");
    if (i + count > bytes.length) throw new Error("truncated UTF-8");
    for (let j = 0; j < count; j++) {
      const next = bytes[i++]!;
      if ((next & 0xc0) !== 0x80) throw new Error("invalid UTF-8");
      value = (value << 6) | (next & 63);
    }
    if (value < minimum || value > 0x10ffff || (value >= 0xd800 && value <= 0xdfff)) throw new Error("invalid UTF-8");
    points.push(value);
    if (points.length === 4096) chunks.push(String.fromCodePoint(...points.splice(0)));
  }
  if (points.length) chunks.push(String.fromCodePoint(...points));
  return chunks.join("");
}
function parse(bytes: Uint8Array): unknown {
  const value: unknown = JSON.parse(decodeUtf8(bytes));
  const queue: [unknown, number][] = [[value, 1]];
  let nodes = 0;
  while (queue.length) {
    const [item, depth] = queue.pop()!;
    if (depth > 64 || ++nodes > 50_000) throw new Error("JSON structural limit");
    if (typeof item === "number" && !Number.isFinite(item)) throw new Error("nonfinite number");
    if (Array.isArray(item)) for (const child of item) queue.push([child, depth + 1]);
    else if (item !== null && typeof item === "object") for (const child of Object.values(item)) queue.push([child, depth + 1]);
  }
  return value;
}
export function processAdvancedTransfer(requestBase64: unknown, runtimeJson: unknown):
  | { ok: true; runtime: AdvancedRuntime; model: AdvancedModel; spec: AdvancedSpec }
  | { ok: false; response: ReturnType<typeof advancedFailure> } {
  if (typeof runtimeJson !== "string" || runtimeJson.length > 16_384) throw new Error("invalid runtime transfer");
  const runtimeValue: unknown = JSON.parse(runtimeJson);
  if (!validateAdvancedRuntime(runtimeValue)) throw new Error("runtime binding invalid");
  const runtime = runtimeValue as AdvancedRuntime;
  let request: { chart_model_b64: string; chart_model_sha256: string; render_spec_b64: string; render_spec_sha256: string };
  try {
    const value = parse(decodeCanonicalBase64(requestBase64, 3 * 1024 * 1024));
    if (!validateAdvancedRequest(value)) throw new Error("request schema");
    request = value as typeof request;
  } catch (error) {
    return { ok: false, response: advancedFailure(runtime, error instanceof RangeError ? "payload.too_large" : "protocol.invalid") };
  }
  try {
    const modelBytes = decodeCanonicalBase64(request.chart_model_b64, 256 * 1024);
    const specBytes = decodeCanonicalBase64(request.render_spec_b64, 16 * 1024);
    if (sha256Hex(modelBytes) !== request.chart_model_sha256 || sha256Hex(specBytes) !== request.render_spec_sha256) {
      return { ok: false, response: advancedFailure(runtime, "digest.mismatch") };
    }
    const model = parse(modelBytes), spec = parse(specBytes);
    if (!validateAdvancedModel(model) || !validateAdvancedSpec(spec)) throw new Error("input schema");
    return { ok: true, runtime, model, spec: spec as AdvancedSpec };
  } catch (error) {
    return { ok: false, response: advancedFailure(runtime, error instanceof RangeError ? "payload.too_large" : "schema.invalid") };
  }
}
