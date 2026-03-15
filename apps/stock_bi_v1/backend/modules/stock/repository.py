from __future__ import annotations

from typing import Optional

from sqlalchemy import and_, func, select

from apps.stock_bi_v1.backend.infrastructure.database import SessionLocal
from apps.stock_bi_v1.backend.models.db_models import DailyBasic, DailyKline, StockBasic


def search_stocks(query_text: str, limit: int = 20):
    like_value = f"%{query_text}%"
    with SessionLocal() as session:
        query = (
            select(StockBasic)
            .where((StockBasic.ts_code.like(like_value)) | (StockBasic.name.like(like_value)) | (StockBasic.symbol.like(like_value)))
            .order_by(StockBasic.ts_code.asc())
            .limit(limit)
        )
        return list(session.scalars(query))


def get_latest_trade_date(ts_code: Optional[str] = None) -> str:
    with SessionLocal() as session:
        query = select(func.max(DailyKline.trade_date))
        if ts_code:
            query = query.where(DailyKline.ts_code == ts_code)
        return session.scalar(query) or ""


def get_stock_profile(ts_code: str, trade_date: str):
    with SessionLocal() as session:
        query = (
            select(StockBasic, DailyKline, DailyBasic)
            .join(DailyKline, DailyKline.ts_code == StockBasic.ts_code)
            .outerjoin(
                DailyBasic,
                and_(DailyBasic.ts_code == DailyKline.ts_code, DailyBasic.trade_date == DailyKline.trade_date),
            )
            .where(StockBasic.ts_code == ts_code, DailyKline.trade_date == trade_date)
        )
        return session.execute(query).first()


def get_kline(ts_code: str, start: Optional[str] = None, end: Optional[str] = None):
    with SessionLocal() as session:
        query = select(DailyKline).where(DailyKline.ts_code == ts_code)
        if start:
            query = query.where(DailyKline.trade_date >= start)
        if end:
            query = query.where(DailyKline.trade_date <= end)
        query = query.order_by(DailyKline.trade_date.asc())
        return list(session.scalars(query))


def get_valuation_history(ts_code: str, start: Optional[str] = None, end: Optional[str] = None):
    with SessionLocal() as session:
        query = select(DailyBasic).where(DailyBasic.ts_code == ts_code)
        if start:
            query = query.where(DailyBasic.trade_date >= start)
        if end:
            query = query.where(DailyBasic.trade_date <= end)
        query = query.order_by(DailyBasic.trade_date.asc())
        return list(session.scalars(query))


def get_peers(ts_code: str, trade_date: str):
    with SessionLocal() as session:
        industry = session.scalar(select(StockBasic.industry).where(StockBasic.ts_code == ts_code))
        if not industry:
            return []
        query = (
            select(StockBasic, DailyKline, DailyBasic)
            .join(DailyKline, DailyKline.ts_code == StockBasic.ts_code)
            .outerjoin(
                DailyBasic,
                and_(DailyBasic.ts_code == DailyKline.ts_code, DailyBasic.trade_date == DailyKline.trade_date),
            )
            .where(StockBasic.industry == industry, DailyKline.trade_date == trade_date)
            .order_by(DailyBasic.total_mv.desc().nullslast(), StockBasic.ts_code.asc())
            .limit(20)
        )
        return list(session.execute(query))


def get_history(ts_code: str, start: Optional[str] = None, end: Optional[str] = None, page: int = 0, size: int = 50):
    with SessionLocal() as session:
        filters = [DailyKline.ts_code == ts_code]
        if start:
            filters.append(DailyKline.trade_date >= start)
        if end:
            filters.append(DailyKline.trade_date <= end)

        total = session.scalar(select(func.count()).select_from(DailyKline).where(*filters)) or 0
        query = (
            select(DailyKline)
            .where(*filters)
            .order_by(DailyKline.trade_date.desc())
            .offset(page * size)
            .limit(size)
        )
        return list(session.scalars(query)), int(total)
