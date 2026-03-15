export type ChartView = "distribution" | "industry" | "ranking";
export type SortDirection = "asc" | "desc";
export type RankingSortBy = "pct_chg" | "amount" | "turnover";
export type WsStatus = "connecting" | "connected" | "disconnected";

export interface DataConsistency {
  consistent: boolean;
  primary_date: string | null;
  warnings: string[];
}

export interface IndexItem {
  ts_code: string;
  name?: string;
  close: number;
  pct_chg: number;
}

export interface DistributionBucket {
  range_start: number;
  range_end: number;
  count: number;
}

export interface NorthMoneySummary {
  north_total?: number;
  hgt?: number;
  sgt?: number;
  trade_date?: string;
  message?: string;
}

export interface IndustryRankingItem {
  name: string;
  pct_chg: number;
  avg5_pct_chg?: number;
  total_amount: number;
  stock_count: number;
  up_count: number;
  down_count: number;
  up_ratio?: number;
}

export interface RankingItem {
  ts_code: string;
  name?: string;
  pct_chg: number;
  close?: number;
  amount?: number;
  vol?: number;
  turnover_rate?: number;
  industry?: string | null;
  pe?: number | null;
  pb?: number | null;
}

export interface AmountTrendPoint {
  trade_date: string;
  total_amount: number;
}

export interface NorthTrendPoint {
  trade_date: string;
  north_total: number;
  hgt: number;
  sgt: number;
}

export interface TopListSummary {
  count?: number;
  net_buy_amount?: number;
  top_reason?: string;
}

export interface SummaryResponse {
  trade_date?: string | null;
  trade_date_fmt: string | null;
  total_stocks: number;
  up_count: number;
  down_count: number;
  flat_count: number;
  limit_up: number;
  limit_down: number;
  total_amount: number;
  avg_pct_chg: number;
  north_money?: NorthMoneySummary | null;
  top_list_summary?: TopListSummary | null;
  data_consistency: DataConsistency;
  index_data: IndexItem[];
  pct_distribution: DistributionBucket[];
  industry_ranking: IndustryRankingItem[];
  top_gainers: RankingItem[];
  top_losers: RankingItem[];
  top_amount: RankingItem[];
  top_turnover: RankingItem[];
}

export interface RankingResponse {
  trade_date: string;
  sort_by: RankingSortBy;
  order: SortDirection;
  market?: string | null;
  industry?: string | null;
  stocks: RankingItem[];
}

export interface IndustryDetailResponse {
  industry: string;
  trade_date: string;
  index_code?: string | null;
  index_name?: string | null;
  today?: {
    open: number;
    high: number;
    low: number;
    close: number;
    pct_chg: number;
    vol: number;
    amount: number;
    pe?: number | null;
    pb?: number | null;
  } | null;
  stats?: {
    stock_count: number;
    up_count: number;
    down_count: number;
    avg_pct_chg: number;
    total_amount: number;
  } | null;
  kline: Array<{
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    vol: number;
    amount: number;
    pct_chg: number;
  }>;
}

export interface IndustryStocksResponse {
  trade_date: string;
  industry: string;
  order: SortDirection;
  total: number;
  up_count: number;
  down_count: number;
  flat_count: number;
  stocks: Array<
    RankingItem & {
      open?: number;
      high?: number;
      low?: number;
      total_mv?: number | null;
    }
  >;
}

export interface StockDetailResponse {
  ts_code: string;
  trade_date: string;
  daily?: {
    ts_code: string;
    trade_date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    pre_close: number;
    pct_chg: number;
    vol: number;
    amount: number;
    name: string;
  } | null;
  basic?: {
    turnover_rate: number;
    pe: number;
    pe_ttm: number;
    pb: number;
    total_mv: number;
    circ_mv: number;
    volume_ratio: number;
  } | null;
  company?: {
    ts_code: string;
    name: string;
    area?: string | null;
    industry?: string | null;
    market?: string | null;
    list_date?: string | null;
  } | null;
  kline: Array<{
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    pct_chg: number;
    vol: number;
    amount: number;
  }>;
}

export interface CompanyInfoResponse {
  ts_code: string;
  symbol?: string;
  name: string;
  area?: string;
  industry?: string;
  market?: string;
  exchange?: string;
  list_date?: string;
  chairman?: string;
  manager?: string;
  main_business?: string;
  website?: string;
}

export interface MoneyflowBucket {
  buy_vol: number;
  buy_amount: number;
  sell_vol: number;
  sell_amount: number;
  net_amount: number;
}

export interface MoneyflowResponse {
  ts_code: string;
  trade_date: string;
  small?: MoneyflowBucket;
  medium?: MoneyflowBucket;
  large?: MoneyflowBucket;
  extra_large?: MoneyflowBucket;
  net_mf_vol?: number;
  net_mf_amount?: number;
  message?: string;
}

export interface ChatContextTurn {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  reply: string;
  chart_config?: Record<string, unknown> | null;
  data?: Array<Record<string, unknown>> | null;
  sql?: string | null;
}
