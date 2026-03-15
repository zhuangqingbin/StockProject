from sqlalchemy import func, select

from apps.stock_bi_v1.backend.infrastructure.database import SessionLocal
from apps.stock_bi_v1.backend.models.db_models import Moneyflow, MoneyflowHsgt


def get_latest_trade_date() -> str:
    with SessionLocal() as session:
        return session.scalar(select(func.max(MoneyflowHsgt.trade_date))) or session.scalar(select(func.max(Moneyflow.trade_date))) or ""


def get_north_money(days: int):
    with SessionLocal() as session:
        query = select(MoneyflowHsgt).order_by(MoneyflowHsgt.trade_date.desc()).limit(days)
        return list(session.scalars(query))


def get_stock_flow(ts_code: str, days: int):
    with SessionLocal() as session:
        query = (
            select(Moneyflow)
            .where(Moneyflow.ts_code == ts_code)
            .order_by(Moneyflow.trade_date.desc())
            .limit(days)
        )
        return list(session.scalars(query))


def get_stock_flow_detail(ts_code: str, trade_date: str):
    with SessionLocal() as session:
        query = select(Moneyflow).where(Moneyflow.ts_code == ts_code, Moneyflow.trade_date == trade_date)
        return session.scalar(query)
