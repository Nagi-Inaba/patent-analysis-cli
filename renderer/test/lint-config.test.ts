import { spawnSync } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const rendererRoot = dirname(fileURLToPath(new URL("../package.json", import.meta.url)));
const eslintCli = join(rendererRoot, "node_modules", "eslint", "bin", "eslint.js");

function eslint(args: string[]) {
  return spawnSync(process.execPath, [eslintCli, ...args], {
    cwd: rendererRoot,
    encoding: "utf8"
  });
}

describe("renderer ESLint configuration", () => {
  it("activates official JavaScript and TypeScript recommended rule paths", { timeout: 20_000 }, () => {
    for (const file of ["src/contracts.ts", "test/contracts.test.ts", "vite.config.ts"]) {
      const result = eslint(["--print-config", file]);
      expect(result.status).toBe(0);
      const rules = JSON.parse(result.stdout).rules as Record<string, unknown>;
      expect(rules["@typescript-eslint/no-unused-vars"]).toEqual([2]);
    }

    for (const file of ["scripts/verify-lock.mjs", "eslint.config.js"]) {
      const result = eslint(["--print-config", file]);
      expect(result.status).toBe(0);
      const rules = JSON.parse(result.stdout).rules as Record<string, unknown>;
      expect(rules["no-unused-vars"]).toMatchObject([2, { args: "after-used" }]);
    }
  });

  it("rejects controlled unused JavaScript and TypeScript mutations", { timeout: 20_000 }, async () => {
    const directory = await mkdtemp(join(rendererRoot, ".lint-proof-"));
    try {
      const jsPath = join(directory, "unused.js");
      const tsPath = join(directory, "unused.ts");
      await writeFile(jsPath, "const unusedJavaScript = 1;\n", "utf8");
      await writeFile(tsPath, "const unusedTypeScript: number = 1;\n", "utf8");

      const jsResult = eslint([jsPath]);
      const tsResult = eslint([tsPath]);
      expect(jsResult.status).not.toBe(0);
      expect(tsResult.status).not.toBe(0);
      expect(`${jsResult.stdout}${jsResult.stderr}`).toContain("no-unused-vars");
      expect(`${tsResult.stdout}${tsResult.stderr}`).toContain("@typescript-eslint/no-unused-vars");
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });
});
