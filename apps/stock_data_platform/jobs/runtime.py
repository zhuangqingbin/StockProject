from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import pandas as pd
import yaml
from sqlalchemy import inspect, text

from apps.stock_data_platform.common.database_runtime import get_engine
from apps.stock_data_platform.common.market_calendar import get_trade_cal


TradeCalendarProvider = Callable[[str, str], Sequence[str]]
DEFAULT_CONFIG_PATH = Path(__file__).with_name("daily_jobs.yaml")


def _coerce_date(value: str | date | datetime | None) -> date:
    if value is None:
        return date.today()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def _compact(value: date) -> str:
    return value.strftime("%Y%m%d")


def _parse_compact(value: str) -> date:
    return datetime.strptime(value, "%Y%m%d").date()


@dataclass(frozen=True)
class ExecutionContext:
    as_of_date: date
    trade_date: date

    @classmethod
    def for_as_of(
        cls,
        as_of: str | date | datetime | None = None,
        trade_calendar_provider: TradeCalendarProvider = get_trade_cal,
        lookback_days: int = 14,
    ) -> "ExecutionContext":
        as_of_date = _coerce_date(as_of)
        start_date = as_of_date - timedelta(days=lookback_days)
        open_days = list(trade_calendar_provider(_compact(start_date), _compact(as_of_date)))
        eligible = [day for day in open_days if day <= _compact(as_of_date)]
        if not eligible:
            raise ValueError(f"No open trade date found for as_of={as_of_date.isoformat()}")
        return cls(as_of_date=as_of_date, trade_date=_parse_compact(max(eligible)))

    def variables(self) -> dict[str, str]:
        return {
            "as_of_date_iso": self.as_of_date.isoformat(),
            "as_of_date_compact": _compact(self.as_of_date),
            "trade_date_iso": self.trade_date.isoformat(),
            "trade_date_compact": _compact(self.trade_date),
        }

    def render_value(self, value: Any) -> Any:
        if not isinstance(value, str):
            return value

        rendered = value
        for key, replacement in self.variables().items():
            rendered = rendered.replace(f"{{{{ {key} }}}}", replacement)
            rendered = rendered.replace(f"{{{{{key}}}}}", replacement)
        return rendered

    def render_mapping(self, values: Mapping[str, Any]) -> dict[str, Any]:
        return {key: self.render_value(value) for key, value in values.items()}


@dataclass(frozen=True)
class JobDefinition:
    name: str
    fetcher_cls: type[Any]
    table_name: str
    params: Mapping[str, Any]
    mirror_table_names: tuple[str, ...] = ()
    scope_columns: tuple[str, ...] = ()
    trigger_stock_bi_sync: bool = False

    def all_table_names(self) -> tuple[str, ...]:
        seen: set[str] = set()
        ordered_tables: list[str] = []

        for table_name in (self.table_name, *self.mirror_table_names):
            if table_name in seen:
                continue
            seen.add(table_name)
            ordered_tables.append(table_name)

        return tuple(ordered_tables)


@dataclass(frozen=True)
class JobRunResult:
    job_name: str
    table_name: str
    params: Mapping[str, Any]
    rows_fetched: int
    rows_written: int
    written_tables: tuple[str, ...] = ()
    trigger_stock_bi_sync: bool = False


def _resolve_fetcher_class(name: str) -> type[Any]:
    from apps.stock_data_platform import DataFetch

    try:
        return getattr(DataFetch, name)
    except AttributeError as exc:
        raise ValueError(f"Unknown fetcher: {name}") from exc


def load_job_definitions(config_path: str | Path | None = None) -> list[JobDefinition]:
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    raw_config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw_jobs = raw_config.get("jobs") or []

    jobs: list[JobDefinition] = []
    for raw_job in raw_jobs:
        mirror_table_names = tuple(raw_job.get("mirror_table_names") or ())
        jobs.append(
            JobDefinition(
                name=raw_job["name"],
                fetcher_cls=_resolve_fetcher_class(raw_job["fetcher"]),
                table_name=raw_job["table_name"],
                params=raw_job.get("params") or {},
                mirror_table_names=mirror_table_names,
                scope_columns=tuple(raw_job.get("scope_columns") or ()),
                trigger_stock_bi_sync=bool(
                    raw_job.get("trigger_stock_bi_sync", bool(mirror_table_names))
                ),
            )
        )
    return jobs


def _ensure_dataframe(value: Any) -> pd.DataFrame:
    if value is None:
        return pd.DataFrame()
    if isinstance(value, pd.DataFrame):
        return value
    return pd.DataFrame(value)


def _quote_identifier(name: str) -> str:
    return f"`{name.replace('`', '``')}`"


def _format_job_context(job_definition: JobDefinition, resolved_params: Mapping[str, Any]) -> str:
    target_tables = ",".join(job_definition.all_table_names())
    trade_date = str(resolved_params.get("trade_date", "")).strip() or "n/a"
    return (
        f"job={job_definition.name}, "
        f"primary_table={job_definition.table_name}, "
        f"target_tables={target_tables}, "
        f"trade_date={trade_date}"
    )


class DatabaseWriter:
    def __init__(self, engine: Any = None):
        self.engine = engine or get_engine()

    def write(self, job_definition: JobDefinition, frame: pd.DataFrame) -> int:
        if frame.empty:
            return 0

        with self.engine.begin() as connection:
            for table_name in job_definition.all_table_names():
                self._delete_existing_scope(table_name, job_definition.scope_columns, frame, connection)
                frame.to_sql(table_name, con=connection, if_exists="append", index=False)
        return int(len(frame.index))

    def _delete_existing_scope(
        self,
        table_name: str,
        scope_columns: Sequence[str],
        frame: pd.DataFrame,
        connection: Any,
    ) -> None:
        if not scope_columns:
            return
        if not inspect(connection).has_table(table_name):
            return

        scoped_values = frame.loc[:, list(scope_columns)].drop_duplicates().to_dict("records")
        if not scoped_values:
            return

        conditions = " AND ".join(
            f"{_quote_identifier(column_name)} = :{column_name}" for column_name in scope_columns
        )
        delete_sql = text(f"DELETE FROM {_quote_identifier(table_name)} WHERE {conditions}")

        for scoped_row in scoped_values:
            connection.execute(delete_sql, scoped_row)


def run_jobs(
    job_definitions: Sequence[JobDefinition],
    context: ExecutionContext | None = None,
    writer: Any | None = None,
    job_names: Sequence[str] | None = None,
) -> list[JobRunResult]:
    execution_context = context or ExecutionContext.for_as_of()
    database_writer = writer or DatabaseWriter()
    selected_names = set(job_names) if job_names else None
    available_names = {job_definition.name for job_definition in job_definitions}

    if selected_names is not None:
        unknown_names = sorted(selected_names - available_names)
        if unknown_names:
            raise ValueError(f"Unknown job names: {', '.join(unknown_names)}")

    results: list[JobRunResult] = []
    for job_definition in job_definitions:
        if selected_names is not None and job_definition.name not in selected_names:
            continue

        fetcher = job_definition.fetcher_cls()
        resolved_params = execution_context.render_mapping(job_definition.params)
        job_context = _format_job_context(job_definition, resolved_params)
        print(f"Running {job_context}")

        try:
            frame = _ensure_dataframe(fetcher.fetch(**resolved_params))
            rows_fetched = int(len(frame.index))
            rows_written = database_writer.write(job_definition, frame) if rows_fetched else 0
        except Exception as exc:
            raise RuntimeError(
                f"Daily job failed: {job_context}, params={dict(resolved_params)}, reason={exc}"
            ) from exc

        results.append(
            JobRunResult(
                job_name=job_definition.name,
                table_name=job_definition.table_name,
                written_tables=job_definition.all_table_names() if rows_written else (),
                trigger_stock_bi_sync=job_definition.trigger_stock_bi_sync,
                params=resolved_params,
                rows_fetched=rows_fetched,
                rows_written=rows_written,
            )
        )

    return results


def run_configured_jobs(
    config_path: str | Path | None = None,
    as_of: str | date | datetime | None = None,
    job_names: Sequence[str] | None = None,
    writer: Any | None = None,
) -> list[JobRunResult]:
    context = ExecutionContext.for_as_of(as_of)
    job_definitions = load_job_definitions(config_path)
    return run_jobs(job_definitions, context=context, writer=writer, job_names=job_names)
