import type { IndexItem } from "../../lib/api/types";
import { Surface } from "../../ui";

const labels: Record<string, string> = {
  "000001.SH": "上证指数",
  "399001.SZ": "深证成指",
  "399006.SZ": "创业板指",
  "000688.SH": "科创 50",
};

interface IndexPulseProps {
  indices: IndexItem[];
}

export const IndexPulse = ({ indices }: IndexPulseProps) => {
  return (
    <Surface className="index-pulse" data-testid="market-pulse">
      <div className="index-pulse__header">
        <span className="section-kicker">Pulse Board</span>
        <p className="index-pulse__summary">四大指数的即时温差。</p>
      </div>
      <div className="index-pulse__grid">
        {indices.map((index) => (
          <div key={index.ts_code} className={`index-pulse__item ${index.pct_chg >= 0 ? "is-up" : "is-down"}`}>
            <span className="index-pulse__label">{labels[index.ts_code] ?? index.name ?? index.ts_code}</span>
            <strong className="index-pulse__value">{index.close.toFixed(2)}</strong>
            <span className="index-pulse__change">
              {index.pct_chg >= 0 ? "+" : ""}
              {index.pct_chg.toFixed(2)}%
            </span>
          </div>
        ))}
      </div>
    </Surface>
  );
};
