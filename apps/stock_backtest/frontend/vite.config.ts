import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

import { resolveManualChunk } from "./src/lib/chunkPlan";

export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 700,
    rollupOptions: {
      output: {
        manualChunks: resolveManualChunk,
      },
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    globals: true,
  },
});
