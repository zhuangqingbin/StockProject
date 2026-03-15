from __future__ import annotations

from typing import Optional

from apps.stock_bi_v1.backend.infrastructure.cache import cached
from apps.stock_bi_v1.backend.infrastructure.settings import CACHE_TTL_OVERVIEW, CACHE_TTL_RANKING
from apps.stock_bi_v1.backend.modules.market import repository


INDEX_NAMES = {
    "000001.SH": "上证指数",
    "399001.SZ": "深证成指",
    "399006.SZ": "创业板指",
    "000688.SH": "科创50",
    "399005.SZ": "中小100",
}


def _bucket_distribution(values: list[float]) -> dict[str, int]:
    buckets = {
        "-10~-7": 0,
        "-7~-5": 0,
        "-5~-3": 0,
        "-3~0": 0,
        "0": 0,
        "0~3": 0,
        "3~5": 0,
        "5~7": 0,
        "7~10": 0,
    }
    for value in values:
        if value <= -7:
            buckets["-10~-7"] += 1
        elif value <= -5:
            buckets["-7~-5"] += 1
        elif value <= -3:
            buckets["-5~-3"] += 1
        elif value < 0:
            buckets["-3~0"] += 1
        elif value == 0:
            buckets["0"] += 1
        elif value < 3:
            buckets["0~3"] += 1
        elif value <= 5:
            buckets["3~5"] += 1
        elif value <= 7:
            buckets["5~7"] += 1
        else:
            buckets["7~10"] += 1
    return buckets


def _resolve_trade_date(requested_date: Optional[str]) -> str:
    if requested_date:
        return requested_date
    latest_trade_date = repository.get_latest_trade_date()
    if latest_trade_date:
        return latest_trade_date
    return ""


@cached(ttl=CACHE_TTL_OVERVIEW)
def get_indices(trade_date: Optional[str] = None):
    resolved_date = _resolve_trade_date(trade_date)
    rows = repository.get_index_daily(resolved_date)
    return [
        {
            "ts_code": row.ts_code,
            "name": INDEX_NAMES.get(row.ts_code, row.ts_code),
            "close": float(row.close or 0),
            "pct_chg": float(row.pct_chg or 0),
            "amount": float(row.amount or 0),
        }
        for row in rows
    ]


@cached(ttl=CACHE_TTL_OVERVIEW)
def get_distribution(trade_date: Optional[str] = None):
    resolved_date = _resolve_trade_date(trade_date)
    return _bucket_distribution(repository.get_distribution_values(resolved_date))


@cached(ttl=CACHE_TTL_RANKING)
def get_ranking(trade_date: Optional[str] = None, sort_by: str = "pct_chg", order: str = "desc", limit: int = 20):
    resolved_date = _resolve_trade_date(trade_date)
    return repository.get_ranking(resolved_date, sort_by, order, limit)


@cached(ttl=CACHE_TTL_OVERVIEW)
def get_limit_stats(trade_date: Optional[str] = None):
    resolved_date = _resolve_trade_date(trade_date)
    row = repository.get_precomputed_limit(resolved_date)
    if row is None:
        return {
            "trade_date": resolved_date,
            "up_count": 0,
            "down_count": 0,
            "broken_count": 0,
            "broken_rate": 0.0,
            "tier_stats": {},
        }
    return {
        "trade_date": resolved_date,
        "up_count": int(row.up_count or 0),
        "down_count": int(row.down_count or 0),
        "broken_count": int(row.broken_count or 0),
        "broken_rate": float(row.broken_rate or 0),
        "tier_stats": row.tier_stats or {},
    }


@cached(ttl=CACHE_TTL_OVERVIEW)
def get_limit_list(trade_date: Optional[str] = None, limit_type: str = "up"):
    resolved_date = _resolve_trade_date(trade_date)
    row = repository.get_precomputed_limit(resolved_date)
    if row is None:
        return []
    if limit_type == "down":
        return row.down_limit_stocks or []
    return row.up_limit_stocks or []


@cached(ttl=CACHE_TTL_OVERVIEW)
def get_overview(trade_date: Optional[str] = None):
    resolved_date = _resolve_trade_date(trade_date)
    market_row = repository.get_precomputed_market(resolved_date)

    if market_row is None:
        return {
            "trade_date": resolved_date,
            "indices": get_indices(resolved_date),
            "distribution": get_distribution(resolved_date),
            "top_gainers": get_ranking(resolved_date, "pct_chg", "desc", 5),
            "top_losers": get_ranking(resolved_date, "pct_chg", "asc", 5),
            "top_amount": get_ranking(resolved_date, "amount", "desc", 5),
            "top_turnover": get_ranking(resolved_date, "turnover_rate", "desc", 5),
            "limit_stats": get_limit_stats(resolved_date),
        }

    return {
        "trade_date": resolved_date,
        "indices": get_indices(resolved_date),
        "distribution": market_row.distribution or {},
        "top_gainers": (market_row.top_gainers or [])[:5],
        "top_losers": (market_row.top_losers or [])[:5],
        "top_amount": (market_row.top_amount or [])[:5],
        "top_turnover": (market_row.top_turnover or [])[:5],
        "limit_stats": get_limit_stats(resolved_date),
    }
