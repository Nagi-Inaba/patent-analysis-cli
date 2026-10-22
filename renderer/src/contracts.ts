import type { JSONSchemaType } from "ajv";

export const RENDERER_PROTOCOL_VERSION = "1.0.0";

const SHA256_PATTERN = "^[0-9a-f]{64}(?![\\s\\S])";
const CANONICAL_BASE64_PATTERN = "^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/][AQgw]==|[A-Za-z0-9+/]{2}[AEIMQUYcgkosw048]=)?(?![\\s\\S])";
const ECHARTS_VERSION = "6.1.0";
const RENDER_PROFILE_ID = "ranking-svg-ja-jp-node22-echarts6.v1";
const NODE_VERSION = "22.23.4";

function deepFreeze<T>(value: T, seen = new Set<object>()): T {
  if (value === null || typeof value !== "object" || seen.has(value)) return value;
  seen.add(value);
  const record = value as Record<PropertyKey, unknown>;
  for (const key of Reflect.ownKeys(record)) {
    deepFreeze(record[key], seen);
  }
  return Object.freeze(value) as T;
}

export const RENDERER_FAILURES = deepFreeze([
  { code: "protocol.invalid", message: "Renderer protocol is invalid" },
  { code: "payload.too_large", message: "Renderer payload is too large" },
  { code: "digest.mismatch", message: "Renderer payload digest does not match" },
  { code: "schema.invalid", message: "Renderer input was rejected" },
  { code: "runtime.mismatch", message: "Renderer runtime does not match" },
  { code: "render.failed", message: "Renderer failed" }
] as const);

export type RendererRequest = {
  protocol_version: typeof RENDERER_PROTOCOL_VERSION;
  chart_model_b64: string;
  chart_model_sha256: string;
  render_spec_b64: string;
  render_spec_sha256: string;
};

type RendererRuntime = {
  node_version: typeof NODE_VERSION;
  echarts_version: typeof ECHARTS_VERSION;
  renderer_build_digest: string;
  render_profile_id: typeof RENDER_PROFILE_ID;
};

export type RendererSuccess = {
  protocol_version: typeof RENDERER_PROTOCOL_VERSION;
  ok: true;
  runtime: RendererRuntime;
  svg_b64: string;
};

export type RendererFailure = {
  protocol_version: typeof RENDERER_PROTOCOL_VERSION;
  ok: false;
  runtime: RendererRuntime;
  error: (typeof RENDERER_FAILURES)[number];
};

const runtimeSchema = deepFreeze({
  type: "object",
  additionalProperties: false,
  required: ["node_version", "echarts_version", "renderer_build_digest", "render_profile_id"],
  properties: {
    node_version: { type: "string", const: NODE_VERSION },
    echarts_version: { type: "string", const: ECHARTS_VERSION },
    renderer_build_digest: {
      type: "string",
      minLength: 64,
      maxLength: 64,
      pattern: SHA256_PATTERN
    },
    render_profile_id: { type: "string", const: RENDER_PROFILE_ID }
  }
} as const);

export const RENDERER_RUNTIME_SCHEMA = runtimeSchema as JSONSchemaType<RendererRuntime>;

const requestSchema = deepFreeze({
  type: "object",
  additionalProperties: false,
  required: [
    "protocol_version",
    "chart_model_b64",
    "chart_model_sha256",
    "render_spec_b64",
    "render_spec_sha256"
  ],
  properties: {
    protocol_version: { type: "string", const: RENDERER_PROTOCOL_VERSION },
    chart_model_b64: {
      type: "string",
      minLength: 1,
      maxLength: 2_796_204,
      pattern: CANONICAL_BASE64_PATTERN
    },
    chart_model_sha256: {
      type: "string",
      minLength: 64,
      maxLength: 64,
      pattern: SHA256_PATTERN
    },
    render_spec_b64: {
      type: "string",
      minLength: 1,
      maxLength: 21_848,
      pattern: CANONICAL_BASE64_PATTERN
    },
    render_spec_sha256: {
      type: "string",
      minLength: 64,
      maxLength: 64,
      pattern: SHA256_PATTERN
    }
  }
} as const);

export const RENDERER_REQUEST_SCHEMA = requestSchema as JSONSchemaType<RendererRequest>;

const failureErrorSchemas = deepFreeze(
  RENDERER_FAILURES.map(({ code, message }) => ({
    type: "object",
    additionalProperties: false,
    required: ["code", "message"],
    properties: {
      code: { type: "string", const: code },
      message: { type: "string", const: message }
    }
  }))
);

const successSchema = deepFreeze({
  type: "object",
  additionalProperties: false,
  required: ["protocol_version", "ok", "runtime", "svg_b64"],
  properties: {
    protocol_version: { type: "string", const: RENDERER_PROTOCOL_VERSION },
    ok: { type: "boolean", const: true },
    runtime: runtimeSchema,
    svg_b64: {
      type: "string",
      minLength: 1,
      maxLength: 11_184_812,
      pattern: CANONICAL_BASE64_PATTERN
    }
  }
} as const);

export const RENDERER_SUCCESS_SCHEMA = successSchema as JSONSchemaType<RendererSuccess>;

const failureSchema = deepFreeze({
  type: "object",
  additionalProperties: false,
  required: ["protocol_version", "ok", "runtime", "error"],
  properties: {
    protocol_version: { type: "string", const: RENDERER_PROTOCOL_VERSION },
    ok: { type: "boolean", const: false },
    runtime: runtimeSchema,
    error: { oneOf: failureErrorSchemas }
  }
} as const);

export const RENDERER_FAILURE_SCHEMA = failureSchema as JSONSchemaType<RendererFailure>;
