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

export const demoOverview: MarketOverview = {
  trade_date: "20260315",
  indices: [
    { ts_code: "000001.SH", name: "上证指数", close: 3350.12, pct_chg: 1.1, amount: 120000000 },
    { ts_code: "399001.SZ", name: "深证成指", close: 10820.55, pct_chg: 0.8, amount: 98000000 },
    { ts_code: "399006.SZ", name: "创业板指", close: 2105.77, pct_chg: -0.2, amount: 87000000 },
  ],
  distribution: { "-3~0": 1200, "0~3": 1800, "3~5": 320, "5~7": 88 },
  top_gainers: [{ ts_code: "000001.SZ", name: "平安银行", pct_chg: 5.21, close: 12.31, amount: 100000000 }],
  top_losers: [{ ts_code: "600000.SH", name: "浦发银行", pct_chg: -2.11, close: 9.88, amount: 90000000 }],
  top_amount: [{ ts_code: "300750.SZ", name: "宁德时代", pct_chg: 2.31, close: 212.9, amount: 550000000 }],
  top_turnover: [{ ts_code: "688981.SH", name: "中芯国际", pct_chg: 3.12, close: 51.2, turnover_rate: 9.4 }],
  limit_stats: { up_count: 12, down_count: 1, broken_count: 3, broken_rate: 0.2, tier_stats: { "1": 8, "2": 3, "3": 1 } },
};

export const demoNorthMoney: NorthMoneyItem[] = [
  { trade_date: "20260311", hgt: 20, sgt: 18, north_money: 38, south_money: 4 },
  { trade_date: "20260312", hgt: 24, sgt: 21, north_money: 45, south_money: 5 },
  { trade_date: "20260313", hgt: 16, sgt: 12, north_money: 28, south_money: 3 },
  { trade_date: "20260314", hgt: 28, sgt: 18, north_money: 46, south_money: 7 },
  { trade_date: "20260315", hgt: 31, sgt: 24, north_money: 55, south_money: 8 },
];

export const demoToplist: TopListItem[] = [
  { ts_code: "000001.SZ", trade_date: "20260315", name: "平安银行", close: 11.7, pct_chg: 2.63, net_amount: 800000, reason: "日涨幅偏离值达7%" },
  { ts_code: "300750.SZ", trade_date: "20260315", name: "宁德时代", close: 212.9, pct_chg: 4.18, net_amount: 3200000, reason: "机构净买入" },
];

export const demoProfile: StockProfile = {
  ts_code: "000001.SZ",
  symbol: "000001",
  name: "平安银行",
  industry: "银行",
  market: "主板",
  exchange: "SZSE",
  current_price: 11.7,
  pct_chg: 2.63,
  open: 11.5,
  high: 11.8,
  low: 11.3,
  pre_close: 11.4,
  amount: 5567890,
  vol: 153456,
  turnover_rate: 1.8,
  pe_ttm: 6.2,
  pb: 0.7,
  ps_ttm: 1.1,
  total_mv: 210000000000,
  circ_mv: 180000000000,
  total_share: 19400000000,
  float_share: 16200000000,
};

export const demoKline: KlineItem[] = [
  { trade_date: "20260311", open: 11.1, high: 11.3, low: 10.9, close: 11.0, vol: 120000, amount: 5000000, pct_chg: -0.8 },
  { trade_date: "20260312", open: 11.2, high: 11.6, low: 11.0, close: 11.4, vol: 123456, amount: 4567890, pct_chg: 2.7 },
  { trade_date: "20260313", open: 11.5, high: 11.8, low: 11.3, close: 11.7, vol: 153456, amount: 5567890, pct_chg: 2.63 },
];

export const demoValuation = [
  { trade_date: "20260311", pe_ttm: 6.1, pb: 0.69, ps_ttm: 1.08 },
  { trade_date: "20260312", pe_ttm: 6.15, pb: 0.7, ps_ttm: 1.09 },
  { trade_date: "20260313", pe_ttm: 6.2, pb: 0.7, ps_ttm: 1.1 },
];

export const demoFlow: FlowItem[] = [
  { trade_date: "20260311", net_mf_amount: 420, buy_elg_amount: 900, sell_elg_amount: 480 },
  { trade_date: "20260312", net_mf_amount: 730, buy_elg_amount: 1100, sell_elg_amount: 370 },
  { trade_date: "20260313", net_mf_amount: 950, buy_elg_amount: 1000, sell_elg_amount: 400 },
];

export const demoPeers: PeerItem[] = [
  { ts_code: "600000.SH", name: "浦发银行", close: 9.88, pct_chg: 0.88, total_mv: 150000000000, pe_ttm: 6.8 },
  { ts_code: "601166.SH", name: "兴业银行", close: 18.42, pct_chg: 1.13, total_mv: 320000000000, pe_ttm: 5.9 },
];

export const demoFilters: FilterMeta[] = [
  { field: "pct_chg", label: "涨跌幅", category: "行情", operators: ["gt", "lt", "between"] },
  { field: "pe_ttm", label: "PE(TTM)", category: "估值", operators: ["gt", "lt", "between"] },
  { field: "industry", label: "行业", category: "分类", operators: ["eq", "contains"] },
];

export const demoScreenerResults: ScreenerResultItem[] = [
  { ts_code: "000001.SZ", name: "平安银行", industry: "银行", market: "主板", close: 11.7, pct_chg: 2.63, amount: 5567890, turnover_rate: 1.8, pe_ttm: 6.2, pb: 0.7, ps_ttm: 1.1, total_mv: 210000000000, net_mf_amount: 950 },
  { ts_code: "601166.SH", name: "兴业银行", industry: "银行", market: "主板", close: 18.42, pct_chg: 1.13, amount: 4560000, turnover_rate: 1.3, pe_ttm: 5.9, pb: 0.66, ps_ttm: 1.02, total_mv: 320000000000, net_mf_amount: 640 },
];

export const demoIndustryDetail: IndustryDetail = {
  trade_date: "20260315",
  industry: "银行",
  avg_pct_chg: 1.32,
  total_amount: 4500000000,
  up_count: 28,
  down_count: 5,
  net_mf_amount: 560000000,
  stock_count: 33,
};

export const demoHeatmap: IndustryHeatmapItem[] = [
  { industry: "银行", avg_pct_chg: 1.32, total_amount: 4500000000, up_count: 28, down_count: 5, net_mf_amount: 560000000, stock_count: 33 },
  { industry: "半导体", avg_pct_chg: 2.16, total_amount: 6800000000, up_count: 41, down_count: 8, net_mf_amount: 910000000, stock_count: 49 },
  { industry: "新能源", avg_pct_chg: -0.82, total_amount: 5900000000, up_count: 18, down_count: 22, net_mf_amount: -130000000, stock_count: 40 },
];
