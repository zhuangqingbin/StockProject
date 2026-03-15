from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select

from apps.stock_bi_v1.backend.infrastructure.database import SessionLocal
from apps.stock_bi_v1.backend.models.db_models import DailyBasic, DailyKline, Moneyflow, PrecomputedIndustry, StockBasic


INDUSTRY_SORT_COLUMNS = {
    "pct_chg": DailyKline.pct_chg,
    "amount": DailyKline.amount,
    "turnover_rate": DailyBasic.turnover_rate,
    "pe_ttm": DailyBasic.pe_ttm,
    "net_mf_amount": Moneyflow.net_mf_amount,
}


def _resolve_trade_date(requested_date: Optional[str]) -> str:
    if requested_date:
        return requested_date
    with SessionLocal() as session:
        for model in (PrecomputedIndustry, DailyKline):
            value = session.scalar(select(func.max(model.trade_date)))
            if value:
                return value
    return ""


def get_trade_date(requested_date: Optional[str]) -> str:
    return _resolve_trade_date(requested_date)


def get_precomputed_industries(trade_date: str):
    with SessionLocal() as session:
        query = (
            select(PrecomputedIndustry)
            .where(PrecomputedIndustry.trade_date == trade_date)
            .order_by(PrecomputedIndustry.avg_pct_chg.desc(), PrecomputedIndustry.industry.asc())
        )
        return list(session.scalars(query))


def get_industry_detail(industry_name: str, trade_date: str):
    with SessionLocal() as session:
        query = select(PrecomputedIndustry).where(
            PrecomputedIndustry.trade_date == trade_date,
            PrecomputedIndustry.industry == industry_name,
        )
        return session.scalar(query)


def get_industry_stocks(industry_name: str, trade_date: str, sort_by: str, order: str):
    sort_column = INDUSTRY_SORT_COLUMNS.get(sort_by, DailyKline.pct_chg)
    sort_order = sort_column.asc() if order == "asc" else sort_column.desc()
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
                DailyBasic.pe_ttm,
                Moneyflow.net_mf_amount,
            )
            .join(StockBasic, StockBasic.ts_code == DailyKline.ts_code)
            .outerjoin(
                DailyBasic,
                (DailyBasic.ts_code == DailyKline.ts_code) & (DailyBasic.trade_date == DailyKline.trade_date),
            )
            .outerjoin(
                Moneyflow,
                (Moneyflow.ts_code == DailyKline.ts_code) & (Moneyflow.trade_date == DailyKline.trade_date),
            )
            .where(DailyKline.trade_date == trade_date, StockBasic.industry == industry_name)
            .order_by(sort_order, DailyKline.ts_code.asc())
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
                "pe_ttm": float(row.pe_ttm or 0),
                "net_mf_amount": float(row.net_mf_amount or 0),
            }
            for row in session.execute(query)
        ]
