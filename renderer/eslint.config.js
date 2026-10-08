import js from "@eslint/js";
import tseslint from "typescript-eslint";

const nodeGlobals = {
  Buffer: "readonly",
  URL: "readonly",
  console: "readonly",
  process: "readonly"
};

export default [
  {
    ignores: ["dist/**", "coverage/**", "node_modules/**"]
  },
  {
    ...js.configs.recommended,
    files: ["**/*.{js,mjs}"],
    languageOptions: {
      ...js.configs.recommended.languageOptions,
      globals: nodeGlobals
    }
  },
  ...tseslint.configs.recommended.map((config) => ({
    ...config,
    files: ["**/*.{ts,tsx}"]
  }))
];
