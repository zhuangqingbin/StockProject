import { describe, expect, it } from "vitest";

import { buildDistributionOption } from "../../../features/chart-stage/options/distributionOptions";
import { buildLineSeriesOption } from "../../../features/chart-stage/options/lineOptions";
import {
  buildIndustryTreemapOption,
  buildRankingTreemapOption,
} from "../../../features/chart-stage/options/treemapOptions";

describe("chartOptions", () => {
  it("builds a distribution bar chart option", () => {
    const option = buildDistributionOption([
      { range_start: -2, range_end: 0, count: 12 },
      { range_start: 0, range_end: 2, count: 18 },
    ]);
    const xAxis = option.xAxis as any;
    const series = option.series as any[];

    expect(xAxis?.type).toBe("category");
    expect(series?.[0]?.type).toBe("bar");
  });

  it("builds an industry treemap option with domain labels", () => {
    const option = buildIndustryTreemapOption(
      [
        {
          name: "半导体",
          pct_chg: 3.1,
          avg5_pct_chg: 2.6,
          total_amount: 3200,
          stock_count: 48,
          up_count: 32,
          down_count: 10,
        },
      ],
      10,
    );
    const series = option.series as any[];

    expect(series?.[0]?.type).toBe("treemap");
    expect(series?.[0]?.data?.[0]?.name).toContain("半导体");
  });

  it("builds a ranking treemap option keyed by stock code", () => {
    const option = buildRankingTreemapOption(
      [
        {
          ts_code: "600519.SH",
          name: "贵州茅台",
          pct_chg: 4.2,
          close: 1550,
          amount: 820000,
          turnover_rate: 0.9,
        },
      ],
      "desc",
      10,
    );
    const series = option.series as any[];

    expect(series?.[0]?.type).toBe("treemap");
    expect(series?.[0]?.data?.[0]?.ts_code).toBe("600519.SH");
  });

  it("builds a reusable line option for trend charts", () => {
    const option = buildLineSeriesOption(
      ["2026-03-13", "2026-03-14"],
      [120, 135],
      "#da8e57",
      "rgba(218,142,87,0.24)",
    );
    const xAxis = option.xAxis as any;
    const series = option.series as any[];

    expect(xAxis?.boundaryGap).toBe(false);
    expect(series?.[0]?.type).toBe("line");
    expect(series?.[0]?.data).toEqual([120, 135]);
  });
});
