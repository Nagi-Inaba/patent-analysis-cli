import { createHash } from "node:crypto";
import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const rendererRoot = dirname(fileURLToPath(new URL("../package.json", import.meta.url)));
const packageRoot = join(rendererRoot, "..", "src", "patent_analysis", "renderer");
const paths = {
  bootstrap: join(packageRoot, "bootstrap.js"),
  bundle: join(packageRoot, "renderer.bundle.js"),
  manifest: join(packageRoot, "renderer-build-manifest.json"),
  inventory: join(packageRoot, "dependency-inventory.json"),
  sbom: join(packageRoot, "sbom.cdx.json"),
  workspaceInventory: join(rendererRoot, "THIRD_PARTY_INVENTORY.json"),
  workspaceSbom: join(rendererRoot, "SBOM.cdx.json")
};
const MAX_BUNDLE_BYTES = 4 * 1024 * 1024;
const BUILD_ONLY = [
  "@eslint/js",
  "@types/node",
  "eslint",
  "typescript",
  "typescript-eslint",
  "vite",
  "vitest"
];
const APPROVED_BUNDLED_IDENTITIES = new Set([
  "@xmldom/xmldom@0.9.12",
  "echarts@6.1.0",
  "tslib@2.3.0",
  "zrender@6.1.0"
]);

type InventoryItem = {
  name: string;
  version: string;
  source: string;
  integrity: string;
  license: string;
  direct: boolean;
  transitive: boolean;
  production: boolean;
  development: boolean;
  optional: boolean;
  bundled: boolean;
  inclusion: string;
};

type SbomComponent = {
  type: string;
  name: string;
  version: string;
  "bom-ref": string;
  purl: string;
  licenses: Array<{ expression?: string; license?: { id: string } }>;
  externalReferences: Array<{ type: string; url: string }>;
  properties: Array<{ name: string; value: string }>;
};

function sha256(bytes: string | Buffer): string {
  return createHash("sha256").update(bytes).digest("hex");
}

function packageNameFromLockPath(lockPath: string) {
  const segments = lockPath.split("/");
  const index = segments.lastIndexOf("node_modules");
  const first = segments[index + 1];
  if (index < 0 || first === undefined) throw new Error(`Invalid lock path ${lockPath}`);
  if (!first.startsWith("@")) return first;
  const second = segments[index + 2];
  if (second === undefined) throw new Error(`Invalid scoped lock path ${lockPath}`);
  return `${first}/${second}`;
}

function expectedPurl(name: string, version: string) {
  const encodedName = name.startsWith("@")
    ? `%40${name.slice(1).split("/").map(encodeURIComponent).join("/")}`
    : encodeURIComponent(name);
  return `pkg:npm/${encodedName}@${encodeURIComponent(version)}`;
}

describe("self-contained renderer build", () => {
  it("emits every required deterministic build output", () => {
    const missing = Object.values(paths).filter((path) => !existsSync(path));

    expect(missing).toEqual([]);
  });

  it("pins exact bootstrap and bundle bytes in the strict seven-field manifest", async () => {
    if (![paths.bootstrap, paths.bundle, paths.manifest].every(existsSync)) return;
    const [bootstrap, bundle, manifestText] = await Promise.all([
      readFile(paths.bootstrap),
      readFile(paths.bundle),
      readFile(paths.manifest, "utf8")
    ]);
    const manifest = JSON.parse(manifestText) as Record<string, unknown>;

    expect(manifest).toEqual({
      bootstrap_sha256: sha256(bootstrap),
      build_tool_id: "patent-analysis.renderer-bundler",
      build_tool_version: "1.0.0",
      echarts_version: "6.1.0",
      renderer_build_manifest_version: "1.0.0",
      renderer_bundle_sha256: sha256(bundle),
      renderer_protocol_version: "1.0.0"
    });
    expect(bootstrap.byteLength).toBeGreaterThan(0);
    expect(bundle.byteLength).toBeLessThanOrEqual(MAX_BUNDLE_BYTES);
  });

  it("rejects non-exact manifests, oversized bundles, and altered artifact bytes", async () => {
    if (![paths.bootstrap, paths.bundle, paths.manifest].every(existsSync)) return;
    const verifierPath = "../scripts/build-bundle.mjs";
    const verifier = await import(verifierPath) as {
      validateBuildArtifacts: (
        bootstrap: Buffer,
        bundle: Buffer,
        manifest: Record<string, unknown>
      ) => void;
    };
    const [bootstrap, bundle, manifestText] = await Promise.all([
      readFile(paths.bootstrap),
      readFile(paths.bundle),
      readFile(paths.manifest, "utf8")
    ]);
    const manifest = JSON.parse(manifestText) as Record<string, unknown>;

    expect(() => verifier.validateBuildArtifacts(bootstrap, bundle, manifest)).not.toThrow();
    expect(() => verifier.validateBuildArtifacts(bootstrap, bundle, { ...manifest, extra: true })).toThrow();
    expect(() => verifier.validateBuildArtifacts(bootstrap, Buffer.alloc(MAX_BUNDLE_BYTES + 1), manifest)).toThrow();
    expect(() => verifier.validateBuildArtifacts(Buffer.concat([bootstrap, Buffer.from(";")]), bundle, manifest)).toThrow();
    expect(() => verifier.validateBuildArtifacts(bootstrap, Buffer.concat([bundle, Buffer.from(";")]), manifest)).toThrow();
  });

  it("rejects raw, computed, and executable capability markers", async () => {
    if (!existsSync(paths.bundle)) return;
    const verifierPath = "../scripts/build-bundle.mjs";
    const verifier = await import(verifierPath) as { validateRuntimeBundle: (bundle: Buffer) => void };
    const bundle = await readFile(paths.bundle);
    const forbiddenFixtures = [
      'import("./runtime.js")',
      'require("./runtime.js")',
      'require("echarts")',
      'globalThis["fetch"]',
      'globalThis["f"+"etch"]',
      'globalThis["f\\x65"+"tch"]',
      'globalThis["pro"+"cess"]',
      'globalThis["Function"]("return this")()',
      'process["std"+"out"].write("x")',
      'process.getBuiltinModule("node:fs")',
      'process.stderr.write("x")',
      'Function("return this")()',
      '(0,eval)("x")',
      '({})["constr"+"uctor"]["constructor"]("return this")()',
      '"node:child_process"',
      '"https://cdn.example.invalid/runtime.js"',
      "fetch('https://example.invalid')",
      'new WebSocket("wss://example.invalid")',
      "new XMLHttpRequest()",
      "node_modules/echarts/index.js"
    ];

    expect(() => verifier.validateRuntimeBundle(bundle)).not.toThrow();
    expect(() => verifier.validateRuntimeBundle(
      Buffer.from('"http://www.w3.org/1999/xlink"', "utf8")
    )).not.toThrow();
    for (const marker of forbiddenFixtures) {
      expect(() => verifier.validateRuntimeBundle(Buffer.from(marker))).toThrow();
    }
  });

  it("accepts only the renderer entry, four approved lock paths, and exact Rolldown helper", async () => {
    const verifierPath = "../scripts/build-bundle.mjs";
    const verifier = await import(verifierPath) as {
      validateModuleGraph?: (input: {
        moduleIds: string[];
        rendererRoot: string;
        packageLock: { packages: Record<string, unknown> };
      }) => string[];
    };
    const packageLock = JSON.parse(
      await readFile(join(rendererRoot, "package-lock.json"), "utf8")
    ) as { packages: Record<string, unknown> };
    const approvedModules = [
      "\0rolldown/runtime.js",
      join(rendererRoot, "src", "index.ts"),
      join(rendererRoot, "src", "palette.ts"),
      join(rendererRoot, "src", "payload.ts"),
      join(rendererRoot, "src", "svg-normalize.ts"),
      join(rendererRoot, "src", "generated", "standalone-validators.js"),
      join(rendererRoot, "node_modules", "@xmldom", "xmldom", "lib", "index.js"),
      join(rendererRoot, "node_modules", "echarts", "lib", "core", "echarts.js"),
      join(rendererRoot, "node_modules", "tslib", "tslib.es6.js"),
      join(rendererRoot, "node_modules", "zrender", "lib", "zrender.js")
    ];

    expect(verifier.validateModuleGraph).toBeTypeOf("function");
    if (typeof verifier.validateModuleGraph !== "function") return;
    expect(verifier.validateModuleGraph({
      moduleIds: approvedModules,
      rendererRoot,
      packageLock
    })).toEqual([
      "node_modules/@xmldom/xmldom",
      "node_modules/echarts",
      "node_modules/tslib",
      "node_modules/zrender"
    ]);

    for (const rejected of [
      "\0unexpected/virtual.js",
      "node:fs",
      join(rendererRoot, "src", "contracts.ts"),
      join(rendererRoot, "node_modules", "ajv", "dist", "ajv.js"),
      "node_modules/echarts/lib/core/echarts.js",
      join(rendererRoot, "..", "outside.js")
    ]) {
      expect(() => verifier.validateModuleGraph?.({
        moduleIds: [...approvedModules, rejected],
        rendererRoot,
        packageLock
      })).toThrow();
    }
    for (const requiredModule of [
      "\0rolldown/runtime.js",
      join(rendererRoot, "src", "index.ts"),
      join(rendererRoot, "src", "palette.ts"),
      join(rendererRoot, "src", "payload.ts"),
      join(rendererRoot, "src", "svg-normalize.ts"),
      join(rendererRoot, "src", "generated", "standalone-validators.js"),
      join(rendererRoot, "node_modules", "zrender", "lib", "zrender.js")
    ]) {
      expect(() => verifier.validateModuleGraph?.({
        moduleIds: approvedModules.filter((moduleId) => moduleId !== requiredModule),
        rendererRoot,
        packageLock
      })).toThrow();
    }
  });

  it("generates deterministic complete inventory and SBOM with module-graph inclusion", async () => {
    if (![paths.inventory, paths.sbom, paths.workspaceInventory, paths.workspaceSbom].every(existsSync)) return;
    const [inventoryBytes, packagedInventoryBytes, sbomBytes, packagedSbomBytes, lockText] = await Promise.all([
      readFile(paths.workspaceInventory),
      readFile(paths.inventory),
      readFile(paths.workspaceSbom),
      readFile(paths.sbom),
      readFile(join(rendererRoot, "package-lock.json"), "utf8")
    ]);
    const inventory = JSON.parse(inventoryBytes.toString("utf8")) as { packages: InventoryItem[] };
    const sbom = JSON.parse(sbomBytes.toString("utf8")) as {
      bomFormat: string;
      specVersion: string;
      components: SbomComponent[];
    };
    const lock = JSON.parse(lockText) as {
      packages: Record<string, { version?: string }>;
    };
    const packageJson = JSON.parse(
      await readFile(join(rendererRoot, "package.json"), "utf8")
    ) as { dependencies: Record<string, string>; devDependencies: Record<string, string> };
    const serialized = `${inventoryBytes.toString("utf8")}\n${sbomBytes.toString("utf8")}`;
    const directVersions = { ...packageJson.dependencies, ...packageJson.devDependencies };
    const expectedDirectByIdentity = new Map(
      Object.entries(lock.packages)
        .filter(([lockPath, entry]) => lockPath !== "" && typeof entry.version === "string")
        .map(([lockPath, entry]) => {
          const name = packageNameFromLockPath(lockPath);
          const identity = `${name}@${entry.version}`;
          return [
            identity,
            lockPath === `node_modules/${name}` && directVersions[name] === entry.version
          ] as const;
        })
    );

    expect(packagedInventoryBytes.equals(inventoryBytes)).toBe(true);
    expect(packagedSbomBytes.equals(sbomBytes)).toBe(true);
    expect(inventory.packages).toHaveLength(Object.keys(lock.packages).length - 1);
    expect(inventory.packages.filter((item) => item.direct)).toHaveLength(10);
    expect(inventory.packages).toContainEqual(expect.objectContaining({
      name: "ajv",
      version: "6.15.0",
      direct: false,
      transitive: true
    }));
    expect(sbom).toMatchObject({ bomFormat: "CycloneDX", specVersion: "1.6" });
    expect(sbom.components).toHaveLength(inventory.packages.length);
    expect(sbom.components.some((component) => component.name.includes("sharp"))).toBe(false);
    expect(serialized).not.toMatch(/(?:timestamp|serialNumber|[A-Za-z]:\\|\/Users\/|hostname)/u);
    const inventoryIdentities = inventory.packages.map((item) => `${item.name}@${item.version}`);
    expect(new Set(inventoryIdentities).size).toBe(inventoryIdentities.length);
    const sbomRefs = sbom.components.map((component) => component["bom-ref"]);
    const sbomPurls = sbom.components.map((component) => component.purl);
    expect(new Set(sbomRefs).size).toBe(sbomRefs.length);
    expect(new Set(sbomPurls).size).toBe(sbomPurls.length);

    const sbomByIdentity = new Map(
      sbom.components.map((component) => [`${component.name}@${component.version}`, component])
    );
    expect(new Set(sbomByIdentity.keys())).toEqual(new Set(inventoryIdentities));
    for (const item of inventory.packages) {
      const identity = `${item.name}@${item.version}`;
      expect(Object.keys(item).sort()).toEqual([
        "bundled",
        "development",
        "direct",
        "inclusion",
        "integrity",
        "license",
        "name",
        "optional",
        "production",
        "source",
        "transitive",
        "version"
      ]);
      expect(item.source).toMatch(/^https:\/\/registry\.npmjs\.org\//u);
      expect(item.integrity).toMatch(/^sha512-[A-Za-z0-9+/]+={0,2}$/u);
      expect(item.license.length).toBeGreaterThan(0);
      for (const flag of [
        item.direct,
        item.transitive,
        item.production,
        item.development,
        item.optional,
        item.bundled
      ]) expect(typeof flag).toBe("boolean");
      expect(item.direct).not.toBe(item.transitive);
      expect(item.direct).toBe(expectedDirectByIdentity.get(identity));
      const expectedBundled = APPROVED_BUNDLED_IDENTITIES.has(identity);
      expect(item.bundled).toBe(expectedBundled);
      expect(item.inclusion).toBe(expectedBundled ? "vite-module-graph" : "not-in-vite-module-graph");

      const component = sbomByIdentity.get(identity);
      expect(component).toBeDefined();
      if (component === undefined) continue;
      expect(Object.keys(component).sort()).toEqual([
        "bom-ref",
        "externalReferences",
        "licenses",
        "name",
        "properties",
        "purl",
        "type",
        "version"
      ]);
      expect(component.type).toBe("library");
      expect(component.purl).toBe(expectedPurl(item.name, item.version));
      expect(component["bom-ref"]).toBe(component.purl);
      expect(component.externalReferences).toEqual([{ type: "distribution", url: item.source }]);
      expect(component.licenses).toHaveLength(1);
      const recordedLicense = component.licenses[0]?.expression ?? component.licenses[0]?.license?.id;
      expect(recordedLicense).toBe(item.license);
      expect(component.properties).toHaveLength(8);
      expect(new Set(component.properties.map(({ name }) => name)).size).toBe(8);
      expect(Object.fromEntries(component.properties.map(({ name, value }) => [name, value]))).toEqual({
        "npm:integrity": item.integrity,
        "patent-analysis:direct": String(item.direct),
        "patent-analysis:transitive": String(item.transitive),
        "patent-analysis:production": String(item.production),
        "patent-analysis:development": String(item.development),
        "patent-analysis:optional": String(item.optional),
        "patent-analysis:bundled": String(item.bundled),
        "patent-analysis:inclusion": item.inclusion
      });
    }
    expect(inventory.packages).toContainEqual(expect.objectContaining({
      name: "ajv",
      version: "8.20.0",
      bundled: false,
      inclusion: "not-in-vite-module-graph"
    }));
    for (const dependency of BUILD_ONLY) {
      expect(inventory.packages).toContainEqual(expect.objectContaining({
        name: dependency,
        bundled: false,
        inclusion: "not-in-vite-module-graph"
      }));
    }
  });

  it("keeps build-only tools out of the runtime bundle bytes", async () => {
    if (!existsSync(paths.bundle)) return;
    const bundle = await readFile(paths.bundle, "utf8");

    for (const marker of ["@eslint/js", "@types/node", "typescript-eslint", "sharp@", "vitest"]) {
      expect(bundle).not.toContain(marker);
    }
  });

  it("keeps AJV code generation outside both generated source and the runtime bundle", async () => {
    const [generated, bundle] = await Promise.all([
      readFile(join(rendererRoot, "src", "generated", "standalone-validators.js"), "utf8"),
      readFile(paths.bundle, "utf8")
    ]);

    for (const source of [generated, bundle]) {
      expect(source).not.toMatch(/\brequire\s*\(|ajv\/dist|node_modules[\\/]ajv|\bFunction\s*\(/u);
    }
  });
});
