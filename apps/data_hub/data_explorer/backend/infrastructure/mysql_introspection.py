from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
DATE_COLUMNS = ("trade_date", "ann_date", "end_date", "ipo_date", "list_date", "executed_at")
JOB_RUN_LOG_COLUMNS = (
    "id",
    "run_id",
    "run_mode",
    "trigger_profile",
    "job_name",
    "table_name",
    "status",
    "rows_fetched",
    "rows_written",
    "duration_seconds",
    "error",
    "as_of_date",
    "effective_date",
    "executed_at",
)


def _validate_identifier(identifier: str) -> str:
    if not IDENTIFIER_RE.fullmatch(identifier):
      raise ValueError(f"Unsafe identifier: {identifier}")
    return identifier


def normalize_columns(columns: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "name": column.get("name"),
            "type": str(column.get("type")),
            "nullable": bool(column.get("nullable")),
            "default": column.get("default"),
            "comment": column.get("comment"),
        }
        for column in columns
    ]


def normalize_indexes(
    indexes: Sequence[Mapping[str, Any]],
    primary_key: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []

    primary_columns = list((primary_key or {}).get("constrained_columns") or [])
    if primary_columns:
        normalized.append(
            {
                "name": (primary_key or {}).get("name") or "PRIMARY",
                "columns": primary_columns,
                "unique": True,
                "primary": True,
            }
        )

    for index in indexes:
        normalized.append(
            {
                "name": index.get("name"),
                "columns": list(index.get("column_names") or []),
                "unique": bool(index.get("unique")),
                "primary": False,
            }
        )

    return normalized


def extract_create_table_sql(row: Mapping[str, Any]) -> str:
    ddl = row.get("Create Table")
    if ddl is None:
        raise KeyError("Create Table")
    return str(ddl)


def get_current_schema_name(engine: Engine) -> str | None:
    with engine.connect() as connection:
        return connection.execute(text("SELECT DATABASE()")).scalar()


def get_table_names(engine: Engine) -> list[str]:
    return inspect(engine).get_table_names()


def get_table_columns(engine: Engine, table_name: str) -> list[dict[str, Any]]:
    safe_table_name = _validate_identifier(table_name)
    inspector = inspect(engine)
    return normalize_columns(inspector.get_columns(safe_table_name))


def get_table_indexes(engine: Engine, table_name: str) -> list[dict[str, Any]]:
    safe_table_name = _validate_identifier(table_name)
    inspector = inspect(engine)
    return normalize_indexes(
        inspector.get_indexes(safe_table_name),
        inspector.get_pk_constraint(safe_table_name),
    )


def get_table_constraints(engine: Engine, table_name: str) -> list[dict[str, Any]]:
    safe_table_name = _validate_identifier(table_name)
    inspector = inspect(engine)
    constraints: list[dict[str, Any]] = []

    primary_key = inspector.get_pk_constraint(safe_table_name)
    if primary_key.get("constrained_columns"):
        constraints.append(
            {
                "name": primary_key.get("name") or "PRIMARY",
                "type": "PRIMARY KEY",
                "columns": list(primary_key.get("constrained_columns") or []),
            }
        )

    for unique_constraint in inspector.get_unique_constraints(safe_table_name):
        constraints.append(
            {
                "name": unique_constraint.get("name") or "UNIQUE",
                "type": "UNIQUE",
                "columns": list(unique_constraint.get("column_names") or []),
            }
        )

    for foreign_key in inspector.get_foreign_keys(safe_table_name):
        constraints.append(
            {
                "name": foreign_key.get("name") or "FOREIGN KEY",
                "type": "FOREIGN KEY",
                "columns": list(foreign_key.get("constrained_columns") or []),
            }
        )

    get_check_constraints = getattr(inspector, "get_check_constraints", None)
    if callable(get_check_constraints):
        for check_constraint in get_check_constraints(safe_table_name):
            constraints.append(
                {
                    "name": check_constraint.get("name") or "CHECK",
                    "type": "CHECK",
                    "columns": [],
                }
            )

    return constraints


def get_table_ddl(engine: Engine, table_name: str) -> str:
    safe_table_name = _validate_identifier(table_name)
    with engine.connect() as connection:
        row = connection.execute(text(f"SHOW CREATE TABLE `{safe_table_name}`")).mappings().one()
    return extract_create_table_sql(row)


def get_exact_row_count(engine: Engine, table_name: str) -> int:
    safe_table_name = _validate_identifier(table_name)
    with engine.connect() as connection:
        return int(connection.execute(text(f"SELECT COUNT(*) FROM `{safe_table_name}`")).scalar() or 0)


def get_latest_data_date(
    engine: Engine,
    table_name: str,
    columns: Sequence[Mapping[str, Any]] | Sequence[str],
) -> str | None:
    safe_table_name = _validate_identifier(table_name)
    column_names = [column["name"] if isinstance(column, Mapping) else str(column) for column in columns]
    date_column = next((column for column in DATE_COLUMNS if column in column_names), None)
    if date_column is None:
        return None

    safe_column = _validate_identifier(date_column)
    with engine.connect() as connection:
        value = connection.execute(
            text(f"SELECT MAX(`{safe_column}`) FROM `{safe_table_name}`"),
        ).scalar()
    return None if value is None else str(value)


def get_earliest_data_date(
    engine: Engine,
    table_name: str,
    columns: Sequence[Mapping[str, Any]] | Sequence[str],
) -> str | None:
    safe_table_name = _validate_identifier(table_name)
    column_names = [column["name"] if isinstance(column, Mapping) else str(column) for column in columns]
    date_column = next((column for column in DATE_COLUMNS if column in column_names), None)
    if date_column is None:
        return None

    safe_column = _validate_identifier(date_column)
    with engine.connect() as connection:
        value = connection.execute(
            text(f"SELECT MIN(`{safe_column}`) FROM `{safe_table_name}`"),
        ).scalar()
    return None if value is None else str(value)


def get_latest_job_success_time(engine: Engine, job_name: str) -> str | None:
    if not job_name:
        return None

    with engine.connect() as connection:
        value = connection.execute(
            text(
                "SELECT executed_at FROM job_run_log "
                "WHERE job_name = :job_name AND status = 'success' "
                "ORDER BY executed_at DESC LIMIT 1"
            ),
            {"job_name": job_name},
        ).scalar()
    return None if value is None else str(value)


def _get_job_run_log_columns(engine: Engine) -> set[str]:
    inspector = inspect(engine)
    if not inspector.has_table("job_run_log"):
        return set()
    return {
        str(column.get("name"))
        for column in inspector.get_columns("job_run_log")
        if column.get("name")
    }


def _build_job_run_log_select_list(
    available_columns: set[str],
    *,
    alias: str,
) -> str:
    return ", ".join(
        f"{alias}.`{column}` AS `{column}`" if column in available_columns else f"NULL AS `{column}`"
        for column in JOB_RUN_LOG_COLUMNS
    )


def get_latest_job_run_rows(engine: Engine) -> list[dict[str, Any]]:
    available_columns = _get_job_run_log_columns(engine)
    if not available_columns:
        return []

    select_list = _build_job_run_log_select_list(available_columns, alias="j")
    sql = text(
        f"SELECT {select_list} "
        "FROM job_run_log j "
        "INNER JOIN ("
        "  SELECT job_name, MAX(id) AS max_id "
        "  FROM job_run_log GROUP BY job_name"
        ") latest ON j.id = latest.max_id "
        "ORDER BY CASE WHEN j.status = 'failed' THEN 0 ELSE 1 END, j.executed_at DESC"
    )
    with engine.connect() as connection:
        result = connection.execute(sql)
        return [dict(row._mapping) for row in result]


def get_recent_job_run_rows(engine: Engine, *, limit: int = 200) -> list[dict[str, Any]]:
    available_columns = _get_job_run_log_columns(engine)
    if not available_columns:
        return []

    select_list = _build_job_run_log_select_list(available_columns, alias="j")
    sql = text(
        f"SELECT {select_list} "
        "FROM job_run_log j "
        "ORDER BY j.executed_at DESC, j.id DESC "
        "LIMIT :limit"
    )
    with engine.connect() as connection:
        result = connection.execute(sql, {"limit": int(limit)})
        return [dict(row._mapping) for row in result]


def run_preview_queries(
    engine: Engine,
    query: str,
    count_query: str,
    params: Mapping[str, Any],
) -> dict[str, Any]:
    count_params = {key: value for key, value in params.items() if key not in {"limit", "offset"}}
    with engine.connect() as connection:
        total = int(connection.execute(text(count_query), count_params).scalar() or 0)
        rows = connection.execute(text(query), dict(params))
        data = [dict(row._mapping) for row in rows]
    return {"total": total, "data": data}
