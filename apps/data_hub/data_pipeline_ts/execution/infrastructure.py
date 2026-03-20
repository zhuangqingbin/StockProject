from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from uuid import uuid4

from apps.data_hub.data_pipeline_ts.execution.rendering import _ensure_dataframe
from apps.data_hub.data_pipeline_ts.execution.runner import _record_result
from apps.data_hub.data_pipeline_ts.execution.selection import select_infrastructure_specs
from apps.data_hub.data_pipeline_ts.jobs.specs import InfrastructureSpec, JobRunResult
from apps.data_hub.data_pipeline_ts.execution.persistence import DatabaseWriter


def _build_infrastructure_fetch_kwargs(target_name: str, start: str | None, end: str | None) -> dict[str, str]:
    if target_name != "trade_cal":
        return {}
    if not start or not end:
        raise ValueError("start and end are required when syncing trade_cal")
    return {"start_date": start, "end_date": end}


def run_infrastructure(
    *,
    target_names: Sequence[str],
    start: str | None = None,
    end: str | None = None,
    infrastructure_specs: Mapping[str, InfrastructureSpec] | None = None,
    writer: DatabaseWriter | None = None,
) -> list[JobRunResult]:
    selected_specs = select_infrastructure_specs(target_names, infrastructure_specs=infrastructure_specs)
    database_writer = writer or DatabaseWriter()
    results: list[JobRunResult] = []
    run_id = uuid4().hex

    for spec in selected_specs:
        started_at = time.perf_counter()
        fetch_kwargs = _build_infrastructure_fetch_kwargs(spec.name, start, end)
        try:
            fetcher = spec.fetcher_cls()
            frame = _ensure_dataframe(fetcher.fetch(**fetch_kwargs))
            rows_fetched = int(len(frame.index))
            rows_written = database_writer.write(spec, frame) if rows_fetched else 0
            result = JobRunResult(
                job_name=spec.name,
                table_name=spec.table_name,
                params=fetch_kwargs,
                rows_fetched=rows_fetched,
                rows_written=rows_written,
                duration_seconds=time.perf_counter() - started_at,
                status="success",
                run_id=run_id,
                run_mode="infrastructure",
                trigger_profile="infrastructure",
            )
        except Exception as exc:
            result = JobRunResult(
                job_name=spec.name,
                table_name=spec.table_name,
                params=fetch_kwargs,
                rows_fetched=0,
                rows_written=0,
                duration_seconds=time.perf_counter() - started_at,
                status="failed",
                error=str(exc),
                run_id=run_id,
                run_mode="infrastructure",
                trigger_profile="infrastructure",
            )
        _record_result(database_writer, result)
        results.append(result)

    return results
