from __future__ import annotations

from collections import defaultdict

from sqlalchemy import delete, select

from apps.stock_bi_v1.backend.infrastructure.database import SessionLocal
from apps.stock_bi_v1.backend.models.db_models import (
    DailyBasic,
    DailyKline,
    Moneyflow,
    PrecomputedIndustry,
    PrecomputedLimit,
    PrecomputedMarket,
    StockBasic,
    StockStkLimit,
)


def _to_float(value: object) -> float:
    return float(value or 0)


def get_equity_snapshot_rows(trade_date: str) -> list[dict[str, object]]:
    with SessionLocal() as session:
        query = (
            select(
                DailyKline.ts_code.label("ts_code"),
                StockBasic.name.label("name"),
                StockBasic.industry.label("industry"),
                DailyKline.close.label("close"),
                DailyKline.pct_chg.label("pct_chg"),
                DailyKline.amount.label("amount"),
                DailyBasic.turnover_rate.label("turnover_rate"),
                Moneyflow.net_mf_amount.label("net_mf_amount"),
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
            .where(DailyKline.trade_date == trade_date)
        )
        rows = session.execute(query).mappings().all()
    return [
        {
            "ts_code": row["ts_code"],
            "name": row["name"] or row["ts_code"],
            "industry": row["industry"] or "",
            "close": _to_float(row["close"]),
            "pct_chg": _to_float(row["pct_chg"]),
            "amount": _to_float(row["amount"]),
            "turnover_rate": _to_float(row["turnover_rate"]),
            "net_mf_amount": _to_float(row["net_mf_amount"]),
        }
        for row in rows
    ]


def get_limit_snapshot_rows(trade_date: str) -> list[dict[str, object]]:
    with SessionLocal() as session:
        query = (
            select(
                DailyKline.ts_code.label("ts_code"),
                StockBasic.name.label("name"),
                StockBasic.industry.label("industry"),
                DailyKline.close.label("close"),
                DailyKline.high.label("high"),
                DailyKline.amount.label("amount"),
                DailyKline.pct_chg.label("pct_chg"),
                StockStkLimit.up_limit.label("up_limit"),
                StockStkLimit.down_limit.label("down_limit"),
            )
            .join(
                StockStkLimit,
                (StockStkLimit.ts_code == DailyKline.ts_code) & (StockStkLimit.trade_date == DailyKline.trade_date),
            )
            .join(StockBasic, StockBasic.ts_code == DailyKline.ts_code)
            .where(DailyKline.trade_date == trade_date)
        )
        rows = session.execute(query).mappings().all()
    return [
        {
            "ts_code": row["ts_code"],
            "name": row["name"] or row["ts_code"],
            "industry": row["industry"] or "",
            "close": _to_float(row["close"]),
            "high": _to_float(row["high"]),
            "amount": _to_float(row["amount"]),
            "pct_chg": _to_float(row["pct_chg"]),
            "up_limit": _to_float(row["up_limit"]),
            "down_limit": _to_float(row["down_limit"]),
        }
        for row in rows
    ]


def get_limit_up_history(ts_codes: list[str], trade_date: str) -> dict[str, list[dict[str, object]]]:
    if not ts_codes:
        return {}

    with SessionLocal() as session:
        query = (
            select(
                DailyKline.ts_code.label("ts_code"),
                DailyKline.trade_date.label("trade_date"),
                DailyKline.close.label("close"),
                StockStkLimit.up_limit.label("up_limit"),
            )
            .join(
                StockStkLimit,
                (StockStkLimit.ts_code == DailyKline.ts_code) & (StockStkLimit.trade_date == DailyKline.trade_date),
            )
            .where(DailyKline.ts_code.in_(ts_codes), DailyKline.trade_date <= trade_date)
            .order_by(DailyKline.ts_code.asc(), DailyKline.trade_date.desc())
        )
        rows = session.execute(query).mappings().all()

    history: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        history[row["ts_code"]].append(
            {
                "trade_date": row["trade_date"],
                "is_up_limit": _to_float(row["close"]) >= _to_float(row["up_limit"]),
            }
        )
    return dict(history)


def replace_precomputed_rows(
    trade_date: str,
    market_payload: dict[str, object],
    industry_payloads: list[dict[str, object]],
    limit_payload: dict[str, object],
) -> None:
    with SessionLocal() as session:
        session.execute(delete(PrecomputedIndustry).where(PrecomputedIndustry.trade_date == trade_date))
        session.execute(delete(PrecomputedMarket).where(PrecomputedMarket.trade_date == trade_date))
        session.execute(delete(PrecomputedLimit).where(PrecomputedLimit.trade_date == trade_date))
        session.add(PrecomputedMarket(trade_date=trade_date, **market_payload))
        session.add(PrecomputedLimit(trade_date=trade_date, **limit_payload))
        session.add_all(PrecomputedIndustry(trade_date=trade_date, **payload) for payload in industry_payloads)
        session.commit()
