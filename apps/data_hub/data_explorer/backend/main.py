from __future__ import annotations

from fastapi import FastAPI

from apps.data_hub.data_explorer.backend.api.catalog import router as catalog_router
from apps.data_hub.data_explorer.backend.api.database_metadata import (
    router as database_metadata_router,
)
from apps.data_hub.data_explorer.backend.api.monitor import router as monitor_router
from apps.data_hub.data_explorer.backend.api.preview import router as preview_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="data_explorer API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    app.include_router(catalog_router)
    app.include_router(preview_router)
    app.include_router(monitor_router)
    app.include_router(database_metadata_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "healthy"}

    @app.get("/")
    def root() -> dict[str, str]:
        return {"name": "data_explorer"}

    return app


app = create_app()
