from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd
import yaml

from apps.stock_data_platform.common.database_runtime import get_engine
from apps.stock_data_platform.jobs.runtime import load_job_definitions


def _validate_identifier(identifier: str) -> str:
    candidate = identifier.strip()
    if not candidate:
        raise ValueError("identifier is required")

    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
    if any(character not in allowed for character in candidate):
        raise ValueError(f"invalid identifier: {identifier!r}")
    return candidate


def build_table_preview_sql(table_name: str, limit: int = 20) -> str:
    validated_table_name = _validate_identifier(table_name)
    if limit <= 0:
        raise ValueError(f"limit must be positive, got {limit}")
    return f"SELECT * FROM `{validated_table_name}` LIMIT {int(limit)}"


def preview_table(table_name: str, limit: int = 20) -> pd.DataFrame:
    sql = build_table_preview_sql(table_name, limit=limit)
    return pd.read_sql_query(sql, con=get_engine())


def list_job_catalog(config_path: str | Path | None = None) -> pd.DataFrame:
    records = []
    for job_definition in load_job_definitions(config_path):
        records.append(
            {
                "job_name": job_definition.name,
                "fetcher": job_definition.fetcher_cls.__name__,
                "primary_table": job_definition.table_name,
                "mirror_tables": ",".join(job_definition.mirror_table_names),
                "scope_columns": ",".join(job_definition.scope_columns),
                "trigger_stock_bi_sync": job_definition.trigger_stock_bi_sync,
            }
        )

    return pd.DataFrame(
        records,
        columns=[
            "job_name",
            "fetcher",
            "primary_table",
            "mirror_tables",
            "scope_columns",
            "trigger_stock_bi_sync",
        ],
    )


def build_new_source_job_yaml(
    name: str,
    fetcher: str,
    table_name: str,
    params: Mapping[str, Any] | None = None,
    mirror_table_names: Sequence[str] = (),
    scope_columns: Sequence[str] = (),
    trigger_stock_bi_sync: bool = False,
) -> str:
    payload: dict[str, Any] = {
        "name": _validate_identifier(name),
        "fetcher": fetcher.strip(),
        "table_name": _validate_identifier(table_name),
    }

    if mirror_table_names:
        payload["mirror_table_names"] = [_validate_identifier(item) for item in mirror_table_names]

    if trigger_stock_bi_sync:
        payload["trigger_stock_bi_sync"] = True

    if params:
        payload["params"] = dict(params)

    if scope_columns:
        payload["scope_columns"] = [_validate_identifier(item) for item in scope_columns]

    rendered = yaml.safe_dump([payload], sort_keys=False, allow_unicode=True).strip()
    if not rendered.startswith("- "):
        return rendered
    return rendered


def build_new_source_steps() -> list[str]:
    return [
        "Probe the upstream API in a notebook and confirm the returned DataFrame shape, columns, and date grain.",
        "Decide the primary table name and whether BI also needs a mirrored table name.",
        "Add a new fetcher under apps/stock_data_platform/DataFetch and export it from DataFetch/__init__.py.",
        "Add a new job entry to apps/stock_data_platform/jobs/daily_jobs.yaml with params and scope_columns.",
        "Add focused tests for the fetcher or job configuration before wiring it into the daily schedule.",
        "Only after the fetcher and job are stable should the new table be included in the daily schedule or BI sync path.",
    ]
