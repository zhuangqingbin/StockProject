from fastapi import APIRouter, Query

from apps.stock_bi_v1.backend.modules.flow import service


router = APIRouter(prefix="/api/flow", tags=["flow"])


@router.get("/north")
def north_money(days: int = Query(default=30, ge=1, le=240)):
    return service.get_north_money(days)


@router.get("/stock/{code}")
def stock_flow(code: str, days: int = Query(default=30, ge=1, le=240)):
    return service.get_stock_flow(code, days)


@router.get("/stock/{code}/detail")
def stock_flow_detail(code: str, date: str = Query(...)):
    return service.get_stock_flow_detail(code, date)
