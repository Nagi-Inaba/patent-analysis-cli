import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const EXPECTED_NODE_VERSION = "v22.19.0";
const EXPECTED_NPM_VERSION = "10.9.3";
const EXPECTED_PRODUCTION_DEPENDENCIES = Object.freeze({
  "@xmldom/xmldom": "0.9.12",
  ajv: "8.20.0",
  echarts: "6.1.0"
});
const EXPECTED_DEVELOPMENT_DEPENDENCIES = Object.freeze({
  "@eslint/js": "10.0.1",
  "@types/node": "22.20.1",
  eslint: "10.8.1",
  typescript: "5.9.3",
  "typescript-eslint": "8.67.0",
  vite: "8.3.4",
  vitest: "4.1.11"
});
const EXPECTED_TRANSITIVE_INVENTORY_SHA256 = "5c96a9ecc5dc25f12d0edc6d0815fda7d7d4f6525d56d10732d2b4f4eeac4460";
const EXPECTED_LOCK_INSTALL_SCRIPT_PACKAGES = Object.freeze({ fsevents: "2.3.3" });
const SHA512_BASE64_PATTERN = /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/;

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function compareText(left, right) {
  if (left < right) return -1;
  if (left > right) return 1;
  return 0;
}

function packagePath(name) {
  return `node_modules/${name}`;
}

function packageNameFromPath(path) {
  const segments = path.split("/");
  const nodeModulesIndex = segments.lastIndexOf("node_modules");
  const firstNameSegment = segments[nodeModulesIndex + 1];
  if (nodeModulesIndex === -1 || firstNameSegment === undefined) return undefined;
  if (firstNameSegment.startsWith("@")) {
    const secondNameSegment = segments[nodeModulesIndex + 2];
    return secondNameSegment === undefined ? undefined : `${firstNameSegment}/${secondNameSegment}`;
  }
  return firstNameSegment;
}

function tarballFileName(name, version) {
  return `${name.startsWith("@") ? name.slice(name.indexOf("/") + 1) : name}-${version}.tgz`;
}

function canonicalTarballUrl(name, version) {
  return `https://registry.npmjs.org/${name}/-/${tarballFileName(name, version)}`;
}

function hasStrictSha512Integrity(integrity) {
  if (typeof integrity !== "string" || !integrity.startsWith("sha512-")) return false;
  const encoded = integrity.slice("sha512-".length);
  if (!SHA512_BASE64_PATTERN.test(encoded) || encoded.length === 0) return false;
  const decoded = Buffer.from(encoded, "base64");
  return decoded.byteLength === 64 && decoded.toString("base64") === encoded;
}

function validateRegistryEntry(name, entry) {
  assert(entry && typeof entry === "object", `Expected ${name} package entry`);
  assert(typeof entry.version === "string" && entry.version.length > 0, `Expected ${name} package version`);
  assert(typeof entry.resolved === "string", `Expected ${name} tarball URL`);
  const expectedUrl = canonicalTarballUrl(name, entry.version);
  assert(entry.resolved === expectedUrl, `Expected ${name} canonical tarball URL ${expectedUrl}`);
  assert(hasStrictSha512Integrity(entry.integrity), `Expected ${name} strict sha512 integrity`);
}

function assertExactDependencyCategory(actual, expected, category) {
  assert(actual && typeof actual === "object", `Expected ${category} dependency category`);
  const actualEntries = Object.entries(actual).sort(([left], [right]) => compareText(left, right));
  const expectedEntries = Object.entries(expected).sort(([left], [right]) => compareText(left, right));
  assert(
    JSON.stringify(actualEntries) === JSON.stringify(expectedEntries),
    `Expected exact ${category} dependency category`
  );
}

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value)
        .sort(([left], [right]) => compareText(left, right))
        .map(([key, nestedValue]) => [key, canonicalize(nestedValue)])
    );
  }
  return value;
}

export function calculateTransitiveInventorySha256(packageLock) {
  const packageEntries = Object.entries(packageLock.packages ?? {})
    .filter(([path]) => path !== "")
    .sort(([left], [right]) => compareText(left, right));
  const canonicalInventory = canonicalize(Object.fromEntries(packageEntries));
  return createHash("sha256").update(JSON.stringify(canonicalInventory), "utf8").digest("hex");
}

export function validateLockData(packageJson, packageLock) {
  assert(packageLock?.lockfileVersion === 3, "Expected lockfileVersion 3");
  assertExactDependencyCategory(packageJson?.dependencies, EXPECTED_PRODUCTION_DEPENDENCIES, "production");
  assertExactDependencyCategory(packageJson?.devDependencies, EXPECTED_DEVELOPMENT_DEPENDENCIES, "development");

  const rootPackage = packageLock.packages?.[""];
  assertExactDependencyCategory(rootPackage?.dependencies, EXPECTED_PRODUCTION_DEPENDENCIES, "root production");
  assertExactDependencyCategory(rootPackage?.devDependencies, EXPECTED_DEVELOPMENT_DEPENDENCIES, "root development");
  for (const lifecycleName of ["preinstall", "install", "postinstall", "prepare"]) {
    assert(packageJson?.scripts?.[lifecycleName] === undefined, `Unexpected root ${lifecycleName} lifecycle script`);
  }

  for (const [name, version] of Object.entries({
    ...EXPECTED_PRODUCTION_DEPENDENCIES,
    ...EXPECTED_DEVELOPMENT_DEPENDENCIES
  })) {
    const entry = packageLock.packages?.[packagePath(name)];
    assert(entry?.version === version, `Expected ${name} exact lock version ${version}`);
    validateRegistryEntry(name, entry);
  }

  for (const [path, entry] of Object.entries(packageLock.packages ?? {})) {
    if (path === "") continue;
    const name = packageNameFromPath(path);
    assert(name !== undefined, `Expected package name for ${path}`);
    validateRegistryEntry(name, entry);
  }

  const lockInstallScripts = Object.entries(packageLock.packages ?? {})
    .filter(([path, entry]) => path !== "" && entry.hasInstallScript === true)
    .map(([path, entry]) => [packageNameFromPath(path), entry.version])
    .sort(([left], [right]) => compareText(left, right));
  assert(
    JSON.stringify(lockInstallScripts) === JSON.stringify(Object.entries(EXPECTED_LOCK_INSTALL_SCRIPT_PACKAGES)),
    "Expected exact transitive lock lifecycle inventory"
  );

  const inventorySha256 = calculateTransitiveInventorySha256(packageLock);
  assert(
    inventorySha256 === EXPECTED_TRANSITIVE_INVENTORY_SHA256,
    "Expected exact transitive package inventory SHA-256"
  );
  return inventorySha256;
}

async function npmVersion() {
  const command = process.platform === "win32" ? "npm.cmd" : "npm";
  return new Promise((resolve, reject) => {
    const child = spawn(command, ["--version"], {
      shell: process.platform === "win32",
      stdio: ["ignore", "pipe", "pipe"]
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) {
        resolve(stdout.trim());
      } else {
        reject(new Error(`npm --version failed: ${stderr.trim()}`));
      }
    });
  });
}

async function main() {
  assert(process.version === EXPECTED_NODE_VERSION, `Expected Node ${EXPECTED_NODE_VERSION}, received ${process.version}`);
  assert(await npmVersion() === EXPECTED_NPM_VERSION, `Expected npm ${EXPECTED_NPM_VERSION}`);
  const packageJson = JSON.parse(await readFile(new URL("../package.json", import.meta.url)));
  const packageLock = JSON.parse(await readFile(new URL("../package-lock.json", import.meta.url)));
  validateLockData(packageJson, packageLock);
  console.log("renderer lock verified");
}

if (process.argv[1] !== undefined && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await main();
}
