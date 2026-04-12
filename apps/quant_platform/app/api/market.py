from fastapi import APIRouter, Query, HTTPException
from ..services.tushare_service import TushareService, DataService
from ..core.database import async_session, StockBasic, StockDaily
from sqlalchemy import select, func, text
from loguru import logger
from datetime import datetime
import asyncio

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/heatmap")
async def sector_heatmap(trade_date: str = Query("", description="Trade date YYYYMMDD")):
    try:
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')

        async with async_session() as session:
            result = await session.execute(
                select(func.max(StockDaily.trade_date)).where(
                    StockDaily.trade_date <= trade_date
                )
            )
            actual_date = result.scalar()
            if not actual_date:
                return {"code": 0, "data": {"sectors": [], "date": trade_date}}

            result = await session.execute(text("""
                SELECT b.industry,
                       COUNT(*) as stock_count,
                       AVG(d.pct_chg) as avg_pct_chg,
                       SUM(CASE WHEN d.pct_chg > 0 THEN 1 ELSE 0 END) as up_count,
                       SUM(CASE WHEN d.pct_chg < 0 THEN 1 ELSE 0 END) as down_count,
                       SUM(d.amount) as total_amount,
                       MAX(d.pct_chg) as max_pct_chg,
                       MIN(d.pct_chg) as min_pct_chg
                FROM stock_daily d
                JOIN stock_basic b ON d.ts_code = b.ts_code
                WHERE d.trade_date = :date AND b.industry IS NOT NULL AND b.industry != ''
                GROUP BY b.industry
                ORDER BY avg_pct_chg DESC
            """), {"date": actual_date})

            rows = result.fetchall()
            sectors = []
            for row in rows:
                sectors.append({
                    "industry": row[0],
                    "stock_count": row[1],
                    "avg_pct_chg": round(row[2], 2) if row[2] else 0,
                    "up_count": row[3] or 0,
                    "down_count": row[4] or 0,
                    "total_amount": round(row[5] / 10000, 2) if row[5] else 0,
                    "max_pct_chg": round(row[6], 2) if row[6] else 0,
                    "min_pct_chg": round(row[7], 2) if row[7] else 0,
                })

            return {"code": 0, "data": {"sectors": sectors, "date": actual_date}}
    except Exception as e:
        logger.error(f"Heatmap failed: {e}")
        raise HTTPException(500, str(e))


@router.get("/top-stocks")
async def top_stocks(
    sort_by: str = Query("pct_chg", description="Sort field: pct_chg, amount, vol"),
    direction: str = Query("desc", description="Sort direction: asc, desc"),
    limit: int = Query(20, description="Result count"),
    trade_date: str = Query("", description="Trade date"),
):
    try:
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')

        valid_fields = {"pct_chg", "amount", "vol"}
        if sort_by not in valid_fields:
            sort_by = "pct_chg"
        order = "DESC" if direction == "desc" else "ASC"

        async with async_session() as session:
            result = await session.execute(
                select(func.max(StockDaily.trade_date)).where(
                    StockDaily.trade_date <= trade_date
                )
            )
            actual_date = result.scalar() or trade_date

            result = await session.execute(text(
                f"SELECT d.ts_code, b.name, b.industry, "
                f"       d.close, d.pct_chg, d.vol, d.amount, d.`change` "
                f"FROM stock_daily d "
                f"JOIN stock_basic b ON d.ts_code = b.ts_code "
                f"WHERE d.trade_date = :date "
                f"ORDER BY d.{sort_by} {order} "
                f"LIMIT :limit"
            ), {"date": actual_date, "limit": limit})

            rows = result.fetchall()
            stocks = [{
                "ts_code": r[0], "name": r[1], "industry": r[2],
                "close": r[3], "pct_chg": round(r[4], 2) if r[4] else 0,
                "volume": r[5], "amount": r[6], "change": r[7],
            } for r in rows]

            return {"code": 0, "data": {"stocks": stocks, "date": actual_date}}
    except Exception as e:
        logger.error(f"Top stocks failed: {e}")
        raise HTTPException(500, str(e))


@router.get("/compare")
async def compare_stocks(
    codes: str = Query(..., description="Stock codes, comma separated: 000001.SZ,600519.SH"),
    start_date: str = Query(...),
    end_date: str = Query(...),
):
    try:
        code_list = [c.strip() for c in codes.split(",") if c.strip()]
        if len(code_list) < 2:
            raise HTTPException(400, "At least 2 stocks required")
        if len(code_list) > 6:
            raise HTTPException(400, "Max 6 stocks for comparison")

        results = {}
        for code in code_list:
            data = await DataService.get_daily_data(code, start_date, end_date)
            if data:
                first_close = data[0]['close']
                normalized = [{
                    "date": d['date'],
                    "close": round(d['close'] / first_close * 100, 2),
                    "raw_close": d['close'],
                    "pct_chg": d.get('pct_chg', 0),
                } for d in data]

                async with async_session() as session:
                    r = await session.execute(
                        select(StockBasic.name).where(StockBasic.ts_code == code)
                    )
                    name = r.scalar() or code

                results[code] = {
                    "name": name,
                    "data": normalized,
                    "total_return": round((data[-1]['close'] / first_close - 1) * 100, 2),
                }

        return {"code": 0, "data": results}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Compare failed: {e}")
        raise HTTPException(500, str(e))


@router.get("/moneyflow/{ts_code}")
async def money_flow(
    ts_code: str,
    start_date: str = Query(...),
    end_date: str = Query(...),
):
    try:
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None, TushareService.fetch_moneyflow, ts_code, start_date, end_date
        )
        if df is None or df.empty:
            return {"code": 0, "data": []}

        df = df.sort_values('trade_date').reset_index(drop=True)
        records = df.to_dict('records')
        return {"code": 0, "data": records}
    except Exception as e:
        logger.error(f"Money flow failed: {e}")
        raise HTTPException(500, str(e))


@router.get("/toplist")
async def top_list(trade_date: str = Query(...)):
    try:
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None, TushareService.fetch_top_list, trade_date
        )
        if df is None or df.empty:
            return {"code": 0, "data": []}

        records = df.head(30).to_dict('records')
        return {"code": 0, "data": records}
    except Exception as e:
        logger.error(f"Top list failed: {e}")
        raise HTTPException(500, str(e))


@router.get("/statistics")
async def market_statistics():
    try:
        async with async_session() as session:
            stock_count = (await session.execute(
                select(func.count(StockBasic.ts_code))
            )).scalar() or 0

            daily_count = (await session.execute(
                select(func.count(StockDaily.id))
            )).scalar() or 0

            latest_date = (await session.execute(
                select(func.max(StockDaily.trade_date))
            )).scalar() or "N/A"

            industry_count = (await session.execute(
                select(func.count(func.distinct(StockBasic.industry)))
            )).scalar() or 0

        return {"code": 0, "data": {
            "stock_count": stock_count,
            "daily_records": daily_count,
            "latest_date": latest_date,
            "industry_count": industry_count,
        }}
    except Exception as e:
        logger.error(f"Statistics failed: {e}")
        raise HTTPException(500, str(e))
