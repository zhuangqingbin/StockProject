"use client";

import useSWR from "swr";

import {
  demoFilters,
  demoFlow,
  demoHeatmap,
  demoIndustryDetail,
  demoKline,
  demoNorthMoney,
  demoOverview,
  demoPeers,
  demoProfile,
  demoScreenerResults,
  demoToplist,
  demoValuation,
} from "@/lib/demo-data";
import type {
  FilterMeta,
  FlowItem,
  IndustryDetail,
  IndustryHeatmapItem,
  KlineItem,
  MarketOverview,
  NorthMoneyItem,
  PeerItem,
  ScreenerResultItem,
  StockProfile,
  TopListItem,
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_STOCK_BI_V1_API_BASE ?? "http://localhost:8100";

const fetchJson = async <T,>(path: string): Promise<T> => {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${path}`);
  }
  return (await response.json()) as T;
};

const useBackendData = <T,>(key: string, path: string, fallbackData: T) =>
  useSWR<T>(key, () => fetchJson<T>(path), {
    fallbackData,
    revalidateOnFocus: false,
    shouldRetryOnError: false,
  });

export const useDashboardData = () => {
  const overview = useBackendData<MarketOverview>("dashboard-overview", "/api/market/overview", demoOverview);
  const northFlow = useBackendData<NorthMoneyItem[]>("dashboard-north", "/api/flow/north?days=5", demoNorthMoney);
  const topList = useBackendData<TopListItem[]>("dashboard-toplist", "/api/toplist/daily", demoToplist);
  const heatmap = useBackendData<IndustryHeatmapItem[]>("dashboard-heatmap", "/api/industry/heatmap", demoHeatmap);
  return {
    overview: overview.data ?? demoOverview,
    northFlow: northFlow.data ?? demoNorthMoney,
    topList: topList.data ?? demoToplist,
    heatmap: heatmap.data ?? demoHeatmap,
  };
};

export const useStockDetailData = (code: string) => {
  const profile = useBackendData<StockProfile>(`stock-profile-${code}`, `/api/stock/${code}/profile`, demoProfile);
  const kline = useBackendData<KlineItem[]>(`stock-kline-${code}`, `/api/stock/${code}/kline?period=daily`, demoKline);
  const valuationHistory = useBackendData<{ trade_date: string; pe_ttm: number; pb: number; ps_ttm: number }[]>(
    `stock-valuation-${code}`,
    `/api/stock/${code}/valuation-history`,
    demoValuation,
  );
  const flowHistory = useBackendData<FlowItem[]>(`stock-flow-${code}`, `/api/flow/stock/${code}?days=30`, demoFlow);
  const toplistHistory = useBackendData<TopListItem[]>(`stock-toplist-${code}`, `/api/toplist/stock/${code}`, demoToplist);
  const peerRows = useBackendData<PeerItem[]>(`stock-peers-${code}`, `/api/stock/${code}/peers`, demoPeers);
  const historyRows = useBackendData<{ items: KlineItem[] }>(`stock-history-${code}`, `/api/stock/${code}/history`, { items: demoKline });
  return {
    profile: profile.data ?? demoProfile,
    kline: kline.data ?? demoKline,
    valuationHistory: valuationHistory.data ?? demoValuation,
    flowHistory: flowHistory.data ?? demoFlow,
    toplistHistory: toplistHistory.data ?? demoToplist,
    peerRows: peerRows.data ?? demoPeers,
    historyRows: (historyRows.data?.items ?? demoKline) as KlineItem[],
  };
};

export const useScreenerData = () => {
  const filters = useBackendData<FilterMeta[]>("screener-filters", "/api/screener/filters", demoFilters);
  return { filters: filters.data ?? demoFilters, initialResults: demoScreenerResults };
};

export const searchStocks = async (query: string) => {
  return fetchJson<Array<{ ts_code: string; name: string; industry?: string }>>(`/api/stock/search?q=${encodeURIComponent(query)}`);
};

export const queryScreener = async (payload: {
  conditions: Array<{ field: string; operator: string; value: string | number | Array<string | number> }>;
  sort_by: string;
  order: string;
  page: number;
  size: number;
}) => {
  const response = await fetch(`${API_BASE}/api/screener/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Screener query failed");
  }
  return (await response.json()) as { items: ScreenerResultItem[] };
};

export const exportScreener = async (payload: {
  conditions: Array<{ field: string; operator: string; value: string | number | Array<string | number> }>;
  sort_by: string;
  order: string;
  page: number;
  size: number;
}) => {
  const response = await fetch(`${API_BASE}/api/screener/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Screener export failed");
  }
  return response.blob();
};

export const useIndustryData = (name: string) => {
  const detail = useBackendData<IndustryDetail>(`industry-${name}`, `/api/industry/detail?name=${encodeURIComponent(name)}`, demoIndustryDetail);
  const stocks = useBackendData<ScreenerResultItem[]>(
    `industry-stocks-${name}`,
    `/api/industry/stocks?name=${encodeURIComponent(name)}`,
    demoScreenerResults,
  );
  return { detail: detail.data ?? demoIndustryDetail, stocks: stocks.data ?? demoScreenerResults };
};

export const useToplistData = () => useBackendData<TopListItem[]>("toplist-page", "/api/toplist/daily", demoToplist);

export const useLimitData = () => {
  const limitStats = useBackendData<{ up_count: number; down_count: number; broken_count: number; broken_rate: number; tier_stats: Record<string, number> }>(
    "limit-stats",
    "/api/market/limit-stats",
    demoOverview.limit_stats,
  );
  const limitList = useBackendData<Array<{ ts_code: string; name: string }>>("limit-list", "/api/market/limit-list?type=up", demoOverview.top_gainers);
  return { limitStats: limitStats.data ?? demoOverview.limit_stats, limitList: limitList.data ?? demoOverview.top_gainers };
};
