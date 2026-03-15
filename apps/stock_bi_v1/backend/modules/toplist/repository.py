from sqlalchemy import func, select

from apps.stock_bi_v1.backend.infrastructure.database import SessionLocal
from apps.stock_bi_v1.backend.models.db_models import TopList


def get_latest_trade_date() -> str:
    with SessionLocal() as session:
        return session.scalar(select(func.max(TopList.trade_date))) or ""


def get_daily_toplist(trade_date: str):
    with SessionLocal() as session:
        query = select(TopList).where(TopList.trade_date == trade_date).order_by(TopList.pct_chg.desc(), TopList.ts_code.asc())
        return list(session.scalars(query))


def get_stock_toplist_history(ts_code: str):
    with SessionLocal() as session:
        query = select(TopList).where(TopList.ts_code == ts_code).order_by(TopList.trade_date.desc())
        return list(session.scalars(query))
