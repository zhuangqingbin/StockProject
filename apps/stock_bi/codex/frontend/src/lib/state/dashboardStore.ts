import { create } from "zustand";

import type { ChartView, RankingSortBy, SortDirection, WsStatus } from "../api/types";

export interface DashboardStoreState {
  view: ChartView;
  topN: number;
  order: SortDirection;
  rankingSortBy: RankingSortBy;
  activeStock: string | null;
  activeIndustry: string | null;
  updateBannerTradeDate: string | null;
  wsStatus: WsStatus;
  setView: (view: ChartView) => void;
  setTopN: (topN: number) => void;
  setOrder: (order: SortDirection) => void;
  setRankingSortBy: (sortBy: RankingSortBy) => void;
  setActiveStock: (tsCode: string | null) => void;
  setActiveIndustry: (industry: string | null) => void;
  setUpdateBannerTradeDate: (tradeDate: string | null) => void;
  setWsStatus: (status: WsStatus) => void;
}

export const useDashboardStore = create<DashboardStoreState>()((set) => ({
  view: "distribution",
  topN: 10,
  order: "desc",
  rankingSortBy: "pct_chg",
  activeStock: null,
  activeIndustry: null,
  updateBannerTradeDate: null,
  wsStatus: "connecting",
  setView: (view) => set({ view }),
  setTopN: (topN) => set({ topN }),
  setOrder: (order) => set({ order }),
  setRankingSortBy: (rankingSortBy) => set({ rankingSortBy }),
  setActiveStock: (activeStock) => set({ activeStock }),
  setActiveIndustry: (activeIndustry) => set({ activeIndustry }),
  setUpdateBannerTradeDate: (updateBannerTradeDate) => set({ updateBannerTradeDate }),
  setWsStatus: (wsStatus) => set({ wsStatus }),
}));
