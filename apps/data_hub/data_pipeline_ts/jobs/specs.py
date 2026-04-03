from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from apps.data_hub.data_pipeline_ts.fetchers.base import TableSchema
from apps.data_hub.data_pipeline_ts.jobs.profiles import ProfileId

FetchStrategy = Literal[
    "direct",
    "full_market_stock_code_fanout",
    "enum_fanout_tag",
    "enum_fanout_type",
    "row_cap_fallback_exchange",
    "row_cap_fallback_exchange_id",
    "snapshot_column",
    "transport_pro_bar",
    "custom_rate_limit_handling",
    "post_fetch_dedup",
]


@dataclass(frozen=True)
class JobSpec:
    name: str
    table_name: str
    fetcher_cls: type[Any]
    description: str
    profile: ProfileId
    api_name: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    scope_columns: tuple[str, ...] = ()
    fetch_strategies: tuple[FetchStrategy, ...] = ("direct",)
    source: str = "tushare"
    table_schema: TableSchema | None = None


@dataclass(frozen=True)
class InfrastructureSpec:
    name: str
    fetcher_cls: type[Any]
    table_name: str
    scope_columns: tuple[str, ...]
    api_name: str = ""
    source: str = "tushare"
    table_schema: TableSchema | None = None


@dataclass(frozen=True)
class JobRunResult:
    job_name: str
    table_name: str
    params: dict[str, Any]
    rows_fetched: int
    rows_written: int
    duration_seconds: float
    status: Literal["success", "failed", "skipped"]
    error: str | None = None
    run_id: str | None = None
    run_mode: Literal["once", "backfill", "infrastructure", "direct"] | None = None
    trigger_profile: str | None = None
    as_of_date: str | None = None
    effective_date: str | None = None
    executed_at: datetime = field(default_factory=datetime.utcnow)
