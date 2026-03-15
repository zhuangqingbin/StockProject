from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from apps.stock_bi_v1.backend.modules.market import service


router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/overview")
def market_overview(date: Optional[str] = None):
    return service.get_overview(date)


@router.get("/indices")
def market_indices(date: Optional[str] = None):
    return service.get_indices(date)


@router.get("/distribution")
def market_distribution(date: Optional[str] = None):
    return service.get_distribution(date)


@router.get("/ranking")
def market_ranking(
    sort_by: str = Query(default="pct_chg"),
    order: str = Query(default="desc"),
    limit: int = Query(default=20, ge=1, le=100),
    date: Optional[str] = None,
):
    return service.get_ranking(date, sort_by, order, limit)


@router.get("/limit-stats")
def market_limit_stats(date: Optional[str] = None):
    return service.get_limit_stats(date)


@router.get("/limit-list")
def market_limit_list(type: str = Query(default="up"), date: Optional[str] = None):
    return service.get_limit_list(date, type)
