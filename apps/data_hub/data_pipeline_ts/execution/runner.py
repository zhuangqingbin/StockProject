from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from typing import Callable, Sequence
from uuid import uuid4

from apps.data_hub.data_pipeline_ts.execution.context import ExecutionContext
from apps.data_hub.data_pipeline_ts.execution.rendering import _ensure_dataframe, _render_params
from apps.data_hub.data_pipeline_ts.execution.selection import select_job_specs
from apps.data_hub.data_pipeline_ts.jobs.profiles import PROFILE_SPECS
from apps.data_hub.data_pipeline_ts.jobs.specs import JobRunResult, JobSpec
from apps.data_hub.data_pipeline_ts.execution.persistence import DatabaseWriter


ContextFactory = Callable[[str | None], ExecutionContext]


def _record_result(writer: DatabaseWriter, result: JobRunResult) -> None:
    writer.record_run_result(result)


def _format_compact_date(value: date | None) -> str | None:
    if value is None:
        return None
    return value.strftime("%Y%m%d")


def _resolve_effective_date(spec: JobSpec, context: ExecutionContext) -> str | None:
    backfill_mode = PROFILE_SPECS[spec.profile].backfill_mode
    if backfill_mode == "trade_day":
        return _format_compact_date(context.trade_date)
    return _format_compact_date(context.as_of_date)


def _run_single_job(
    spec: JobSpec,
    context: ExecutionContext,
    writer: DatabaseWriter,
    run_id: str,
    run_mode: str,
) -> JobRunResult:
    started_at = time.perf_counter()
    resolved_params = _render_params(spec.params, context)
    as_of_date = _format_compact_date(context.as_of_date)
    effective_date = _resolve_effective_date(spec, context)

    try:
        fetcher = spec.fetcher_cls()
        frame = _ensure_dataframe(fetcher.fetch(**resolved_params))
        rows_fetched = int(len(frame.index))
        rows_written = writer.write(spec, frame) if rows_fetched else 0
        return JobRunResult(
            job_name=spec.name,
            table_name=spec.table_name,
            params=resolved_params,
            rows_fetched=rows_fetched,
            rows_written=rows_written,
            duration_seconds=time.perf_counter() - started_at,
            status="success",
            run_id=run_id,
            run_mode=run_mode,
            trigger_profile=spec.profile.value,
            as_of_date=as_of_date,
            effective_date=effective_date,
        )
    except Exception as exc:
        return JobRunResult(
            job_name=spec.name,
            table_name=spec.table_name,
            params=resolved_params,
            rows_fetched=0,
            rows_written=0,
            duration_seconds=time.perf_counter() - started_at,
            status="failed",
            error=str(exc),
            run_id=run_id,
            run_mode=run_mode,
            trigger_profile=spec.profile.value,
            as_of_date=as_of_date,
            effective_date=effective_date,
        )


def _run_grouped_jobs(
    specs: Sequence[JobSpec],
    *,
    context: ExecutionContext,
    writer: DatabaseWriter,
    run_id: str,
    run_mode: str,
    max_workers: int | None = None,
) -> list[JobRunResult]:
    grouped_specs: dict[object, list[JobSpec]] = {}
    for spec in specs:
        grouped_specs.setdefault(spec.profile, []).append(spec)

    results: list[JobRunResult] = []
    for profile_name, specs_in_profile in grouped_specs.items():
        profile_spec = PROFILE_SPECS[profile_name]
        if profile_spec.execution_mode == "serial":
            for spec in specs_in_profile:
                result = _run_single_job(spec, context, writer, run_id, run_mode)
                _record_result(writer, result)
                results.append(result)
            continue

        worker_count = max_workers or min(len(specs_in_profile), 8) or 1
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = {
                executor.submit(_run_single_job, spec, context, writer, run_id, run_mode): spec
                for spec in specs_in_profile
            }
            for future in as_completed(futures):
                result = future.result()
                _record_result(writer, result)
                results.append(result)

    order = {spec.name: index for index, spec in enumerate(specs)}
    return sorted(results, key=lambda result: order[result.job_name])


def _should_run_spec_for_backfill_date(spec: JobSpec, context: ExecutionContext, current_date: date) -> bool:
    backfill_mode = PROFILE_SPECS[spec.profile].backfill_mode
    if backfill_mode == "calendar_day":
        return True
    if backfill_mode == "manual":
        return False
    return context.trade_date == current_date


def _coerce_compact_date(raw_value: str) -> date:
    return datetime.strptime(raw_value, "%Y%m%d").date()


def _iter_calendar_days(start: str, end: str) -> list[date]:
    current = _coerce_compact_date(start)
    end_date = _coerce_compact_date(end)
    if current > end_date:
        raise ValueError(f"start must be <= end, got {start} > {end}")

    dates: list[date] = []
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)
    return dates


def run_once(
    *,
    as_of: str | None = None,
    profiles: Sequence[str] | None = None,
    job_names: Sequence[str] | None = None,
    job_specs: Sequence[JobSpec] | None = None,
    writer: DatabaseWriter | None = None,
    context_factory: ContextFactory = ExecutionContext.for_as_of,
    max_workers: int | None = None,
) -> list[JobRunResult]:
    selected_specs = select_job_specs(job_specs, job_names=job_names, profiles=profiles)
    database_writer = writer or DatabaseWriter()
    context = context_factory(as_of)
    run_id = uuid4().hex
    return _run_grouped_jobs(
        selected_specs,
        context=context,
        writer=database_writer,
        run_id=run_id,
        run_mode="once",
        max_workers=max_workers,
    )


def run_backfill(
    *,
    start: str,
    end: str,
    profiles: Sequence[str] | None = None,
    job_names: Sequence[str] | None = None,
    job_specs: Sequence[JobSpec] | None = None,
    writer: DatabaseWriter | None = None,
    context_factory: ContextFactory = ExecutionContext.for_as_of,
    max_workers: int | None = None,
) -> list[JobRunResult]:
    selected_specs = select_job_specs(job_specs, job_names=job_names, profiles=profiles)
    database_writer = writer or DatabaseWriter()
    run_id = uuid4().hex

    results: list[JobRunResult] = []
    for current_date in _iter_calendar_days(start, end):
        context = context_factory(current_date.isoformat())
        runnable_specs = [
            spec
            for spec in selected_specs
            if _should_run_spec_for_backfill_date(spec, context, current_date)
        ]
        if not runnable_specs:
            continue
        results.extend(
            _run_grouped_jobs(
                runnable_specs,
                context=context,
                writer=database_writer,
                run_id=run_id,
                run_mode="backfill",
                max_workers=max_workers,
            )
        )
    return results
