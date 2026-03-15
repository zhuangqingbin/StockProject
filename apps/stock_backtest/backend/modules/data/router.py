from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.stock_backtest.backend.engine.data_registry import get_feed_catalog
from apps.stock_backtest.backend.infrastructure.database import get_db_session
from apps.stock_backtest.backend.models.api_models import (
    BenchmarkResponse,
    DataOverviewResponse,
    FeedCatalogResponse,
    SeedMarketPayload,
    SymbolSearchResponse,
)
from apps.stock_backtest.backend.models.db_models import MarketDailyKlineModel, MarketStockBasicModel

from .service import build_data_overview, clear_data_cache, list_benchmarks


router = APIRouter(tags=["data"])


@router.get("/api/data/feeds", response_model=list[FeedCatalogResponse])
def list_feeds():
    return [
        {
            "feed_id": item.feed_id,
            "label": item.label,
            "description": item.description,
            "table_name": item.table_name,
            "primary": item.primary,
        }
        for item in get_feed_catalog()
    ]


@router.get("/api/data/symbols", response_model=list[SymbolSearchResponse])
def search_symbols(
    keyword: str = Query(default=""),
    industry: str = Query(default=""),
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_db_session),
):
    statement = select(MarketStockBasicModel).order_by(MarketStockBasicModel.ts_code.asc())
    if keyword:
        keyword_like = f"%{keyword}%"
        statement = statement.where(
            (MarketStockBasicModel.ts_code.like(keyword_like)) | (MarketStockBasicModel.name.like(keyword_like))
        )
    if industry:
        statement = statement.where(MarketStockBasicModel.industry == industry)
    return list(session.execute(statement.limit(limit)).scalars().all())


@router.get("/api/data/overview", response_model=DataOverviewResponse)
def get_data_overview(session: Session = Depends(get_db_session)):
    return build_data_overview(session)


@router.get("/api/data/benchmarks", response_model=list[BenchmarkResponse])
def get_benchmarks(session: Session = Depends(get_db_session)):
    return list_benchmarks(session)


@router.post("/api/dev/seed")
def seed_market_data(payload: SeedMarketPayload, session: Session = Depends(get_db_session)):
    for symbol in payload.symbols:
        session.merge(MarketStockBasicModel(**symbol.model_dump()))
    for record in payload.daily_kline:
        session.merge(MarketDailyKlineModel(**record.model_dump()))
    session.commit()
    clear_data_cache()
    return {"symbols": len(payload.symbols), "daily_kline": len(payload.daily_kline)}
