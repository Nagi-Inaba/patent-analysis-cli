import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";

export default defineConfig({
  define: {
    "process.env.NODE_ENV": JSON.stringify("production")
  },
  build: {
    target: "node24",
    write: false,
    sourcemap: false,
    minify: "oxc",
    cssCodeSplit: false,
    assetsInlineLimit: 0,
    emitAssets: false,
    copyPublicDir: false,
    manifest: false,
    ssrManifest: false,
    reportCompressedSize: false,
    lib: {
      entry: fileURLToPath(
        new URL("./src/points-index.ts", import.meta.url)
      ),
      name: "PatentAnalysisRenderer",
      formats: ["iife"],
      fileName: () => "points-renderer.bundle.js"
    },
    rollupOptions: {
      external: [],
      output: {
        entryFileNames: "points-renderer.bundle.js",
        chunkFileNames: "points-renderer.chunk.js",
        assetFileNames: "points-renderer.asset[extname]"
      }
    }
  }
});
