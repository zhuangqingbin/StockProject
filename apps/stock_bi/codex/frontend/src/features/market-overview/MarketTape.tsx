import type { SummaryResponse } from "../../lib/api/types";

const labels: Record<string, string> = {
  "000001.SH": "上证",
  "399001.SZ": "深成指",
  "399006.SZ": "创业板",
  "000688.SH": "科创 50",
};

type TapeTone = "up" | "down" | "neutral";

const formatFlow = (amount?: number | null) => {
  if (amount === undefined || amount === null) {
    return "北向待补齐";
  }

  return `${amount >= 0 ? "净流入" : "净流出"} ${(Math.abs(amount) / 100).toFixed(1)} 亿`;
};

const buildTapeItems = (summary: SummaryResponse) => {
  const total = summary.total_stocks || 1;
  const breadth = ((summary.up_count / total) * 100).toFixed(1);
  const leader = summary.industry_ranking[0];
  const dragonCount = summary.top_list_summary?.count;
  const dragonReason = summary.top_list_summary?.top_reason;
  const dragonValue =
    dragonCount || dragonReason
      ? `${dragonCount ?? "--"} 席${dragonReason ? ` / ${dragonReason}` : ""}`
      : "暂无龙虎榜线索";

  const items: Array<{ label: string; value: string; tone: TapeTone }> = [
    { label: "Breadth", value: `${breadth}% 上涨`, tone: summary.up_count >= summary.down_count ? "up" : "down" },
    { label: "Turnover", value: `${summary.total_amount.toFixed(0)} 亿`, tone: "neutral" },
    {
      label: "North Flow",
      value: formatFlow(summary.north_money?.north_total),
      tone:
        summary.north_money?.north_total === undefined || summary.north_money?.north_total === null
          ? "neutral"
          : summary.north_money.north_total >= 0
            ? "up"
            : "down",
    },
    { label: "Heat", value: leader ? `${leader.name} ${leader.pct_chg.toFixed(2)}%` : "等待行业排序", tone: "neutral" },
    { label: "Dragon List", value: dragonValue, tone: dragonReason ? "up" : "neutral" },
    { label: "Limit Up", value: `${summary.limit_up} 家`, tone: "up" },
    { label: "Limit Down", value: `${summary.limit_down} 家`, tone: summary.limit_down > summary.limit_up ? "down" : "neutral" },
  ];

  return [
    ...items,
    ...summary.index_data.map((index) => ({
      label: labels[index.ts_code] ?? index.name ?? index.ts_code,
      value: `${index.close.toFixed(2)} / ${index.pct_chg >= 0 ? "+" : ""}${index.pct_chg.toFixed(2)}%`,
      tone: index.pct_chg >= 0 ? "up" : "down",
    })),
  ];
};

interface MarketTapeProps {
  summary: SummaryResponse;
}

export const MarketTape = ({ summary }: MarketTapeProps) => {
  const items = buildTapeItems(summary);

  return (
    <section className="market-tape" aria-label="market tape">
      <div className="market-tape__track">
        {[0, 1].flatMap((copyIndex) =>
          items.map((item, itemIndex) => (
            <div
              key={`${copyIndex}-${item.label}-${itemIndex}`}
              className={`market-tape__item is-${item.tone}`}
              aria-hidden={copyIndex === 1}
            >
              <span className="market-tape__label">{item.label}</span>
              <strong className="market-tape__value">{item.value}</strong>
            </div>
          )),
        )}
      </div>
    </section>
  );
};
