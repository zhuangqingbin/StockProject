from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from apps.data_hub.data_explorer.backend.services.preview_service import get_table_preview


router = APIRouter(prefix="/api/preview", tags=["preview"])


@router.get("/{table_name}")
def preview_table(
    table_name: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1),
    all_rows: bool = False,
    trade_date_start: str | None = None,
    trade_date_end: str | None = None,
    ts_code: str | None = None,
) -> dict[str, object]:
    filters = {
        key: value
        for key, value in {
            "trade_date_start": trade_date_start,
            "trade_date_end": trade_date_end,
            "ts_code": ts_code,
        }.items()
        if value is not None
    }
    try:
        return get_table_preview(
            table_name,
            page=page,
            page_size=page_size,
            all_rows=all_rows,
            filters=filters,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown table: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
