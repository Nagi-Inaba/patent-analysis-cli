import { readFile } from "node:fs/promises";
import { Ajv } from "ajv";
import { describe, expect, it } from "vitest";

const SHA256 = "a".repeat(64);

async function loadContracts() {
  const modulePath = "../src/contracts.ts";
  return import(modulePath);
}

async function loadLockVerifier() {
  const modulePath = "../scripts/verify-lock.mjs";
  return import(modulePath);
}

function requestFixture() {
  return {
    protocol_version: "1.0.0",
    chart_model_b64: "e30=",
    chart_model_sha256: SHA256,
    render_spec_b64: "e30=",
    render_spec_sha256: SHA256
  };
}

function runtimeFixture() {
  return {
    node_version: "22.19.0",
    echarts_version: "6.1.0",
    renderer_build_digest: SHA256,
    render_profile_id: "ranking-svg-ja-jp-node22-echarts6.v1"
  };
}

function isDeepFrozen(value: unknown, seen = new Set<object>()): boolean {
  if (value === null || typeof value !== "object") return true;
  if (seen.has(value)) return true;
  if (!Object.isFrozen(value)) return false;
  seen.add(value);
  return Reflect.ownKeys(value).every((key) => isDeepFrozen(value[key as keyof typeof value], seen));
}

describe("renderer protocol contract", () => {
  it("pins the exact ten direct dependencies", async () => {
    const packageJson = JSON.parse(
      await readFile(new URL("../package.json", import.meta.url), "utf8")
    ) as { dependencies: Record<string, string>; devDependencies: Record<string, string> };

    expect({ ...packageJson.dependencies, ...packageJson.devDependencies }).toEqual({
      "@xmldom/xmldom": "0.9.12",
      ajv: "8.20.0",
      echarts: "6.1.0",
      "@eslint/js": "10.0.1",
      "@types/node": "22.20.1",
      eslint: "10.8.1",
      typescript: "5.9.3",
      "typescript-eslint": "8.67.0",
      vite: "8.2.1",
      vitest: "4.1.11"
    });
    expect(packageJson.dependencies).toEqual({
      "@xmldom/xmldom": "0.9.12",
      ajv: "8.20.0",
      echarts: "6.1.0"
    });
  });

  it("exports the literal closed protocol contract", async () => {
    const contracts = await loadContracts();

    expect(contracts).toEqual(
      expect.objectContaining({
        RENDERER_PROTOCOL_VERSION: "1.0.0",
        RENDERER_FAILURES: [
          { code: "protocol.invalid", message: "Renderer protocol is invalid" },
          { code: "payload.too_large", message: "Renderer payload is too large" },
          { code: "digest.mismatch", message: "Renderer payload digest does not match" },
          { code: "schema.invalid", message: "Renderer input was rejected" },
          { code: "runtime.mismatch", message: "Renderer runtime does not match" },
          { code: "render.failed", message: "Renderer failed" }
        ]
      })
    );
  });

  it("compiles schemas and rejects malformed scalar, base64, budget, and runtime values", async () => {
    const contracts = await loadContracts();
    const ajv = new Ajv({ strict: false });
    const validateRequest = ajv.compile(contracts.RENDERER_REQUEST_SCHEMA);
    const validateSuccess = ajv.compile(contracts.RENDERER_SUCCESS_SCHEMA);
    const validateFailure = ajv.compile(contracts.RENDERER_FAILURE_SCHEMA);

    expect(validateRequest(requestFixture())).toBe(true);
    expect(validateSuccess({
      protocol_version: "1.0.0",
      ok: true,
      runtime: runtimeFixture(),
      svg_b64: "PHN2Zy8+"
    })).toBe(true);

    expect(validateRequest({ ...requestFixture(), extra: true })).toBe(false);
    expect(validateRequest({ ...requestFixture(), chart_model_sha256: "A".repeat(64) })).toBe(false);
    expect(validateRequest({ ...requestFixture(), render_spec_sha256: "a".repeat(63) })).toBe(false);
    expect(validateRequest({ ...requestFixture(), chart_model_b64: "TQ" })).toBe(false);
    expect(validateRequest({ ...requestFixture(), chart_model_b64: "TQ===" })).toBe(false);
    expect(validateRequest({ ...requestFixture(), chart_model_b64: "T Q==" })).toBe(false);
    expect(validateRequest({ ...requestFixture(), chart_model_b64: "***=" })).toBe(false);
    expect(validateRequest({ ...requestFixture(), chart_model_b64: "A".repeat(2_796_205) })).toBe(false);
    expect(validateRequest({ ...requestFixture(), render_spec_b64: "A".repeat(21_849) })).toBe(false);

    expect(validateSuccess({
      protocol_version: "1.0.0",
      ok: true,
      runtime: { ...runtimeFixture(), node_version: "v22.19.0" },
      svg_b64: "PHN2Zy8+"
    })).toBe(false);
    expect(validateSuccess({
      protocol_version: "1.0.0",
      ok: true,
      runtime: { ...runtimeFixture(), render_profile_id: "wrong-profile" },
      svg_b64: "PHN2Zy8+"
    })).toBe(false);
    expect(validateSuccess({
      protocol_version: "1.0.0",
      ok: true,
      runtime: { ...runtimeFixture(), renderer_build_digest: "b".repeat(64) },
      svg_b64: "A".repeat(11_184_813)
    })).toBe(false);
    expect(validateFailure({
      protocol_version: "1.0.0",
      ok: false,
      runtime: { ...runtimeFixture(), echarts_version: "6.0.0" },
      error: { code: "protocol.invalid", message: "Renderer protocol is invalid" }
    })).toBe(false);
  });

  it("rejects a noncanonical two-byte base64 quantum", async () => {
    const contracts = await loadContracts();
    const validateRequest = new Ajv({ strict: false }).compile(contracts.RENDERER_REQUEST_SCHEMA);

    expect(validateRequest({ ...requestFixture(), chart_model_b64: "AB==" })).toBe(false);
  });

  it("rejects a noncanonical three-byte base64 quantum", async () => {
    const contracts = await loadContracts();
    const validateRequest = new Ajv({ strict: false }).compile(contracts.RENDERER_REQUEST_SCHEMA);

    expect(validateRequest({ ...requestFixture(), chart_model_b64: "AAB=" })).toBe(false);
  });

  it("rejects base64 with a terminal newline", async () => {
    const contracts = await loadContracts();
    const validateRequest = new Ajv({ strict: false }).compile(contracts.RENDERER_REQUEST_SCHEMA);

    expect(validateRequest({ ...requestFixture(), chart_model_b64: "TQ==\n" })).toBe(false);
  });

  it("rejects a SHA-256 value with a terminal newline", async () => {
    const contracts = await loadContracts();
    const validateRequest = new Ajv({ strict: false }).compile(contracts.RENDERER_REQUEST_SCHEMA);

    expect(validateRequest({ ...requestFixture(), chart_model_sha256: `${SHA256}\n` })).toBe(false);
  });

  it("continues to accept canonical padded base64", async () => {
    const contracts = await loadContracts();
    const validateRequest = new Ajv({ strict: false }).compile(contracts.RENDERER_REQUEST_SCHEMA);

    expect(validateRequest({ ...requestFixture(), chart_model_b64: "AA==" })).toBe(true);
    expect(validateRequest({ ...requestFixture(), chart_model_b64: "AAA=" })).toBe(true);
  });

  it("accepts only the six exact failure pairs and exact response shapes", async () => {
    const contracts = await loadContracts();
    const ajv = new Ajv({ strict: false });
    const validateFailure = ajv.compile(contracts.RENDERER_FAILURE_SCHEMA);

    for (const error of contracts.RENDERER_FAILURES) {
      expect(validateFailure({
        protocol_version: "1.0.0",
        ok: false,
        runtime: runtimeFixture(),
        error
      })).toBe(true);
    }

    expect(validateFailure({
      protocol_version: "1.0.0",
      ok: false,
      runtime: runtimeFixture(),
      error: { code: "protocol.invalid", message: "Renderer failed" }
    })).toBe(false);
    expect(validateFailure({
      protocol_version: "1.0.0",
      ok: false,
      runtime: runtimeFixture(),
      error: { code: "protocol.invalid", message: "Renderer protocol is invalid" },
      extra: true
    })).toBe(false);
  });

  it("recursively freezes each exported schema graph", async () => {
    const contracts = await loadContracts();

    expect(isDeepFrozen(contracts.RENDERER_REQUEST_SCHEMA)).toBe(true);
    expect(isDeepFrozen(contracts.RENDERER_RUNTIME_SCHEMA)).toBe(true);
    expect(isDeepFrozen(contracts.RENDERER_SUCCESS_SCHEMA)).toBe(true);
    expect(isDeepFrozen(contracts.RENDERER_FAILURE_SCHEMA)).toBe(true);
  });

  it("keeps generated request/runtime validation aligned with the closed contract", async () => {
    const generatedPath = "../src/generated/standalone-validators.js";
    const generated = await import(generatedPath);

    expect(generated.validateRendererRequest(requestFixture())).toBe(true);
    expect(generated.validateRendererRuntime(runtimeFixture())).toBe(true);
    expect(generated.validateRendererRequest({ ...requestFixture(), extra: true })).toBe(false);
    expect(generated.validateRendererRuntime({
      ...runtimeFixture(),
      renderer_build_digest: "A".repeat(64)
    })).toBe(false);
  });
});

describe("renderer lock verifier", () => {
  it("exports a pure lock validator for in-memory mutation tests", async () => {
    const verifier = await loadLockVerifier();

    expect(verifier).toEqual(expect.objectContaining({ validateLockData: expect.any(Function) }));
  });

  it("rejects wrong tarballs, malformed integrity, category swaps, and inventory drift", async () => {
    const verifier = await loadLockVerifier();
    if (typeof verifier.validateLockData !== "function") return;

    const packageJson = JSON.parse(await readFile(new URL("../package.json", import.meta.url), "utf8"));
    const packageLock = JSON.parse(await readFile(new URL("../package-lock.json", import.meta.url), "utf8"));
    const mutate = () => structuredClone(packageLock);
    const xmldomPath = "node_modules/@xmldom/xmldom";

    expect(() => verifier.validateLockData(packageJson, packageLock)).not.toThrow();

    for (const resolved of [
      "https://example.invalid/@xmldom/xmldom/-/xmldom-0.9.12.tgz",
      "https://user:pass@registry.npmjs.org/@xmldom/xmldom/-/xmldom-0.9.12.tgz",
      "https://registry.npmjs.org:443/@xmldom/xmldom/-/xmldom-0.9.12.tgz",
      "https://registry.npmjs.org/@xmldom/xmldom/-/xmldom-0.9.12.tgz?cache=1",
      "https://registry.npmjs.org/@xmldom/xmldom/-/xmldom-0.9.12.tgz#fragment",
      "https://registry.npmjs.org/@xmldom/xmldom/-/xmldom-9.9.9.tgz"
    ]) {
      const lock = mutate();
      lock.packages[xmldomPath].resolved = resolved;
      expect(() => verifier.validateLockData(packageJson, lock)).toThrow();
    }

    const versionDrift = mutate();
    versionDrift.packages[xmldomPath].version = "9.9.9";
    versionDrift.packages[xmldomPath].resolved =
      "https://registry.npmjs.org/@xmldom/xmldom/-/xmldom-9.9.9.tgz";
    expect(() => verifier.validateLockData(packageJson, versionDrift)).toThrow();

    const malformedIntegrity = mutate();
    malformedIntegrity.packages[xmldomPath].integrity = "sha512-not-base64";
    expect(() => verifier.validateLockData(packageJson, malformedIntegrity)).toThrow();

    const categorySwap = mutate();
    delete categorySwap.packages[""].dependencies.echarts;
    categorySwap.packages[""].devDependencies.echarts = "6.1.0";
    expect(() => verifier.validateLockData(packageJson, categorySwap)).toThrow();

    const packageCategorySwap = structuredClone(packageJson);
    delete packageCategorySwap.dependencies.echarts;
    packageCategorySwap.devDependencies.echarts = "6.1.0";
    expect(() => verifier.validateLockData(packageCategorySwap, packageLock)).toThrow();

    const inventoryDrift = mutate();
    const directPaths = new Set(
      Object.keys({ ...packageJson.dependencies, ...packageJson.devDependencies }).map(
        (name) => `node_modules/${name}`
      )
    );
    const transitivePath = Object.keys(inventoryDrift.packages).find(
      (path) => path !== "" && !directPaths.has(path)
    );
    if (transitivePath === undefined) throw new Error("Expected a transitive package entry");
    inventoryDrift.packages[transitivePath].integrity = `sha512-${Buffer.alloc(64, 7).toString("base64")}`;
    expect(() => verifier.validateLockData(packageJson, inventoryDrift)).toThrow();
  });
});
