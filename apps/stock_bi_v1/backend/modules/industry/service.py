from __future__ import annotations

from typing import Optional

from apps.stock_bi_v1.backend.infrastructure.cache import cached
from apps.stock_bi_v1.backend.infrastructure.settings import CACHE_TTL_HEATMAP, CACHE_TTL_OVERVIEW
from apps.stock_bi_v1.backend.modules.industry import repository


@cached(ttl=CACHE_TTL_HEATMAP)
def get_heatmap(trade_date: Optional[str] = None):
    resolved_date = repository.get_trade_date(trade_date)
    rows = repository.get_precomputed_industries(resolved_date)
    return [
        {
            "industry": row.industry,
            "avg_pct_chg": float(row.avg_pct_chg or 0),
            "total_amount": float(row.total_amount or 0),
            "up_count": int(row.up_count or 0),
            "down_count": int(row.down_count or 0),
            "net_mf_amount": float(row.net_mf_amount or 0),
            "stock_count": int(row.stock_count or 0),
        }
        for row in rows
    ]


@cached(ttl=CACHE_TTL_OVERVIEW)
def get_detail(industry_name: str, trade_date: Optional[str] = None):
    resolved_date = repository.get_trade_date(trade_date)
    row = repository.get_industry_detail(industry_name, resolved_date)
    if row is None:
        return {
            "trade_date": resolved_date,
            "industry": industry_name,
            "avg_pct_chg": 0.0,
            "total_amount": 0.0,
            "up_count": 0,
            "down_count": 0,
            "net_mf_amount": 0.0,
            "stock_count": 0,
        }
    return {
        "trade_date": resolved_date,
        "industry": row.industry,
        "avg_pct_chg": float(row.avg_pct_chg or 0),
        "total_amount": float(row.total_amount or 0),
        "up_count": int(row.up_count or 0),
        "down_count": int(row.down_count or 0),
        "net_mf_amount": float(row.net_mf_amount or 0),
        "stock_count": int(row.stock_count or 0),
    }


def get_stocks(industry_name: str, trade_date: Optional[str] = None, sort_by: str = "pct_chg", order: str = "desc"):
    resolved_date = repository.get_trade_date(trade_date)
    return repository.get_industry_stocks(industry_name, resolved_date, sort_by, order)
