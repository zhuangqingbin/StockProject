from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from apps.data_hub.data_explorer.backend.api.catalog import router as catalog_router
from apps.data_hub.data_explorer.backend.api.database_metadata import (
    router as database_metadata_router,
)
from apps.data_hub.data_explorer.backend.api.monitor import router as monitor_router
from apps.data_hub.data_explorer.backend.api.preview import router as preview_router

FAVICON_DIR = Path(__file__).resolve().parents[1] / "frontend" / "public"
FAVICON_ICO_PATH = FAVICON_DIR / "favicon.ico"
FAVICON_SVG_PATH = FAVICON_DIR / "favicon.svg"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Jimmy发发发 API",
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
        return {"name": "Jimmy发发发"}

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon_ico() -> FileResponse:
        return FileResponse(FAVICON_ICO_PATH, media_type="image/x-icon")

    @app.get("/favicon.svg", include_in_schema=False)
    def favicon_svg() -> FileResponse:
        return FileResponse(FAVICON_SVG_PATH, media_type="image/svg+xml")

    return app


app = create_app()
