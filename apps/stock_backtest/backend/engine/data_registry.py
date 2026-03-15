from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeedDefinition:
    feed_id: str
    label: str
    description: str
    table_name: str
    primary: bool = False
    merge_columns: tuple[str, ...] = ()


FEED_CATALOG: dict[str, FeedDefinition] = {
    "daily_kline": FeedDefinition(
        feed_id="daily_kline",
        label="日线行情",
        description="基础 OHLCV 日线行情",
        table_name="daily_kline",
        primary=True,
        merge_columns=("open", "high", "low", "close", "vol", "amount"),
    ),
    "daily_basic": FeedDefinition(
        feed_id="daily_basic",
        label="基本面",
        description="估值与换手率等日频基础指标",
        table_name="daily_basic",
        merge_columns=("turnover_rate", "pe_ttm"),
    ),
    "moneyflow": FeedDefinition(
        feed_id="moneyflow",
        label="资金流",
        description="主力资金净流入等日频资金流向",
        table_name="moneyflow",
        merge_columns=("net_mf_amount",),
    ),
    "index_daily": FeedDefinition(
        feed_id="index_daily",
        label="指数数据",
        description="主要指数日线序列",
        table_name="index_daily",
        merge_columns=("close",),
    ),
    "top_list": FeedDefinition(
        feed_id="top_list",
        label="龙虎榜",
        description="龙虎榜席位和净额摘要",
        table_name="top_list",
        merge_columns=("net_amount",),
    ),
    "stock_basic": FeedDefinition(
        feed_id="stock_basic",
        label="股票静态信息",
        description="股票名称、行业、板块等静态信息",
        table_name="stock_basic",
        merge_columns=("name", "industry", "market"),
    ),
}


def get_feed_catalog() -> list[FeedDefinition]:
    return list(FEED_CATALOG.values())


def get_feed_definition(feed_id: str) -> FeedDefinition:
    if feed_id not in FEED_CATALOG:
        raise KeyError(f"Unknown feed id: {feed_id}")
    return FEED_CATALOG[feed_id]
