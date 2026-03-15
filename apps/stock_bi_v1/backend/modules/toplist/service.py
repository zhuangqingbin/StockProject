from __future__ import annotations

from typing import Optional

from apps.stock_bi_v1.backend.modules.toplist import repository


def _serialize_rows(rows):
    return [
        {
            "ts_code": row.ts_code,
            "trade_date": row.trade_date,
            "name": row.name or row.ts_code,
            "close": float(row.close or 0),
            "pct_chg": float(row.pct_chg or 0),
            "turnover_rate": float(row.turnover_rate or 0),
            "amount": float(row.amount or 0),
            "l_buy": float(row.l_buy or 0),
            "l_sell": float(row.l_sell or 0),
            "net_amount": float(row.net_amount or 0),
            "reason": row.reason or "",
        }
        for row in rows
    ]


def get_daily(trade_date: Optional[str] = None):
    resolved_date = trade_date or repository.get_latest_trade_date()
    return _serialize_rows(repository.get_daily_toplist(resolved_date))


def get_stock_history(ts_code: str):
    return _serialize_rows(repository.get_stock_toplist_history(ts_code))
