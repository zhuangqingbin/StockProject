from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StockBiV1Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class IndexItem(StockBiV1Schema):
    ts_code: str
    name: str
    close: float
    pct_chg: float
    amount: float = 0.0


class RankingItem(StockBiV1Schema):
    ts_code: str
    name: str
    industry: str = ""
    close: float = 0.0
    pct_chg: float = 0.0
    amount: float = 0.0
    turnover_rate: float = 0.0


class MarketOverviewResponse(StockBiV1Schema):
    trade_date: str
    indices: list[IndexItem]
    distribution: dict[str, int]
    top_gainers: list[RankingItem]
    top_losers: list[RankingItem]
    top_amount: list[RankingItem]
    top_turnover: list[RankingItem]
    limit_stats: dict[str, Any]


class IndustryHeatmapItem(StockBiV1Schema):
    industry: str
    avg_pct_chg: float
    total_amount: float
    up_count: int
    down_count: int
    net_mf_amount: float
    stock_count: int


class IndustryDetailResponse(StockBiV1Schema):
    trade_date: str
    industry: str
    avg_pct_chg: float
    total_amount: float
    up_count: int
    down_count: int
    net_mf_amount: float
    stock_count: int


class IndustryStockItem(StockBiV1Schema):
    ts_code: str
    name: str
    industry: str
    close: float
    pct_chg: float
    amount: float
    turnover_rate: float = 0.0
    pe_ttm: float = 0.0
    net_mf_amount: float = 0.0


class SearchResult(StockBiV1Schema):
    ts_code: str
    symbol: str
    name: str
    industry: str = ""
    market: str = ""


class StockProfileResponse(StockBiV1Schema):
    ts_code: str
    symbol: str
    name: str
    industry: str = ""
    market: str = ""
    exchange: str = ""
    current_price: float = 0.0
    pct_chg: float = 0.0
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    pre_close: float = 0.0
    amount: float = 0.0
    vol: float = 0.0
    turnover_rate: float = 0.0
    pe_ttm: float = 0.0
    pb: float = 0.0
    ps_ttm: float = 0.0
    total_mv: float = 0.0
    circ_mv: float = 0.0
    total_share: float = 0.0
    float_share: float = 0.0


class KlineItem(StockBiV1Schema):
    trade_date: str
    open: float
    high: float
    low: float
    close: float
    vol: float = 0.0
    amount: float = 0.0
    pct_chg: float = 0.0


class ValuationItem(StockBiV1Schema):
    trade_date: str
    pe_ttm: float = 0.0
    pb: float = 0.0
    ps_ttm: float = 0.0


class PeerItem(StockBiV1Schema):
    ts_code: str
    name: str
    close: float = 0.0
    pct_chg: float = 0.0
    total_mv: float = 0.0
    pe_ttm: float = 0.0


class NorthMoneyItem(StockBiV1Schema):
    trade_date: str
    hgt: float = 0.0
    sgt: float = 0.0
    north_money: float = 0.0
    south_money: float = 0.0


class StockFlowItem(StockBiV1Schema):
    trade_date: str
    buy_elg_amount: float = 0.0
    sell_elg_amount: float = 0.0
    buy_lg_amount: float = 0.0
    sell_lg_amount: float = 0.0
    buy_md_amount: float = 0.0
    sell_md_amount: float = 0.0
    buy_sm_amount: float = 0.0
    sell_sm_amount: float = 0.0
    net_mf_amount: float = 0.0


class TopListItem(StockBiV1Schema):
    ts_code: str
    trade_date: str
    name: str
    close: float = 0.0
    pct_chg: float = 0.0
    turnover_rate: float = 0.0
    amount: float = 0.0
    l_buy: float = 0.0
    l_sell: float = 0.0
    net_amount: float = 0.0
    reason: str = ""


class ScreenerCondition(StockBiV1Schema):
    field: str
    operator: Literal["gt", "lt", "eq", "between", "contains"] = "eq"
    value: Any


class ScreenerRequest(StockBiV1Schema):
    conditions: list[ScreenerCondition] = Field(default_factory=list)
    sort_by: str = "pct_chg"
    order: Literal["asc", "desc"] = "desc"
    page: int = 0
    size: int = 20


class ScreenerResultItem(StockBiV1Schema):
    ts_code: str
    name: str
    industry: str = ""
    market: str = ""
    close: float = 0.0
    pct_chg: float = 0.0
    amount: float = 0.0
    turnover_rate: float = 0.0
    pe_ttm: float = 0.0
    pb: float = 0.0
    ps_ttm: float = 0.0
    total_mv: float = 0.0
    net_mf_amount: float = 0.0


class ScreenerResponse(StockBiV1Schema):
    total: int
    page: int
    size: int
    items: list[ScreenerResultItem]


class FilterMeta(StockBiV1Schema):
    field: str
    label: str
    category: str
    operators: list[str]
