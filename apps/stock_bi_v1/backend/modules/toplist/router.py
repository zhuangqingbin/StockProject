from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from apps.stock_bi_v1.backend.modules.toplist import service


router = APIRouter(prefix="/api/toplist", tags=["toplist"])


@router.get("/daily")
def daily_toplist(date: Optional[str] = None):
    return service.get_daily(date)


@router.get("/stock/{code}")
def stock_toplist_history(code: str):
    return service.get_stock_history(code)
