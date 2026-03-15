import { describe, expect, it } from "vitest";

import { normalizeSummaryResponse } from "../../../lib/api/marketApi";

describe("normalizeSummaryResponse", () => {
  it("fills arrays and warning payloads with safe defaults", () => {
    const result = normalizeSummaryResponse({
      trade_date_fmt: "2026-03-15",
      total_stocks: 5231,
      up_count: 3188,
      down_count: 1800,
      data_consistency: {
        consistent: false,
        primary_date: "20260315",
        warnings: ["daily_basic latest date mismatch"],
      },
    });

    expect(result.trade_date_fmt).toBe("2026-03-15");
    expect(result.index_data).toEqual([]);
    expect(result.pct_distribution).toEqual([]);
    expect(result.industry_ranking).toEqual([]);
    expect(result.top_gainers).toEqual([]);
    expect(result.top_losers).toEqual([]);
    expect(result.data_consistency.warnings).toContain("daily_basic latest date mismatch");
  });
});
