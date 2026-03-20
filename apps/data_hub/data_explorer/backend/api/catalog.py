from __future__ import annotations

from fastapi import APIRouter, HTTPException

from apps.data_hub.data_explorer.backend.services.catalog_service import (
    list_categories,
    list_tables_by_category,
)
from apps.data_hub.data_explorer.backend.services.table_detail_service import get_table_detail


router = APIRouter(prefix="/api/catalog", tags=["catalog"])


@router.get("/categories")
def get_categories() -> list[dict[str, object]]:
    return list_categories()


@router.get("/categories/{category_key}/tables")
def get_tables(category_key: str) -> list[dict[str, object]]:
    return list_tables_by_category(category_key)


@router.get("/tables/{table_name}")
def get_table(table_name: str) -> dict[str, object]:
    try:
        return get_table_detail(table_name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown table: {exc.args[0]}") from exc
