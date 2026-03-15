import type { SummaryResponse } from "../../lib/api/types";
import { MetricTile, Surface } from "../../ui";

interface HeroBriefProps {
  summary: SummaryResponse;
}

const formatFlow = (north?: number | null) => {
  if (north === undefined || north === null) {
    return "北向资金暂未就绪";
  }

  return `${north >= 0 ? "净流入" : "净流出"} ${(Math.abs(north) / 100).toFixed(1)} 亿`;
};

const buildHeroCopy = (summary: SummaryResponse) => {
  const total = summary.total_stocks || 1;
  const breadthValue = (summary.up_count / total) * 100;
  const breadth = breadthValue.toFixed(1);
  const north = summary.north_money?.north_total ?? null;
  const leader = summary.industry_ranking[0];
  const flowText = formatFlow(north);
  const averageMove = `${summary.avg_pct_chg >= 0 ? "+" : ""}${summary.avg_pct_chg.toFixed(2)}%`;
  const headline =
    breadthValue >= 60 && (north ?? 0) >= 0
      ? "广度占优，增量资金没有缺席"
      : breadthValue <= 40 && north !== null && north < 0
        ? "抛压扩散，风险偏好仍在收缩"
        : "轮动仍快，但主线并未失真";

  return {
    headline,
    message: `${summary.trade_date_fmt ?? "最新交易日"} 市场约 ${breadth}% 个股上涨，${summary.up_count} 家上涨、${summary.down_count} 家下跌，当前资金面 ${flowText}，热点集中在 ${leader?.name ?? "核心主线"}。`,
    breadth,
    flow: flowText,
    focus: leader ? `${leader.name} ${leader.pct_chg.toFixed(2)}%` : "等待行业排序",
    notes: [
      { label: "平均涨幅", value: averageMove },
      { label: "涨停 / 跌停", value: `${summary.limit_up} / ${summary.limit_down}` },
      { label: "龙虎榜", value: summary.top_list_summary?.top_reason ?? "暂无热词" },
    ],
  };
};

export const HeroBrief = ({ summary }: HeroBriefProps) => {
  const hero = buildHeroCopy(summary);

  return (
    <Surface className="hero-brief" data-testid="hero-brief">
      <div className="hero-brief__header">
        <span className="section-kicker">Morning Lead</span>
        <span className="hero-brief__stamp">{summary.trade_date_fmt ?? "Latest Session"}</span>
      </div>
      <h2 className="hero-brief__title">{hero.headline}</h2>
      <p className="hero-brief__body">{hero.message}</p>
      <div className="hero-brief__metrics">
        <MetricTile label="Breadth" value={`${hero.breadth}%`} />
        <MetricTile label="Flow" value={hero.flow} />
        <MetricTile label="Focus" value={hero.focus} />
      </div>
      <div className="hero-brief__notes">
        <div className="hero-brief__notes-header">
          <span className="section-kicker">Desk Notes</span>
        </div>
        <div className="hero-brief__notes-grid">
          {hero.notes.map((item) => (
            <div key={item.label} className="hero-note">
              <span className="hero-note__label">{item.label}</span>
              <strong className="hero-note__value">{item.value}</strong>
            </div>
          ))}
        </div>
      </div>
    </Surface>
  );
};
