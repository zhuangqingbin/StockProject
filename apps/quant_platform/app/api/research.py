from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from sqlalchemy import select

from ..core.database import StockBasic, async_session
from ..services.research_service import get_research_overview
from ..services.research_snapshot_service import (
    get_research_factor_detail,
    get_research_factor_picks,
    get_research_factor_stock_detail,
    get_research_snapshot_manifest,
    list_research_factors,
)

router = APIRouter(prefix="/api/research", tags=["research"])


async def _stock_profile_map(ts_codes: list[str]) -> dict[str, dict[str, str | None]]:
    unique_codes = sorted({code for code in ts_codes if code})
    if not unique_codes:
        return {}
    async with async_session() as session:
        result = await session.execute(select(StockBasic).where(StockBasic.ts_code.in_(unique_codes)))
        rows = result.scalars().all()
    return {
        row.ts_code: {
            "stock_name": row.name,
            "industry": row.industry,
            "market": row.market,
            "symbol": row.symbol,
        }
        for row in rows
    }


async def _attach_profiles(rows: list[dict]) -> list[dict]:
    profile_map = await _stock_profile_map([row.get("ts_code", "") for row in rows])
    enriched: list[dict] = []
    for row in rows:
        profile = profile_map.get(row.get("ts_code"), {})
        enriched.append(
            {
                **row,
                "stock_name": profile.get("stock_name"),
                "industry": row.get("industry") or profile.get("industry"),
                "market": profile.get("market"),
                "symbol": profile.get("symbol"),
            }
        )
    return enriched


@router.get("/overview")
async def research_overview():
    try:
        return {"code": 0, "data": get_research_overview()}
    except Exception as exc:
        logger.error(f"Research overview failed: {exc}")
        raise HTTPException(500, str(exc))


@router.get("/snapshot/latest")
async def research_latest_snapshot():
    try:
        return {"code": 0, "data": get_research_snapshot_manifest()}
    except Exception as exc:
        logger.error(f"Research snapshot failed: {exc}")
        raise HTTPException(500, str(exc))


@router.get("/factors")
async def research_factors(
    limit: int = Query(30, ge=1, le=200),
    qualified_only: bool = Query(False),
):
    try:
        return {"code": 0, "data": list_research_factors(limit=limit, qualified_only=qualified_only)}
    except Exception as exc:
        logger.error(f"Research factors failed: {exc}")
        raise HTTPException(500, str(exc))


@router.get("/factors/{factor_name}")
async def research_factor_detail(factor_name: str):
    try:
        detail = get_research_factor_detail(factor_name)
        if detail is None:
            raise HTTPException(404, f"Factor {factor_name} not found")
        detail["picks"] = await _attach_profiles(list(detail.get("picks", [])))
        return {"code": 0, "data": detail}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Research factor detail failed: {exc}")
        raise HTTPException(500, str(exc))


@router.get("/factors/{factor_name}/picks")
async def research_factor_picks(
    factor_name: str,
    limit: int = Query(20, ge=1, le=100),
):
    try:
        payload = get_research_factor_picks(factor_name, limit=limit)
        if payload is None:
            raise HTTPException(404, f"Factor {factor_name} not found")
        payload["rows"] = await _attach_profiles(list(payload.get("rows", [])))
        return {"code": 0, "data": payload}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Research factor picks failed: {exc}")
        raise HTTPException(500, str(exc))


@router.get("/factors/{factor_name}/stocks/{ts_code}")
async def research_factor_stock_detail(
    factor_name: str,
    ts_code: str,
    history_window: int = Query(120, ge=20, le=500),
):
    try:
        payload = get_research_factor_stock_detail(
            factor_name,
            ts_code,
            history_window=history_window,
        )
        if payload is None:
            raise HTTPException(404, f"Factor {factor_name} or stock {ts_code} not found")
        payload["stock_profile"] = (await _stock_profile_map([ts_code])).get(ts_code)
        return {"code": 0, "data": payload}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Research factor stock detail failed: {exc}")
        raise HTTPException(500, str(exc))
