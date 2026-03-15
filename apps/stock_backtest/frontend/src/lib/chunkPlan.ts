const FRAMEWORK_PACKAGES = ["react", "react-dom", "react-router", "@tanstack", "zustand", "scheduler"];
const EDITOR_PACKAGES = ["@monaco-editor", "monaco-editor"];
const CHART_PACKAGES = ["echarts", "zrender"];

const matchesPackage = (id: string, packageNames: string[]) => packageNames.some((packageName) => id.includes(packageName));

export const resolveManualChunk = (id: string) => {
  if (!id.includes("node_modules")) {
    return undefined;
  }
  if (matchesPackage(id, EDITOR_PACKAGES)) {
    return "editor";
  }
  if (matchesPackage(id, CHART_PACKAGES)) {
    return "charts";
  }
  if (matchesPackage(id, FRAMEWORK_PACKAGES)) {
    return "framework";
  }
  return undefined;
};
