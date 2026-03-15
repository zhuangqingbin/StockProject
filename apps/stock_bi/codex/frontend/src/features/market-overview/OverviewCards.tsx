import type { SummaryResponse } from "../../lib/api/types";
import { MetricTile, Surface } from "../../ui";

interface OverviewCardsProps {
  summary: SummaryResponse;
}

type CardTone = "up" | "down" | "neutral";

const ratio = (part: number, total: number) => `${((part / (total || 1)) * 100).toFixed(1)}%`;

const cards = (summary: SummaryResponse) => {
  const north = summary.north_money?.north_total;

  return [
    {
      title: "上涨家数",
      value: summary.up_count,
      suffix: `/${summary.total_stocks}`,
      hint: `占比 ${ratio(summary.up_count, summary.total_stocks)}`,
      tone: "up" as CardTone,
    },
    {
      title: "下跌家数",
      value: summary.down_count,
      suffix: `/${summary.total_stocks}`,
      hint: `占比 ${ratio(summary.down_count, summary.total_stocks)}`,
      tone: "down" as CardTone,
    },
    {
      title: "成交额",
      value: summary.total_amount.toFixed(0),
      suffix: "亿",
      hint: `平均涨跌 ${summary.avg_pct_chg >= 0 ? "+" : ""}${summary.avg_pct_chg.toFixed(2)}%`,
      tone: "neutral" as CardTone,
    },
    {
      title: "涨停数",
      value: summary.limit_up,
      suffix: "家",
      hint: `跌停仅 ${summary.limit_down} 家`,
      tone: summary.limit_up >= summary.limit_down ? ("up" as CardTone) : ("neutral" as CardTone),
    },
    {
      title: "北向资金",
      value: north === undefined || north === null ? "--" : (north / 100).toFixed(1),
      suffix: "亿",
      hint:
        summary.north_money?.hgt !== undefined && summary.north_money?.sgt !== undefined
          ? `沪股通 ${summary.north_money.hgt} / 深股通 ${summary.north_money.sgt}`
          : "通道拆分待补齐",
      tone:
        north === undefined || north === null ? ("neutral" as CardTone) : north >= 0 ? ("up" as CardTone) : ("down" as CardTone),
    },
  ];
};

export const OverviewCards = ({ summary }: OverviewCardsProps) => {
  return (
    <Surface className="overview-cards">
      <div className="overview-cards__header">
        <span className="section-kicker">Session Ledger</span>
        <p className="overview-cards__summary">先看五个数字，再决定去读哪一张图。</p>
      </div>
      <div className="overview-cards__grid">
        {cards(summary).map((card, index) => (
          <div className={`overview-card overview-card--${card.tone}`} key={card.title}>
            <span className="overview-card__index">{String(index + 1).padStart(2, "0")}</span>
            <MetricTile label={card.title} value={card.value} suffix={card.suffix} />
            <p className="overview-card__hint">{card.hint}</p>
          </div>
        ))}
      </div>
    </Surface>
  );
};
