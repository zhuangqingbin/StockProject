from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from threading import Lock
from time import monotonic
from typing import Any
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.stock_backtest.backend.engine.data_registry import get_feed_catalog
from apps.stock_backtest.backend.models.db_models import (
    MarketDailyBasicModel,
    MarketDailyKlineModel,
    MarketIndexDailyModel,
    MarketMoneyflowModel,
    MarketStockBasicModel,
    MarketTopListModel,
)


BENCHMARK_NAME_MAP = {
    "000001.SH": "上证指数",
    "000300.SH": "沪深300",
    "000852.SH": "中证1000",
    "000905.SH": "中证500",
    "399001.SZ": "深证成指",
    "399006.SZ": "创业板指",
}

FEED_MODEL_MAP = {
    "daily_kline": MarketDailyKlineModel,
    "daily_basic": MarketDailyBasicModel,
    "moneyflow": MarketMoneyflowModel,
    "index_daily": MarketIndexDailyModel,
    "top_list": MarketTopListModel,
    "stock_basic": MarketStockBasicModel,
}

_CACHE_TTL_SECONDS = 45.0
_cache_lock = Lock()
_cache_store: dict[tuple[str, str], tuple[float, Any]] = {}


def normalize_market_trade_date(value: Any) -> Optional[date]:
    if value in (None, ""):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        cleaned = value.strip()
        for pattern in ("%Y%m%d", "%Y-%m-%d"):
            try:
                return datetime.strptime(cleaned, pattern).date()
            except ValueError:
                continue
    return None


def _database_cache_key(session: Session, scope: str) -> tuple[str, str]:
    bind = session.get_bind()
    assert bind is not None
    return (str(bind.url), scope)


def _read_or_build_cached(session: Session, scope: str, factory: Callable[[], Any]) -> Any:
    cache_key = _database_cache_key(session, scope)
    now = monotonic()
    with _cache_lock:
        cached = _cache_store.get(cache_key)
        if cached is not None:
            timestamp, payload = cached
            if now - timestamp < _CACHE_TTL_SECONDS:
                return payload

    payload = factory()
    with _cache_lock:
        _cache_store[cache_key] = (now, payload)
    return payload


def _count_rows(session: Session, model: type) -> int:
    return int(session.execute(select(func.count()).select_from(model)).scalar_one())


def _count_symbols(session: Session, model: type) -> int:
    if not hasattr(model, "ts_code"):
        return 0
    return int(session.execute(select(func.count(func.distinct(model.ts_code)))).scalar_one())


def _latest_trade_date(session: Session, model: type) -> Optional[date]:
    if not hasattr(model, "trade_date"):
        return None
    return normalize_market_trade_date(session.execute(select(func.max(model.trade_date))).scalar_one())


def _earliest_trade_date(session: Session, model: type) -> Optional[date]:
    if not hasattr(model, "trade_date"):
        return None
    return normalize_market_trade_date(session.execute(select(func.min(model.trade_date))).scalar_one())


def build_data_overview(session: Session) -> dict[str, Any]:
    def factory() -> dict[str, Any]:
        feed_health = []
        for feed in get_feed_catalog():
            model = FEED_MODEL_MAP[feed.feed_id]
            feed_health.append(
                {
                    "feed_id": feed.feed_id,
                    "label": feed.label,
                    "description": feed.description,
                    "table_name": feed.table_name,
                    "primary": feed.primary,
                    "record_count": _count_rows(session, model),
                    "symbol_count": _count_symbols(session, model),
                    "earliest_trade_date": _earliest_trade_date(session, model),
                    "latest_trade_date": _latest_trade_date(session, model),
                }
            )

        top_industries = [
            {
                "industry": industry or "未分类",
                "symbol_count": int(symbol_count),
            }
            for industry, symbol_count in session.execute(
                select(MarketStockBasicModel.industry, func.count(MarketStockBasicModel.ts_code))
                .group_by(MarketStockBasicModel.industry)
                .order_by(func.count(MarketStockBasicModel.ts_code).desc(), MarketStockBasicModel.industry.asc())
                .limit(8)
            ).all()
        ]

        return {
            "symbol_count": _count_rows(session, MarketStockBasicModel),
            "industry_count": int(
                session.execute(select(func.count(func.distinct(MarketStockBasicModel.industry)))).scalar_one()
            ),
            "benchmark_count": _count_symbols(session, MarketIndexDailyModel),
            "feed_health": feed_health,
            "top_industries": top_industries,
        }

    return _read_or_build_cached(session, "data_overview", factory)


def list_benchmarks(session: Session) -> list[dict[str, Any]]:
    def factory() -> list[dict[str, Any]]:
        return [
            {
                "ts_code": ts_code,
                "name": BENCHMARK_NAME_MAP.get(ts_code, ts_code),
                "latest_trade_date": normalize_market_trade_date(latest_trade_date),
            }
            for ts_code, latest_trade_date in session.execute(
                select(MarketIndexDailyModel.ts_code, func.max(MarketIndexDailyModel.trade_date))
                .group_by(MarketIndexDailyModel.ts_code)
                .order_by(MarketIndexDailyModel.ts_code.asc())
            ).all()
        ]

    return _read_or_build_cached(session, "benchmarks", factory)


def clear_data_cache() -> None:
    with _cache_lock:
        _cache_store.clear()
