import { describe, expect, test } from "vitest";

import { resolveManualChunk } from "./chunkPlan";

describe("resolveManualChunk", () => {
  test("splits only the remaining heavyweight dependencies into explicit async chunks", () => {
    expect(resolveManualChunk("/repo/node_modules/@monaco-editor/react/index.js")).toBe("editor");
    expect(resolveManualChunk("/repo/node_modules/echarts/core.js")).toBe("charts");
    expect(resolveManualChunk("/repo/node_modules/zrender/lib/zrender.js")).toBe("charts");
    expect(resolveManualChunk("/repo/node_modules/react-router-dom/index.js")).toBe("framework");
    expect(resolveManualChunk("/repo/node_modules/antd/es/button/index.js")).toBeUndefined();
    expect(resolveManualChunk("/repo/node_modules/dayjs/dayjs.min.js")).toBeUndefined();
    expect(resolveManualChunk("/repo/src/pages/AnalysisPage.tsx")).toBeUndefined();
  });
});
