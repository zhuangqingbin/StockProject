from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from apps.stock_bi_v1.backend.modules.stock import service


router = APIRouter(prefix="/api/stock", tags=["stock"])


@router.get("/search")
def stock_search(q: str = Query(..., min_length=1)):
    return service.search(q)


@router.get("/{code}/profile")
def stock_profile(code: str):
    return service.get_profile(code)


@router.get("/{code}/kline")
def stock_kline(code: str, period: str = Query(default="daily"), start: Optional[str] = None, end: Optional[str] = None):
    return service.get_kline(code, period, start, end)


@router.get("/{code}/valuation-history")
def stock_valuation_history(code: str, start: Optional[str] = None, end: Optional[str] = None):
    return service.get_valuation_history(code, start, end)


@router.get("/{code}/peers")
def stock_peers(code: str):
    return service.get_peers(code)


@router.get("/{code}/history")
def stock_history(
    code: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    page: int = Query(default=0, ge=0),
    size: int = Query(default=50, ge=1, le=200),
):
    return service.get_history(code, start, end, page, size)
