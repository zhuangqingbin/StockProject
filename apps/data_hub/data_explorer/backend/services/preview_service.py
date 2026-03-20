from __future__ import annotations

import re
from collections.abc import Sequence

from apps.data_hub.data_explorer.backend.infrastructure.db import get_engine
from apps.data_hub.data_explorer.backend.infrastructure.mysql_introspection import (
    get_table_columns,
    get_table_indexes,
    run_preview_queries,
)
from apps.data_hub.data_explorer.backend.services.catalog_service import (
    get_table_database_source,
    get_table_registry,
)


IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
DATE_COLUMNS = ("trade_date", "ann_date", "end_date", "ipo_date")
DEFAULT_PAGE_SIZE = 50
MAX_ALL_ROWS = 10000


def _validate_identifier(name: str) -> str:
    if not IDENTIFIER_RE.fullmatch(name):
        raise ValueError(f"Unsafe identifier: {name}")
    return name


def _pick_date_column(columns: Sequence[str]) -> str | None:
    column_set = set(columns)
    for column in DATE_COLUMNS:
        if column in column_set:
            return column
    return None


def _pick_order_column(columns: Sequence[str], indexes: Sequence[Sequence[str]]) -> str:
    date_column = _pick_date_column(columns)
    if date_column:
        return date_column
    if indexes and indexes[0]:
        return str(indexes[0][0])
    if columns:
        return str(columns[0])
    raise ValueError("No columns available for preview ordering")


def _require_registered_table(table_name: str) -> None:
    if table_name in get_table_registry():
        return
    raise KeyError(table_name)


def build_preview_queries(
    *,
    table_name: str,
    columns: Sequence[str],
    indexes: Sequence[Sequence[str]],
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    all_rows: bool = False,
    filters: dict[str, str] | None = None,
) -> dict[str, object]:
    safe_table_name = _validate_identifier(table_name)
    safe_columns = [_validate_identifier(column) for column in columns]
    safe_indexes = [[_validate_identifier(column) for column in index] for index in indexes]

    active_filters = filters or {}
    where_clauses: list[str] = []
    params: dict[str, object] = {}
    if not all_rows:
        params = {
            "limit": page_size,
            "offset": max(page - 1, 0) * page_size,
        }
    else:
        params = {
            "all_rows_limit": MAX_ALL_ROWS,
        }

    date_column = _pick_date_column(safe_columns)
    for key, value in active_filters.items():
        if key == "ts_code" and "ts_code" in safe_columns:
            where_clauses.append("ts_code = :ts_code")
            params["ts_code"] = value
            continue
        if key == f"{date_column}_start" and date_column:
            where_clauses.append(f"{date_column} >= :{key}")
            params[key] = value
            continue
        if key == f"{date_column}_end" and date_column:
            where_clauses.append(f"{date_column} <= :{key}")
            params[key] = value
            continue
        raise ValueError(f"Unsupported filter: {key}")

    where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    order_column = _pick_order_column(safe_columns, safe_indexes)
    query = f"SELECT * FROM {safe_table_name}{where_sql} ORDER BY {order_column} DESC"
    if all_rows:
        query = f"{query} LIMIT :all_rows_limit"
    else:
        query = f"{query} LIMIT :limit OFFSET :offset"
    count_query = f"SELECT COUNT(*) FROM {safe_table_name}{where_sql}"

    return {
        "query": query,
        "count_query": count_query,
        "params": params,
        "page": page,
        "page_size": page_size,
        "all_rows": all_rows,
    }


def get_table_preview(
    table_name: str,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    all_rows: bool = False,
    filters: dict[str, str] | None = None,
) -> dict[str, object]:
    _require_registered_table(table_name)
    registry = get_table_registry()
    engine = get_engine(get_table_database_source(table_name, registry))
    columns = [str(column["name"]) for column in get_table_columns(engine, table_name)]
    indexes = [list(index.get("columns", [])) for index in get_table_indexes(engine, table_name)]
    payload = build_preview_queries(
        table_name=table_name,
        columns=columns,
        indexes=indexes,
        page=page,
        page_size=page_size,
        all_rows=all_rows,
        filters=filters,
    )
    results = run_preview_queries(engine, payload["query"], payload["count_query"], payload["params"])
    displayed_rows = len(results["data"])
    truncated = bool(all_rows and results["total"] > displayed_rows)
    effective_page_size = displayed_rows if all_rows else page_size

    return {
        "table_name": table_name,
        "page": 1 if all_rows else page,
        "page_size": effective_page_size,
        "total": results["total"],
        "all_rows": all_rows,
        "displayed_rows": displayed_rows,
        "truncated": truncated,
        "truncated_limit": MAX_ALL_ROWS if all_rows else None,
        "columns": columns,
        "data": results["data"],
        "filters": filters or {},
    }
