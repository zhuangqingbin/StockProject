from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from apps.stock_bi_v1.backend.modules.industry import service


router = APIRouter(prefix="/api/industry", tags=["industry"])


@router.get("/heatmap")
def industry_heatmap(date: Optional[str] = None):
    return service.get_heatmap(date)


@router.get("/detail")
def industry_detail(name: str = Query(...), date: Optional[str] = None):
    return service.get_detail(name, date)


@router.get("/stocks")
def industry_stocks(
    name: str = Query(...),
    sort_by: str = Query(default="pct_chg"),
    order: str = Query(default="desc"),
    date: Optional[str] = None,
):
    return service.get_stocks(name, date, sort_by, order)
