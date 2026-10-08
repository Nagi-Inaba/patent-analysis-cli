import { readFile } from "node:fs/promises";

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function compareText(left, right) {
  if (left < right) return -1;
  if (left > right) return 1;
  return 0;
}

function packageNameFromLockPath(lockPath) {
  const segments = lockPath.split("/");
  const nodeModulesIndex = segments.lastIndexOf("node_modules");
  const first = segments[nodeModulesIndex + 1];
  if (nodeModulesIndex === -1 || first === undefined) throw new Error(`Invalid lock package path: ${lockPath}`);
  if (!first.startsWith("@")) return first;
  const second = segments[nodeModulesIndex + 2];
  if (second === undefined) throw new Error(`Invalid scoped lock package path: ${lockPath}`);
  return `${first}/${second}`;
}

function purl(name, version) {
  const encodedName = name.startsWith("@")
    ? `%40${name.slice(1).split("/").map(encodeURIComponent).join("/")}`
    : encodeURIComponent(name);
  return `pkg:npm/${encodedName}@${encodeURIComponent(version)}`;
}

function cycloneDxLicense(license) {
  return /\s(?:AND|OR|WITH)\s|[()]/u.test(license)
    ? { expression: license }
    : { license: { id: license } };
}

export async function generateInventory({ packageJson, packageLock, includedLockPaths }) {
  const directProduction = new Set(Object.keys(packageJson.dependencies ?? {}));
  const directDevelopment = new Set(Object.keys(packageJson.devDependencies ?? {}));
  const included = new Set(includedLockPaths);
  const packages = [];
  const identities = new Set();
  for (const [lockPath, entry] of Object.entries(packageLock.packages ?? {})) {
    if (lockPath === "") continue;
    const name = packageNameFromLockPath(lockPath);
    const direct =
      lockPath === `node_modules/${name}` &&
      (directProduction.has(name) || directDevelopment.has(name));
    if (
      typeof entry.version !== "string" ||
      typeof entry.resolved !== "string" ||
      typeof entry.integrity !== "string" ||
      typeof entry.license !== "string"
    ) {
      throw new Error(`Incomplete inventory metadata for ${name}`);
    }
    const identity = `${name}@${entry.version}`;
    assert(!identities.has(identity), `Duplicate dependency inventory identity ${identity}`);
    identities.add(identity);
    const bundled = included.has(lockPath);
    packages.push({
      name,
      version: entry.version,
      source: entry.resolved,
      integrity: entry.integrity,
      license: entry.license,
      direct,
      transitive: !direct,
      production: entry.dev !== true,
      development: entry.dev === true,
      optional: entry.optional === true,
      bundled,
      inclusion: bundled ? "vite-module-graph" : "not-in-vite-module-graph"
    });
  }
  packages.sort((left, right) =>
    compareText(left.name, right.name) || compareText(left.version, right.version)
  );
  for (const lockPath of included) {
    assert(packageLock.packages?.[lockPath] !== undefined, `Unknown bundled lock path ${lockPath}`);
  }
  const inventory = { inventory_version: "1.0.0", packages };
  const components = packages.map((item) => ({
    type: "library",
    name: item.name,
    version: item.version,
    "bom-ref": purl(item.name, item.version),
    purl: purl(item.name, item.version),
    licenses: [cycloneDxLicense(item.license)],
    externalReferences: [{ type: "distribution", url: item.source }],
    properties: [
      { name: "npm:integrity", value: item.integrity },
      { name: "patent-analysis:direct", value: String(item.direct) },
      { name: "patent-analysis:transitive", value: String(item.transitive) },
      { name: "patent-analysis:production", value: String(item.production) },
      { name: "patent-analysis:development", value: String(item.development) },
      { name: "patent-analysis:optional", value: String(item.optional) },
      { name: "patent-analysis:bundled", value: String(item.bundled) },
      { name: "patent-analysis:inclusion", value: item.inclusion }
    ]
  }));
  const sbom = {
    bomFormat: "CycloneDX",
    specVersion: "1.6",
    version: 1,
    metadata: {
      component: {
        type: "application",
        name: packageJson.name,
        version: packageJson.version
      }
    },
    components
  };
  assert(new Set(components.map((component) => component["bom-ref"])).size === components.length, "Duplicate SBOM bom-ref");
  assert(new Set(components.map((component) => component.purl)).size === components.length, "Duplicate SBOM purl");
  return { inventory, sbom };
}

export async function readBuildInputs(rendererRoot) {
  const [packageJson, packageLock] = await Promise.all([
    readFile(new URL("../package.json", import.meta.url), "utf8").then(JSON.parse),
    readFile(new URL("../package-lock.json", import.meta.url), "utf8").then(JSON.parse)
  ]);
  return { packageJson, packageLock, rendererRoot };
}
