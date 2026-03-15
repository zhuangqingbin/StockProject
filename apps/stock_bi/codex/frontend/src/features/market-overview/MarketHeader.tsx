import type { WsStatus } from "../../lib/api/types";
import { Button, StatusBadge } from "../../ui";

const wsStatusMap: Record<WsStatus, { text: string; status: WsStatus }> = {
  connecting: { text: "连接中", status: "connecting" },
  connected: { text: "已连接", status: "connected" },
  disconnected: { text: "未连接", status: "disconnected" },
};

interface MarketHeaderProps {
  tradeDate: string | null;
  wsStatus: WsStatus;
  onRefresh: () => void;
  refreshing: boolean;
}

export const MarketHeader = ({ tradeDate, wsStatus, onRefresh, refreshing }: MarketHeaderProps) => {
  const status = wsStatusMap[wsStatus];

  return (
    <header className="market-header">
      <div className="market-header__brand">
        <p className="market-header__eyebrow">Shanghai / Shenzhen / ChiNext</p>
        <h1 className="market-header__title">Stock BI</h1>
        <p className="market-header__deck">把盘中广度、资金流与相对强弱压缩成一张能读的晨会版面。</p>
      </div>
      <div className="market-header__meta">
        <div className="market-header__meta-block">
          <span className="market-header__meta-label">Trade Date</span>
          <strong className="market-header__date">{tradeDate ?? "等待交易日"}</strong>
        </div>
        <div className="market-header__meta-block">
          <span className="market-header__meta-label">Realtime</span>
          <StatusBadge status={status.status} label={status.text} />
        </div>
        <div className="market-header__actions">
          <Button onClick={onRefresh} loading={refreshing}>
            刷新数据
          </Button>
        </div>
      </div>
    </header>
  );
};
