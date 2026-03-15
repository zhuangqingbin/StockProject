from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select

from apps.stock_bi_v1.backend.infrastructure.database import SessionLocal
from apps.stock_bi_v1.backend.models.db_models import DailyBasic, DailyKline, IndexDaily, PrecomputedLimit, PrecomputedMarket, StockBasic


RANKING_COLUMNS = {
    "pct_chg": DailyKline.pct_chg,
    "amount": DailyKline.amount,
    "turnover_rate": DailyBasic.turnover_rate,
}


def get_latest_trade_date() -> Optional[str]:
    with SessionLocal() as session:
        for model in (PrecomputedMarket, IndexDaily, DailyKline):
            value = session.scalar(select(func.max(model.trade_date)))
            if value:
                return value
    return None


def get_index_daily(trade_date: str):
    with SessionLocal() as session:
        query = (
            select(IndexDaily)
            .where(IndexDaily.trade_date == trade_date)
            .order_by(IndexDaily.ts_code)
        )
        return list(session.scalars(query))


def get_precomputed_market(trade_date: str):
    with SessionLocal() as session:
        return session.get(PrecomputedMarket, trade_date)


def get_precomputed_limit(trade_date: str):
    with SessionLocal() as session:
        return session.get(PrecomputedLimit, trade_date)


def get_distribution_values(trade_date: str) -> list[float]:
    with SessionLocal() as session:
        query = select(DailyKline.pct_chg).where(DailyKline.trade_date == trade_date)
        return [row[0] or 0.0 for row in session.execute(query).all()]


def get_ranking(trade_date: str, sort_by: str, order: str, limit: int):
    ranking_column = RANKING_COLUMNS.get(sort_by, DailyKline.pct_chg)
    ranking_order = ranking_column.asc() if order == "asc" else ranking_column.desc()

    with SessionLocal() as session:
        query = (
            select(
                DailyKline.ts_code,
                StockBasic.name,
                StockBasic.industry,
                DailyKline.close,
                DailyKline.pct_chg,
                DailyKline.amount,
                DailyBasic.turnover_rate,
            )
            .join(StockBasic, StockBasic.ts_code == DailyKline.ts_code)
            .outerjoin(
                DailyBasic,
                (DailyBasic.ts_code == DailyKline.ts_code) & (DailyBasic.trade_date == DailyKline.trade_date),
            )
            .where(DailyKline.trade_date == trade_date)
            .order_by(ranking_order, DailyKline.ts_code.asc())
            .limit(limit)
        )
        return [
            {
                "ts_code": row.ts_code,
                "name": row.name or row.ts_code,
                "industry": row.industry or "",
                "close": float(row.close or 0),
                "pct_chg": float(row.pct_chg or 0),
                "amount": float(row.amount or 0),
                "turnover_rate": float(row.turnover_rate or 0),
            }
            for row in session.execute(query)
        ]
