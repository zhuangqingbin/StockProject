from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from apps.stock_backtest.backend.infrastructure.database import get_session_factory, init_database
from apps.stock_backtest.backend.infrastructure.settings import get_settings
from apps.stock_backtest.backend.modules.analysis.router import router as analysis_router
from apps.stock_backtest.backend.modules.backtest.router import router as backtest_router
from apps.stock_backtest.backend.modules.backtest.service import task_runtime
from apps.stock_backtest.backend.modules.backtest.websocket import router as websocket_router
from apps.stock_backtest.backend.modules.data.router import router as data_router
from apps.stock_backtest.backend.modules.notebook.router import router as notebook_router
from apps.stock_backtest.backend.modules.strategy.router import router as strategy_router
from apps.stock_backtest.backend.modules.strategy.service import ensure_default_strategies


def _resolve_index_path(frontend_dist: Optional[Path]) -> Optional[Path]:
    if frontend_dist is None:
        return None
    index_path = frontend_dist / "index.html"
    return index_path if index_path.exists() else None


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    session = get_session_factory()()
    try:
        ensure_default_strategies(session)
    finally:
        session.close()
    task_runtime.start()
    yield
    task_runtime.shutdown()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    index_path = _resolve_index_path(settings.frontend_dist)
    assets_dir = settings.frontend_dist / "assets" if settings.frontend_dist is not None else None
    if assets_dir is not None and assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/")
    def root():
        if index_path is not None:
            return FileResponse(index_path)
        return {"name": settings.app_name, "docs": "/api/docs"}

    @app.get("/health")
    def health():
        return {"status": "healthy"}

    app.include_router(strategy_router)
    app.include_router(backtest_router)
    app.include_router(analysis_router)
    app.include_router(notebook_router)
    app.include_router(data_router)
    app.include_router(websocket_router)

    @app.get("/{frontend_path:path}")
    def frontend_entry(frontend_path: str):
        if index_path is None:
            raise HTTPException(status_code=404, detail="Not Found")
        if frontend_path.startswith("api") or frontend_path.startswith("assets"):
            raise HTTPException(status_code=404, detail="Not Found")
        return FileResponse(index_path)

    return app


app = create_app()
