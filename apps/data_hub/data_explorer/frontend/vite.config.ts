import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) {
            return undefined;
          }

          if (id.includes("/react/") || id.includes("/react-dom/") || id.includes("/scheduler/")) {
            return "react-vendor";
          }

          if (id.includes("/@tanstack/react-query/") || id.includes("/axios/")) {
            return "data-vendor";
          }

          return undefined;
        },
      },
    },
  },
  server: {
    port: 5178,
    proxy: {
      "/api": "http://127.0.0.1:8201",
      "/health": "http://127.0.0.1:8201"
    }
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    globals: true
  }
});
