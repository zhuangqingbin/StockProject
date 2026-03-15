export type IndexItem = {
  ts_code: string;
  name: string;
  close: number;
  pct_chg: number;
  amount?: number;
};

export type RankingItem = {
  ts_code: string;
  name: string;
  industry?: string;
  close: number;
  pct_chg: number;
  amount?: number;
  turnover_rate?: number;
};

export type MarketOverview = {
  trade_date: string;
  indices: IndexItem[];
  distribution: Record<string, number>;
  top_gainers: RankingItem[];
  top_losers: RankingItem[];
  top_amount: RankingItem[];
  top_turnover: RankingItem[];
  limit_stats: {
    up_count: number;
    down_count: number;
    broken_count: number;
    broken_rate: number;
    tier_stats: Record<string, number>;
  };
};

export type NorthMoneyItem = {
  trade_date: string;
  hgt: number;
  sgt: number;
  north_money: number;
  south_money: number;
};

export type TopListItem = {
  ts_code: string;
  trade_date: string;
  name: string;
  close: number;
  pct_chg: number;
  turnover_rate?: number;
  amount?: number;
  net_amount?: number;
  reason?: string;
};

export type StockProfile = {
  ts_code: string;
  symbol?: string;
  name: string;
  industry: string;
  market?: string;
  exchange: string;
  current_price: number;
  pct_chg: number;
  open: number;
  high: number;
  low: number;
  pre_close: number;
  amount: number;
  vol: number;
  turnover_rate: number;
  pe_ttm: number;
  pb: number;
  ps_ttm: number;
  total_mv: number;
  circ_mv: number;
  total_share: number;
  float_share: number;
};

export type KlineItem = {
  trade_date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  vol: number;
  amount: number;
  pct_chg: number;
};

export type FlowItem = {
  trade_date: string;
  buy_elg_amount?: number;
  sell_elg_amount?: number;
  buy_lg_amount?: number;
  sell_lg_amount?: number;
  buy_md_amount?: number;
  sell_md_amount?: number;
  buy_sm_amount?: number;
  sell_sm_amount?: number;
  net_mf_amount?: number;
};

export type PeerItem = {
  ts_code: string;
  name: string;
  close: number;
  pct_chg: number;
  total_mv: number;
  pe_ttm: number;
};

export type FilterMeta = {
  field: string;
  label: string;
  category: string;
  operators: string[];
};

export type ScreenerCondition = {
  field: string;
  operator: string;
  value: string | number | Array<string | number>;
};

export type ScreenerResultItem = {
  ts_code: string;
  name: string;
  industry: string;
  market: string;
  close: number;
  pct_chg: number;
  amount: number;
  turnover_rate: number;
  pe_ttm: number;
  pb: number;
  ps_ttm: number;
  total_mv: number;
  net_mf_amount: number;
};

export type IndustryDetail = {
  trade_date: string;
  industry: string;
  avg_pct_chg: number;
  total_amount: number;
  up_count: number;
  down_count: number;
  net_mf_amount: number;
  stock_count: number;
};

export type IndustryHeatmapItem = {
  industry: string;
  avg_pct_chg: number;
  total_amount: number;
  up_count: number;
  down_count: number;
  net_mf_amount: number;
  stock_count: number;
};
