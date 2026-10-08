import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { expect, test } from "vitest";

for (const [args, message] of [
  [["--unknown"], "Unknown advanced build argument"],
  [["--stage-only", "trailing"], "Unknown advanced build argument"],
  [["--stage-only", "--stage-only"], "Duplicate advanced build argument"],
] as const) {
  test(`advanced build rejects ${args.join(" ")} before generating assets`, () => {
    const script = fileURLToPath(new URL("../scripts/build-advanced-bundle.mjs", import.meta.url));
    const result = spawnSync(process.execPath, [script, ...args], {
      encoding: "utf8", timeout: 10_000, maxBuffer: 64 * 1024
    });
    expect(result.error).toBeUndefined();
    expect(result.status).toBe(1);
    expect(result.stdout).toBe("");
    expect(result.stderr).toContain(message);
  });
}
