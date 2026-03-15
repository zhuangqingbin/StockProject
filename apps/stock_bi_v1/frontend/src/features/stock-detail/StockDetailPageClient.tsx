"use client";

import { StockDetailView } from "@/features/stock-detail/StockDetailView";
import { useStockDetailData } from "@/lib/api";


export const StockDetailPageClient = ({ code }: { code: string }) => {
  const { profile, kline, valuationHistory, flowHistory, toplistHistory, historyRows, peerRows } = useStockDetailData(code);

  return (
    <StockDetailView
      profile={profile}
      kline={kline}
      valuationHistory={valuationHistory}
      flowHistory={flowHistory}
      toplistHistory={toplistHistory}
      historyRows={historyRows}
      peerRows={peerRows}
    />
  );
};
