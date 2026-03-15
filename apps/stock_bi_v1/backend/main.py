from __future__ import annotations

from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.stock_bi_v1.backend.infrastructure.database import create_all
from apps.stock_bi_v1.backend.models import db_models as _db_models  # noqa: F401
from apps.stock_bi_v1.backend.modules.flow.router import router as flow_router
from apps.stock_bi_v1.backend.modules.industry.router import router as industry_router
from apps.stock_bi_v1.backend.modules.market.router import router as market_router
from apps.stock_bi_v1.backend.modules.screener.router import router as screener_router
from apps.stock_bi_v1.backend.modules.stock.router import router as stock_router
from apps.stock_bi_v1.backend.modules.toplist.router import router as toplist_router
from apps.stock_bi_v1.backend.precompute.runner import run_precompute


def create_app() -> FastAPI:
    create_all()

    app = FastAPI(
        title="Stock BI V1 API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    app.include_router(market_router)
    app.include_router(industry_router)
    app.include_router(stock_router)
    app.include_router(flow_router)
    app.include_router(toplist_router)
    app.include_router(screener_router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/")
    def root():
        return {"message": "Stock BI V1 API", "docs": "/api/docs"}

    @app.post("/api/precompute/{trade_date}")
    def precompute(trade_date: str, background_tasks: BackgroundTasks):
        background_tasks.add_task(run_precompute, trade_date)
        return {"status": "accepted", "trade_date": trade_date}

    return app


app = create_app()
