import { describe, expect, it } from "vitest";

import { resolveReactComponentExport } from "../../../lib/charts/resolveReactComponentExport";

describe("resolveReactComponentExport", () => {
  it("unwraps a CommonJS-style default export object", () => {
    const FakeComponent = () => null;

    expect(resolveReactComponentExport({ default: FakeComponent })).toBe(FakeComponent);
  });

  it("keeps an already-direct component export intact", () => {
    const FakeComponent = () => null;

    expect(resolveReactComponentExport(FakeComponent)).toBe(FakeComponent);
  });
});
