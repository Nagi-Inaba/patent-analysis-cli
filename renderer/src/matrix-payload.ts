// @ts-expect-error -- generated build-time validators intentionally have no hand-maintained typings.
import { validateChartModel, validateRendererRequest, validateRendererRuntime, validateRenderSpec } from "./generated/matrix-standalone-validators.js";
import type { PaletteId } from "./palette.js";

const MAX_REQUEST_BYTES = 3 * 1024 * 1024;
const MAX_CHART_MODEL_BYTES = 2 * 1024 * 1024;
const MAX_RENDER_SPEC_BYTES = 16 * 1024;
const BASE64_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

const FAILURE_MESSAGES = Object.freeze({
  "protocol.invalid": "Renderer protocol is invalid",
  "payload.too_large": "Renderer payload is too large",
  "digest.mismatch": "Renderer payload digest does not match",
  "schema.invalid": "Renderer input was rejected",
  "runtime.mismatch": "Renderer runtime does not match",
  "render.failed": "Renderer failed"
} as const);

export type RendererFailureCode = keyof typeof FAILURE_MESSAGES;

export type RuntimeBinding = {
  node_version: "22.19.0";
  echarts_version: "6.1.0";
  renderer_build_digest: string;
  render_profile_id: "matrix-svg-ja-jp-node22-echarts6.v1";
};

export type MatrixCategory = {
  id: string;
  index: number;
  label: string;
  count: number;
  is_other: boolean;
};

export type MatrixAxis = {
  role: string;
  categories: readonly MatrixCategory[];
};

export type MatrixSlice = {
  index: number;
  label: string;
  count: number;
};

export type MatrixCell = {
  x_index: number;
  y_index: number;
  x_label: string;
  y_label: string;
  value: number;
  row_count: number;
  // Present on every cell exactly when the model has a pie.
  slices?: readonly MatrixSlice[];
};

export type MatrixPieCategory = {
  id: string;
  index: number;
  label: string;
  count: number;
  is_other: boolean;
};

export type MatrixPie = {
  role: string;
  categories: readonly MatrixPieCategory[];
};

export type MatrixChartModel = {
  chart_model_contract_version: "1.0.0";
  chart_type: "matrix.bubble" | "matrix.heatmap";
  mark: "matrix-bubble-svg.v1" | "matrix-heatmap-svg.v1";
  analysis_result_sha256: string;
  title: string;
  x_axis: MatrixAxis;
  y_axis: MatrixAxis;
  cells: readonly MatrixCell[];
  // Splits each bubble of the bubble mark into slices; the heatmap ignores it.
  pie?: MatrixPie;
  population: { input_rows: number; analyzed_rows: number; excluded_rows: number };
  warnings: readonly string[];
};

export type MatrixRenderSpec = {
  render_spec_contract_version: "1.0.0";
  renderer_kind: "matrix.bubble.svg" | "matrix.heatmap.svg";
  locale: "ja-JP";
  timezone: "UTC";
  width: 1200;
  height: 675;
  font_family: "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif";
  animation: false;
  axis_label_max_graphemes: 28;
  echarts_version: "6.1.0";
  render_profile_id: "matrix-svg-ja-jp-node22-echarts6.v1";
  // Absent means "hidden"; only the bubble mark draws count labels.
  value_labels?: "hidden" | "shown";
  // Absent means "standard": each family keeps its own colours.
  palette?: PaletteId;
};

export type ChartModel = MatrixChartModel;
export type RenderSpec = MatrixRenderSpec;

type RendererRequest = {
  protocol_version: "1.0.0";
  chart_model_b64: string;
  chart_model_sha256: string;
  render_spec_b64: string;
  render_spec_sha256: string;
};

export type RendererFailure = {
  protocol_version: "1.0.0";
  ok: false;
  runtime: RuntimeBinding;
  error: { code: RendererFailureCode; message: (typeof FAILURE_MESSAGES)[RendererFailureCode] };
};

export type PreparedRendererPayload = {
  ok: true;
  runtime: RuntimeBinding;
  model: ChartModel;
  spec: RenderSpec;
};

function base64Value(code: number): number {
  if (code >= 65 && code <= 90) return code - 65;
  if (code >= 97 && code <= 122) return code - 71;
  if (code >= 48 && code <= 57) return code + 4;
  if (code === 43) return 62;
  if (code === 47) return 63;
  return -1;
}

export function decodeCanonicalBase64(value: unknown, maxBytes: number): Uint8Array {
  if (typeof value !== "string" || value.length === 0 || value.length % 4 !== 0) {
    throw new Error("invalid base64");
  }
  const padding = value.endsWith("==") ? 2 : value.endsWith("=") ? 1 : 0;
  const decodedLength = (value.length / 4) * 3 - padding;
  if (decodedLength > maxBytes) throw new RangeError("base64 payload too large");
  const output = new Uint8Array(decodedLength);
  let outputIndex = 0;
  for (let index = 0; index < value.length; index += 4) {
    const finalQuantum = index + 4 === value.length;
    const a = base64Value(value.charCodeAt(index));
    const b = base64Value(value.charCodeAt(index + 1));
    const cCode = value.charCodeAt(index + 2);
    const dCode = value.charCodeAt(index + 3);
    const c = cCode === 61 ? 0 : base64Value(cCode);
    const d = dCode === 61 ? 0 : base64Value(dCode);
    if (
      a < 0 || b < 0 || c < 0 || d < 0 ||
      (!finalQuantum && (cCode === 61 || dCode === 61)) ||
      (cCode === 61 && dCode !== 61) ||
      (cCode === 61 && (b & 0x0F) !== 0) ||
      (dCode === 61 && cCode !== 61 && (c & 0x03) !== 0)
    ) {
      throw new Error("invalid base64");
    }
    const combined = (a << 18) | (b << 12) | (c << 6) | d;
    if (outputIndex < output.length) output[outputIndex++] = combined >>> 16;
    if (outputIndex < output.length) output[outputIndex++] = combined >>> 8;
    if (outputIndex < output.length) output[outputIndex++] = combined;
  }
  return output;
}

export function encodeUtf8(value: string): Uint8Array {
  const output = new Uint8Array(value.length * 3);
  let outputIndex = 0;
  for (const character of value) {
    const codePoint = character.codePointAt(0)!;
    if (codePoint >= 0xD800 && codePoint <= 0xDFFF) throw new Error("invalid unicode");
    if (codePoint <= 0x7F) {
      output[outputIndex++] = codePoint;
    } else if (codePoint <= 0x7FF) {
      output[outputIndex++] = 0xC0 | (codePoint >>> 6);
      output[outputIndex++] = 0x80 | (codePoint & 0x3F);
    } else if (codePoint <= 0xFFFF) {
      output[outputIndex++] = 0xE0 | (codePoint >>> 12);
      output[outputIndex++] = 0x80 | ((codePoint >>> 6) & 0x3F);
      output[outputIndex++] = 0x80 | (codePoint & 0x3F);
    } else {
      output[outputIndex++] = 0xF0 | (codePoint >>> 18);
      output[outputIndex++] = 0x80 | ((codePoint >>> 12) & 0x3F);
      output[outputIndex++] = 0x80 | ((codePoint >>> 6) & 0x3F);
      output[outputIndex++] = 0x80 | (codePoint & 0x3F);
    }
  }
  return output.slice(0, outputIndex);
}

export function encodeCanonicalBase64(bytes: Uint8Array): string {
  const parts: string[] = [];
  let part = "";
  for (let index = 0; index < bytes.length; index += 3) {
    const a = bytes[index]!;
    const hasB = index + 1 < bytes.length;
    const hasC = index + 2 < bytes.length;
    const b = hasB ? bytes[index + 1]! : 0;
    const c = hasC ? bytes[index + 2]! : 0;
    const combined = (a << 16) | (b << 8) | c;
    part += BASE64_ALPHABET[(combined >>> 18) & 0x3F]!;
    part += BASE64_ALPHABET[(combined >>> 12) & 0x3F]!;
    part += hasB ? BASE64_ALPHABET[(combined >>> 6) & 0x3F]! : "=";
    part += hasC ? BASE64_ALPHABET[combined & 0x3F]! : "=";
    if (part.length >= 16_384) {
      parts.push(part);
      part = "";
    }
  }
  if (part.length > 0) parts.push(part);
  return parts.join("");
}

function decodeUtf8(bytes: Uint8Array): string {
  const codePoints: number[] = [];
  const chunks: string[] = [];
  const flush = () => {
    if (codePoints.length > 0) chunks.push(String.fromCodePoint(...codePoints.splice(0)));
  };
  for (let index = 0; index < bytes.length;) {
    const first = bytes[index++]!;
    let codePoint: number;
    let continuationCount: number;
    let minimum: number;
    if (first <= 0x7F) {
      codePoint = first;
      continuationCount = 0;
      minimum = 0;
    } else if (first >= 0xC2 && first <= 0xDF) {
      codePoint = first & 0x1F;
      continuationCount = 1;
      minimum = 0x80;
    } else if (first >= 0xE0 && first <= 0xEF) {
      codePoint = first & 0x0F;
      continuationCount = 2;
      minimum = 0x800;
    } else if (first >= 0xF0 && first <= 0xF4) {
      codePoint = first & 0x07;
      continuationCount = 3;
      minimum = 0x10000;
    } else {
      throw new Error("invalid utf8");
    }
    if (index + continuationCount > bytes.length) throw new Error("invalid utf8");
    for (let count = 0; count < continuationCount; count += 1) {
      const next = bytes[index++]!;
      if ((next & 0xC0) !== 0x80) throw new Error("invalid utf8");
      codePoint = (codePoint << 6) | (next & 0x3F);
    }
    if (
      codePoint < minimum ||
      codePoint > 0x10FFFF ||
      (codePoint >= 0xD800 && codePoint <= 0xDFFF)
    ) throw new Error("invalid utf8");
    codePoints.push(codePoint);
    if (codePoints.length === 4096) flush();
  }
  flush();
  return chunks.join("");
}

function pythonFloatLexeme(value: number): string | null {
  if (!Number.isFinite(value) || Object.is(value, -0)) return null;
  const negative = value < 0;
  const absolute = Math.abs(value);
  if (absolute === 0) return "0.0";
  const shortest = absolute.toString();
  let digits: string;
  let exponent: number;
  const exponentIndex = shortest.indexOf("e");
  if (exponentIndex !== -1) {
    const mantissa = shortest.slice(0, exponentIndex);
    digits = mantissa.replace(".", "");
    exponent = Number.parseInt(shortest.slice(exponentIndex + 1), 10);
  } else {
    const pointIndex = shortest.indexOf(".");
    if (pointIndex === -1) {
      digits = shortest;
      exponent = shortest.length - 1;
    } else if (shortest[0] !== "0") {
      digits = shortest.slice(0, pointIndex) + shortest.slice(pointIndex + 1);
      exponent = pointIndex - 1;
    } else {
      const fraction = shortest.slice(2);
      const firstSignificant = fraction.search(/[1-9]/u);
      if (firstSignificant === -1) return "0.0";
      digits = fraction.slice(firstSignificant);
      exponent = -(firstSignificant + 1);
    }
  }
  digits = digits.replace(/0+$/u, "");
  let formatted: string;
  if (exponent < -4 || exponent >= 16) {
    const coefficient = digits.length === 1 ? digits : `${digits[0]}.${digits.slice(1)}`;
    const exponentSign = exponent < 0 ? "-" : "+";
    formatted = `${coefficient}e${exponentSign}${Math.abs(exponent).toString().padStart(2, "0")}`;
  } else if (exponent >= 0) {
    const integerDigits = digits.padEnd(exponent + 1, "0");
    formatted = digits.length <= exponent + 1
      ? `${integerDigits}.0`
      : `${digits.slice(0, exponent + 1)}.${digits.slice(exponent + 1)}`;
  } else {
    formatted = `0.${"0".repeat(-exponent - 1)}${digits}`;
  }
  return negative ? `-${formatted}` : formatted;
}

function isPythonCanonicalNumberLexeme(lexeme: string): boolean {
  if (/^(?:0|[1-9][0-9]*|-[1-9][0-9]*)$/u.test(lexeme)) return true;
  if (!/^-?(?:0|[1-9][0-9]*)\.[0-9]+(?:e[+-]?[0-9]+)?$|^-?(?:0|[1-9][0-9]*)e[+-]?[0-9]+$/u.test(lexeme)) {
    return false;
  }
  const number = Number(lexeme);
  return pythonFloatLexeme(number) === lexeme;
}

function isRendererSafeNumberLexeme(lexeme: string): boolean {
  if (!isPythonCanonicalNumberLexeme(lexeme)) return false;
  const integerMatch = /^(-?)(0|[1-9][0-9]*)$/u.exec(lexeme);
  if (integerMatch === null) return true;
  const digits = integerMatch[2]!;
  const maximum = "9007199254740991";
  return digits.length < maximum.length ||
    digits.length === maximum.length && digits <= maximum;
}

const SHA256_CONSTANTS = Object.freeze([
  0x428A2F98, 0x71374491, 0xB5C0FBCF, 0xE9B5DBA5, 0x3956C25B, 0x59F111F1, 0x923F82A4, 0xAB1C5ED5,
  0xD807AA98, 0x12835B01, 0x243185BE, 0x550C7DC3, 0x72BE5D74, 0x80DEB1FE, 0x9BDC06A7, 0xC19BF174,
  0xE49B69C1, 0xEFBE4786, 0x0FC19DC6, 0x240CA1CC, 0x2DE92C6F, 0x4A7484AA, 0x5CB0A9DC, 0x76F988DA,
  0x983E5152, 0xA831C66D, 0xB00327C8, 0xBF597FC7, 0xC6E00BF3, 0xD5A79147, 0x06CA6351, 0x14292967,
  0x27B70A85, 0x2E1B2138, 0x4D2C6DFC, 0x53380D13, 0x650A7354, 0x766A0ABB, 0x81C2C92E, 0x92722C85,
  0xA2BFE8A1, 0xA81A664B, 0xC24B8B70, 0xC76C51A3, 0xD192E819, 0xD6990624, 0xF40E3585, 0x106AA070,
  0x19A4C116, 0x1E376C08, 0x2748774C, 0x34B0BCB5, 0x391C0CB3, 0x4ED8AA4A, 0x5B9CCA4F, 0x682E6FF3,
  0x748F82EE, 0x78A5636F, 0x84C87814, 0x8CC70208, 0x90BEFFFA, 0xA4506CEB, 0xBEF9A3F7, 0xC67178F2
]);

function rotateRight(value: number, shift: number): number {
  return (value >>> shift) | (value << (32 - shift));
}

export function sha256Hex(bytes: Uint8Array): string {
  const bitLength = bytes.length * 8;
  const paddedLength = Math.ceil((bytes.length + 9) / 64) * 64;
  const padded = new Uint8Array(paddedLength);
  padded.set(bytes);
  padded[bytes.length] = 0x80;
  const view = new DataView(padded.buffer);
  view.setUint32(paddedLength - 8, Math.floor(bitLength / 0x1_0000_0000));
  view.setUint32(paddedLength - 4, bitLength >>> 0);
  const state = new Uint32Array([
    0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A,
    0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19
  ]);
  const words = new Uint32Array(64);
  for (let offset = 0; offset < paddedLength; offset += 64) {
    for (let index = 0; index < 16; index += 1) words[index] = view.getUint32(offset + index * 4);
    for (let index = 16; index < 64; index += 1) {
      const previous15 = words[index - 15]!;
      const previous2 = words[index - 2]!;
      const small0 = rotateRight(previous15, 7) ^ rotateRight(previous15, 18) ^ (previous15 >>> 3);
      const small1 = rotateRight(previous2, 17) ^ rotateRight(previous2, 19) ^ (previous2 >>> 10);
      words[index] = (words[index - 16]! + small0 + words[index - 7]! + small1) >>> 0;
    }
    let [a, b, c, d, e, f, g, h] = state;
    for (let index = 0; index < 64; index += 1) {
      const large1 = rotateRight(e!, 6) ^ rotateRight(e!, 11) ^ rotateRight(e!, 25);
      const choose = (e! & f!) ^ (~e! & g!);
      const temp1 = (h! + large1 + choose + SHA256_CONSTANTS[index]! + words[index]!) >>> 0;
      const large0 = rotateRight(a!, 2) ^ rotateRight(a!, 13) ^ rotateRight(a!, 22);
      const majority = (a! & b!) ^ (a! & c!) ^ (b! & c!);
      const temp2 = (large0 + majority) >>> 0;
      h = g; g = f; f = e; e = (d! + temp1) >>> 0;
      d = c; c = b; b = a; a = (temp1 + temp2) >>> 0;
    }
    state[0] = (state[0]! + a!) >>> 0;
    state[1] = (state[1]! + b!) >>> 0;
    state[2] = (state[2]! + c!) >>> 0;
    state[3] = (state[3]! + d!) >>> 0;
    state[4] = (state[4]! + e!) >>> 0;
    state[5] = (state[5]! + f!) >>> 0;
    state[6] = (state[6]! + g!) >>> 0;
    state[7] = (state[7]! + h!) >>> 0;
  }
  return Array.from(state, (word) => word.toString(16).padStart(8, "0")).join("");
}

function scanCanonicalJsonObject(text: string): void {
  let index = 0;

  const current = () => text[index];
  const consume = (expected: string) => {
    if (current() !== expected) throw new Error("noncanonical json");
    index += 1;
  };

  const scanString = (objectKey: boolean): string => {
    consume('"');
    let decoded = "";
    while (index < text.length) {
      const character = text[index++]!;
      if (character === '"') return decoded;
      const code = character.charCodeAt(0);
      if (code < 0x20) throw new Error("noncanonical json string");
      if (character !== "\\") {
        if (objectKey && code > 0x7F) throw new Error("noncanonical json key");
        decoded += character;
        continue;
      }
      if (objectKey || index >= text.length) throw new Error("noncanonical json key escape");
      const escaped = text[index++]!;
      if (escaped === '"' || escaped === "\\") {
        decoded += escaped;
        continue;
      }
      const shortEscapes: Record<string, string> = {
        b: "\b", f: "\f", n: "\n", r: "\r", t: "\t"
      };
      if (escaped in shortEscapes) {
        decoded += shortEscapes[escaped]!;
        continue;
      }
      if (escaped !== "u") throw new Error("noncanonical json escape");
      const digits = text.slice(index, index + 4);
      if (!/^[0-9a-f]{4}$/u.test(digits)) throw new Error("noncanonical unicode escape");
      const codeUnit = Number.parseInt(digits, 16);
      if (codeUnit > 0x1F || [0x08, 0x09, 0x0A, 0x0C, 0x0D].includes(codeUnit)) {
        throw new Error("noncanonical unicode escape");
      }
      decoded += String.fromCharCode(codeUnit);
      index += 4;
    }
    throw new Error("unterminated json string");
  };

  const scanNumber = () => {
    const start = index;
    if (current() === "-") index += 1;
    if (current() === "0") {
      index += 1;
      if (text[index] !== undefined && /[0-9]/u.test(text[index]!)) {
        throw new Error("noncanonical leading zero");
      }
    } else {
      if (current() === undefined || !/[1-9]/u.test(current()!)) throw new Error("invalid json number");
      while (current() !== undefined && /[0-9]/u.test(current()!)) index += 1;
    }
    if (current() === ".") {
      index += 1;
      if (current() === undefined || !/[0-9]/u.test(current()!)) throw new Error("invalid json fraction");
      while (current() !== undefined && /[0-9]/u.test(current()!)) index += 1;
    }
    if (current() === "e") {
      index += 1;
      if (current() === "+" || current() === "-") index += 1;
      if (current() === undefined || !/[0-9]/u.test(current()!)) throw new Error("invalid json exponent");
      while (current() !== undefined && /[0-9]/u.test(current()!)) index += 1;
    } else if (current() === "E") {
      throw new Error("noncanonical exponent");
    }
    const lexeme = text.slice(start, index);
    if (!isRendererSafeNumberLexeme(lexeme)) throw new Error("unsupported canonical json number");
  };

  const scanValue = (depth: number): void => {
    if (depth > 64) throw new Error("json depth");
    const character = current();
    if (character === "{") {
      scanObject(depth + 1);
      return;
    }
    if (character === "[") {
      consume("[");
      if (current() === "]") {
        index += 1;
        return;
      }
      while (true) {
        scanValue(depth + 1);
        if (current() === "]") {
          index += 1;
          return;
        }
        consume(",");
      }
    }
    if (character === '"') {
      scanString(false);
      return;
    }
    for (const literal of ["true", "false", "null"]) {
      if (text.startsWith(literal, index)) {
        index += literal.length;
        return;
      }
    }
    if (character === "-" || character !== undefined && /[0-9]/u.test(character)) {
      scanNumber();
      return;
    }
    throw new Error("invalid json value");
  };

  const scanObject = (depth: number): void => {
    consume("{");
    if (current() === "}") {
      index += 1;
      return;
    }
    let previousKey: string | null = null;
    while (true) {
      const key = scanString(true);
      if (previousKey !== null && previousKey >= key) throw new Error("noncanonical json key order");
      previousKey = key;
      consume(":");
      scanValue(depth + 1);
      if (current() === "}") {
        index += 1;
        return;
      }
      consume(",");
    }
  };

  scanObject(0);
  if (index !== text.length) throw new Error("trailing json bytes");
}

function parseObject(bytes: Uint8Array): unknown {
  const text = decodeUtf8(bytes);
  scanCanonicalJsonObject(text);
  const value: unknown = JSON.parse(text);
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("expected object");
  }
  return value;
}

export function rendererFailure(runtime: RuntimeBinding, code: RendererFailureCode): RendererFailure {
  return {
    protocol_version: "1.0.0",
    ok: false,
    runtime,
    error: { code, message: FAILURE_MESSAGES[code] }
  };
}

function fallbackRuntime(): RuntimeBinding {
  return {
    node_version: "22.19.0",
    echarts_version: "6.1.0",
    renderer_build_digest: "0".repeat(64),
    render_profile_id: "matrix-svg-ja-jp-node22-echarts6.v1"
  };
}

export function processRendererTransfer(
  requestBase64: unknown,
  runtimeJson: unknown
): PreparedRendererPayload | { ok: false; response: RendererFailure } {
  let runtime = fallbackRuntime();
  try {
    if (typeof runtimeJson !== "string") throw new Error("runtime transfer type");
    const candidate: unknown = JSON.parse(runtimeJson);
    if (!validateRendererRuntime(candidate)) {
      return { ok: false, response: rendererFailure(runtime, "runtime.mismatch") };
    }
    runtime = candidate as RuntimeBinding;
  } catch {
    return { ok: false, response: rendererFailure(runtime, "runtime.mismatch") };
  }

  let requestBytes: Uint8Array;
  try {
    requestBytes = decodeCanonicalBase64(requestBase64, MAX_REQUEST_BYTES);
  } catch (error) {
    const code = error instanceof RangeError ? "payload.too_large" : "protocol.invalid";
    return { ok: false, response: rendererFailure(runtime, code) };
  }

  let request: RendererRequest;
  try {
    const candidate = parseObject(requestBytes);
    if (!validateRendererRequest(candidate)) throw new Error("request schema");
    request = candidate as RendererRequest;
  } catch {
    return { ok: false, response: rendererFailure(runtime, "protocol.invalid") };
  }

  let modelBytes: Uint8Array;
  let specBytes: Uint8Array;
  try {
    modelBytes = decodeCanonicalBase64(request.chart_model_b64, MAX_CHART_MODEL_BYTES);
    specBytes = decodeCanonicalBase64(request.render_spec_b64, MAX_RENDER_SPEC_BYTES);
  } catch (error) {
    const code = error instanceof RangeError ? "payload.too_large" : "schema.invalid";
    return { ok: false, response: rendererFailure(runtime, code) };
  }
  if (
    sha256Hex(modelBytes) !== request.chart_model_sha256 ||
    sha256Hex(specBytes) !== request.render_spec_sha256
  ) {
    return { ok: false, response: rendererFailure(runtime, "digest.mismatch") };
  }

  try {
    const modelCandidate = parseObject(modelBytes);
    const specCandidate = parseObject(specBytes);
    if (!validateChartModel(modelCandidate) || !validateRenderSpec(specCandidate)) {
      throw new Error("inner schema");
    }
    const model = modelCandidate as MatrixChartModel;
    const spec = specCandidate as MatrixRenderSpec;
    return { ok: true, runtime, model, spec };
  } catch {
    return { ok: false, response: rendererFailure(runtime, "schema.invalid") };
  }
}
