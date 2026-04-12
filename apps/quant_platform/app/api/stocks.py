from fastapi import APIRouter, Query, HTTPException
from ..services.tushare_service import DataService
from loguru import logger

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/search")
async def search_stocks(keyword: str = Query("", description="Search keyword: stock code or name")):
    try:
        results = await DataService.get_stock_list(keyword)
        return {"code": 0, "data": results}
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(500, str(e))


@router.get("/daily/{ts_code}")
async def get_daily(
    ts_code: str,
    start_date: str = Query(..., description="Start date YYYYMMDD"),
    end_date: str = Query(..., description="End date YYYYMMDD"),
    indicators: str = Query("", description="Technical indicators, comma separated: MA5,MA20,MACD,KDJ,RSI,BOLL,VOL_MA"),
):
    try:
        data = await DataService.get_daily_data(ts_code, start_date, end_date)
        if not data:
            return {"code": 0, "data": {"data": [], "indicators": {}}}

        indicator_list = [i.strip() for i in indicators.split(",") if i.strip()]
        result = DataService.compute_indicators(data, indicator_list)
        return {"code": 0, "data": result}
    except Exception as e:
        logger.error(f"Get daily failed: {e}")
        raise HTTPException(500, str(e))


@router.get("/market/overview")
async def market_overview():
    try:
        result = await DataService.get_market_overview()
        return {"code": 0, "data": result}
    except Exception as e:
        logger.error(f"Get market overview failed: {e}")
        raise HTTPException(500, str(e))
