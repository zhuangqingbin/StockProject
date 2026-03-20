from __future__ import annotations

from fastapi import APIRouter

from apps.data_hub.data_explorer.backend.services.database_metadata_service import (
    get_schema_overview,
    get_table_metadata_detail,
)


router = APIRouter(prefix="/api/database", tags=["database"])


@router.get("/overview")
def get_overview() -> dict[str, object]:
    return get_schema_overview()


@router.get("/tables/{table_name}/metadata")
def get_table_metadata(table_name: str) -> dict[str, object]:
    return get_table_metadata_detail(table_name)
