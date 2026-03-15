import { request } from "./httpClient";
import type {
  AmountTrendPoint,
  DataConsistency,
  IndustryDetailResponse,
  IndustryStocksResponse,
  MoneyflowResponse,
  NorthTrendPoint,
  RankingResponse,
  RankingSortBy,
  SortDirection,
  StockDetailResponse,
  SummaryResponse,
  CompanyInfoResponse,
} from "./types";

const emptyConsistency: DataConsistency = {
  consistent: true,
  primary_date: null,
  warnings: [],
};

export const normalizeSummaryResponse = (payload: Partial<SummaryResponse>): SummaryResponse => ({
  trade_date: payload.trade_date ?? null,
  trade_date_fmt: payload.trade_date_fmt ?? null,
  total_stocks: payload.total_stocks ?? 0,
  up_count: payload.up_count ?? 0,
  down_count: payload.down_count ?? 0,
  flat_count: payload.flat_count ?? 0,
  limit_up: payload.limit_up ?? 0,
  limit_down: payload.limit_down ?? 0,
  total_amount: payload.total_amount ?? 0,
  avg_pct_chg: payload.avg_pct_chg ?? 0,
  north_money: payload.north_money ?? null,
  top_list_summary: payload.top_list_summary ?? null,
  data_consistency: {
    consistent: payload.data_consistency?.consistent ?? emptyConsistency.consistent,
    primary_date: payload.data_consistency?.primary_date ?? emptyConsistency.primary_date,
    warnings: payload.data_consistency?.warnings ?? emptyConsistency.warnings,
  },
  index_data: payload.index_data ?? [],
  pct_distribution: payload.pct_distribution ?? [],
  industry_ranking: payload.industry_ranking ?? [],
  top_gainers: payload.top_gainers ?? [],
  top_losers: payload.top_losers ?? [],
  top_amount: payload.top_amount ?? [],
  top_turnover: payload.top_turnover ?? [],
});

export const fetchSummary = async () => {
  const response = await request<Partial<SummaryResponse>>("/api/market/summary");
  return normalizeSummaryResponse(response);
};

export const fetchNorthMoneyTrend = () => {
  return request<NorthTrendPoint[]>("/api/market/north-money-trend", {
    query: { days: 30 },
  });
};

export const fetchAmountTrend = () => {
  return request<AmountTrendPoint[]>("/api/market/amount-trend", {
    query: { days: 30 },
  });
};

export const fetchRanking = (params: {
  sortBy: RankingSortBy;
  order: SortDirection;
  top: number;
  market?: string | null;
  industry?: string | null;
}) => {
  return request<RankingResponse>("/api/market/ranking-enhanced", {
    query: {
      sort_by: params.sortBy,
      order: params.order,
      top: params.top,
      market: params.market ?? undefined,
      industry: params.industry ?? undefined,
    },
  });
};

export const fetchIndustryDetail = (industry: string) => {
  return request<IndustryDetailResponse>(
    `/api/market/industry-detail/${encodeURIComponent(industry)}`,
  );
};

export const fetchIndustryStocks = (industry: string, order: SortDirection) => {
  return request<IndustryStocksResponse>(
    `/api/market/industry-stocks/${encodeURIComponent(industry)}`,
    { query: { order, limit: 80 } },
  );
};

export const fetchStockDetail = (tsCode: string) => {
  return request<StockDetailResponse>(`/api/market/stock/${encodeURIComponent(tsCode)}`);
};

export const fetchCompanyInfo = (tsCode: string) => {
  return request<CompanyInfoResponse>(`/api/market/company/${encodeURIComponent(tsCode)}`);
};

export const fetchMoneyflow = (tsCode: string) => {
  return request<MoneyflowResponse>(`/api/market/moneyflow/${encodeURIComponent(tsCode)}`);
};
