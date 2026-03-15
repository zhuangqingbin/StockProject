from __future__ import annotations

from typing import Optional

import pandas as pd

from apps.stock_bi_v1.backend.infrastructure.cache import cached
from apps.stock_bi_v1.backend.infrastructure.settings import CACHE_TTL_KLINE_DAILY, CACHE_TTL_KLINE_WEEKLY, CACHE_TTL_SEARCH
from apps.stock_bi_v1.backend.modules.stock import repository


def _serialize_kline_rows(rows):
    return [
        {
            "trade_date": row.trade_date,
            "open": float(row.open or 0),
            "high": float(row.high or 0),
            "low": float(row.low or 0),
            "close": float(row.close or 0),
            "vol": float(row.vol or 0),
            "amount": float(row.amount or 0),
            "pct_chg": float(row.pct_chg or 0),
        }
        for row in rows
    ]


def _resample_rows(rows, rule: str):
    if not rows:
        return []

    frame = pd.DataFrame(_serialize_kline_rows(rows))
    frame["trade_date"] = pd.to_datetime(frame["trade_date"])
    frame = frame.set_index("trade_date")
    resampled = frame.resample(rule).agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "vol": "sum",
            "amount": "sum",
        }
    )
    resampled = resampled.dropna(subset=["open", "close"])
    resampled["pct_chg"] = resampled["close"].pct_change().fillna(0).mul(100)
    return [
        {
            "trade_date": trade_date.strftime("%Y%m%d"),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "vol": float(row["vol"]),
            "amount": float(row["amount"]),
            "pct_chg": float(row["pct_chg"]),
        }
        for trade_date, row in resampled.iterrows()
    ]


@cached(ttl=CACHE_TTL_SEARCH)
def search(query_text: str):
    rows = repository.search_stocks(query_text)
    return [
        {
            "ts_code": row.ts_code,
            "symbol": row.symbol or row.ts_code,
            "name": row.name or row.ts_code,
            "industry": row.industry or "",
            "market": row.market or "",
        }
        for row in rows
    ]


def get_profile(ts_code: str):
    trade_date = repository.get_latest_trade_date(ts_code)
    row = repository.get_stock_profile(ts_code, trade_date)
    if row is None:
        return {"ts_code": ts_code, "name": ts_code, "trade_date": trade_date}

    stock_basic, daily_kline, daily_basic = row
    return {
        "ts_code": stock_basic.ts_code,
        "symbol": stock_basic.symbol or stock_basic.ts_code,
        "name": stock_basic.name or stock_basic.ts_code,
        "industry": stock_basic.industry or "",
        "market": stock_basic.market or "",
        "exchange": stock_basic.exchange or "",
        "current_price": float(daily_kline.close or 0),
        "pct_chg": float(daily_kline.pct_chg or 0),
        "open": float(daily_kline.open or 0),
        "high": float(daily_kline.high or 0),
        "low": float(daily_kline.low or 0),
        "pre_close": float(daily_kline.pre_close or 0),
        "amount": float(daily_kline.amount or 0),
        "vol": float(daily_kline.vol or 0),
        "turnover_rate": float(getattr(daily_basic, "turnover_rate", 0) or 0),
        "pe_ttm": float(getattr(daily_basic, "pe_ttm", 0) or 0),
        "pb": float(getattr(daily_basic, "pb", 0) or 0),
        "ps_ttm": float(getattr(daily_basic, "ps_ttm", 0) or 0),
        "total_mv": float(getattr(daily_basic, "total_mv", 0) or 0),
        "circ_mv": float(getattr(daily_basic, "circ_mv", 0) or 0),
        "total_share": float(getattr(daily_basic, "total_share", 0) or 0),
        "float_share": float(getattr(daily_basic, "float_share", 0) or 0),
    }


@cached(ttl=CACHE_TTL_KLINE_DAILY)
def get_kline(ts_code: str, period: str = "daily", start: Optional[str] = None, end: Optional[str] = None):
    rows = repository.get_kline(ts_code, start, end)
    if period == "weekly":
        return _resample_rows(rows, "W")
    if period == "monthly":
        return _resample_rows(rows, "M")
    return _serialize_kline_rows(rows)


def get_valuation_history(ts_code: str, start: Optional[str] = None, end: Optional[str] = None):
    rows = repository.get_valuation_history(ts_code, start, end)
    return [
        {
            "trade_date": row.trade_date,
            "pe_ttm": float(row.pe_ttm or 0),
            "pb": float(row.pb or 0),
            "ps_ttm": float(row.ps_ttm or 0),
        }
        for row in rows
    ]


def get_peers(ts_code: str):
    trade_date = repository.get_latest_trade_date(ts_code)
    rows = repository.get_peers(ts_code, trade_date)
    return [
        {
            "ts_code": stock_basic.ts_code,
            "name": stock_basic.name or stock_basic.ts_code,
            "close": float(daily_kline.close or 0),
            "pct_chg": float(daily_kline.pct_chg or 0),
            "total_mv": float(getattr(daily_basic, "total_mv", 0) or 0),
            "pe_ttm": float(getattr(daily_basic, "pe_ttm", 0) or 0),
        }
        for stock_basic, daily_kline, daily_basic in rows
    ]


def get_history(ts_code: str, start: Optional[str] = None, end: Optional[str] = None, page: int = 0, size: int = 50):
    rows, total = repository.get_history(ts_code, start, end, page, size)
    return {"total": total, "page": page, "size": size, "items": _serialize_kline_rows(rows)}
