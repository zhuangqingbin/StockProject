from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Callable
from typing import Sequence

from .runtime import JobRunResult, load_job_definitions, run_configured_jobs
from .stock_bi_sync import sync_stock_bi
from .stock_bi_v1_sync import trigger_stock_bi_v1_precompute

DEFAULT_RETRY_DELAY_SEC = 600


def _parse_job_names(raw_jobs: str | None) -> list[str] | None:
    if not raw_jobs:
        return None
    job_names = [job_name.strip() for job_name in raw_jobs.split(",") if job_name.strip()]
    return job_names or None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run configured stock data daily jobs.")
    parser.add_argument(
        "--config",
        help="Path to the YAML job definition file. Defaults to apps/stock_data_platform/jobs/daily_jobs.yaml.",
    )
    parser.add_argument("--as-of", help="Calendar date used to resolve the latest trade date, format YYYY-MM-DD.")
    parser.add_argument("--jobs", help="Comma-separated job names. When omitted, all configured jobs run.")
    parser.add_argument(
        "--retry-delay-sec",
        type=int,
        default=DEFAULT_RETRY_DELAY_SEC,
        help="Delay before retrying failed jobs. Defaults to 600 seconds.",
    )
    parser.add_argument(
        "--max-retry-rounds",
        type=int,
        default=0,
        help="Maximum retry rounds for failed jobs. 0 means retry until all jobs succeed.",
    )
    return parser


def _collect_trade_dates(results: Sequence[JobRunResult], trigger_only: bool) -> list[str]:
    trade_dates: set[str] = set()

    for result in results:
        if result.rows_written <= 0:
            continue
        if trigger_only and not result.trigger_stock_bi_sync:
            continue

        trade_date = str(result.params.get("trade_date", "")).replace("-", "").strip()
        if trade_date:
            trade_dates.add(trade_date)

    return sorted(trade_dates)


def _collect_stock_bi_trade_dates(results: Sequence[JobRunResult]) -> list[str]:
    return _collect_trade_dates(results, trigger_only=True)


def _collect_all_trade_dates(results: Sequence[JobRunResult]) -> list[str]:
    return _collect_trade_dates(results, trigger_only=False)


def _should_trigger_stock_bi_v1_precompute(requested_job_names: Sequence[str] | None) -> bool:
    return requested_job_names is None


def _resolve_selected_job_names(config_path: str | None, requested_job_names: Sequence[str] | None) -> list[str]:
    configured_job_names = [job_definition.name for job_definition in load_job_definitions(config_path)]
    if requested_job_names is None:
        requested = configured_job_names
    else:
        requested = list(requested_job_names)

    seen: set[str] = set()
    selected_job_names: list[str] = []
    for job_name in requested:
        if job_name in seen:
            continue
        seen.add(job_name)
        selected_job_names.append(job_name)

    unknown_job_names = sorted(set(selected_job_names) - set(configured_job_names))
    if unknown_job_names:
        raise ValueError(f"Unknown job names: {', '.join(unknown_job_names)}")

    return selected_job_names


def _is_retryable_job_failure(exc: Exception) -> bool:
    return isinstance(exc, RuntimeError) and str(exc).startswith("Daily job failed:")


def run_configured_jobs_until_success(
    config_path: str | None = None,
    as_of: str | None = None,
    job_names: Sequence[str] | None = None,
    writer: object | None = None,
    retry_delay_sec: int = DEFAULT_RETRY_DELAY_SEC,
    max_retry_rounds: int = 0,
    sleep_fn: Callable[[float], None] | None = None,
) -> list[JobRunResult]:
    selected_job_names = _resolve_selected_job_names(config_path, job_names)
    if not selected_job_names:
        return []

    resolved_sleep_fn = sleep_fn or time.sleep
    results_by_job_name: dict[str, JobRunResult] = {}
    pending_job_names = list(selected_job_names)
    retry_rounds = 0

    while pending_job_names:
        failed_job_names: list[str] = []

        for job_name in pending_job_names:
            try:
                job_results = run_configured_jobs(
                    config_path=config_path,
                    as_of=as_of,
                    job_names=[job_name],
                    writer=writer,
                )
            except Exception as exc:
                if not _is_retryable_job_failure(exc):
                    raise
                print(exc)
                failed_job_names.append(job_name)
                continue

            if len(job_results) != 1:
                raise RuntimeError(
                    f"Expected exactly one result for job={job_name}, got {len(job_results)}"
                )

            results_by_job_name[job_name] = job_results[0]

        if not failed_job_names:
            break

        retry_rounds += 1
        if max_retry_rounds > 0 and retry_rounds > max_retry_rounds:
            raise RuntimeError(
                "Daily jobs still failing after retry rounds: "
                f"failed_jobs={failed_job_names}, retry_rounds={retry_rounds - 1}"
            )

        print(
            f"Retrying failed jobs after {retry_delay_sec} seconds: "
            f"{', '.join(failed_job_names)}"
        )
        resolved_sleep_fn(retry_delay_sec)
        pending_job_names = failed_job_names

    return [results_by_job_name[job_name] for job_name in selected_job_names]


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    requested_job_names = _parse_job_names(args.jobs)
    results = run_configured_jobs_until_success(
        config_path=args.config,
        as_of=args.as_of,
        job_names=requested_job_names,
        retry_delay_sec=args.retry_delay_sec,
        max_retry_rounds=args.max_retry_rounds,
    )

    if not results:
        print("No jobs executed.")
        return 0

    for result in results:
        print(
            f"{result.job_name}: fetched={result.rows_fetched}, "
            f"written={result.rows_written}, tables={list(result.written_tables)}, "
            f"primary_table={result.table_name}, params={dict(result.params)}"
        )

    post_run_failures: list[tuple[str, Exception]] = []

    for trade_date in _collect_stock_bi_trade_dates(results):
        try:
            response = sync_stock_bi(trade_date)
            print(f"stock_bi sync: trade_date={trade_date}, response={response}")
        except Exception as exc:
            post_run_failures.append(("stock_bi sync", exc))

    if _should_trigger_stock_bi_v1_precompute(requested_job_names):
        for trade_date in _collect_all_trade_dates(results):
            try:
                response = trigger_stock_bi_v1_precompute(trade_date)
                print(f"stock_bi_v1 precompute: trade_date={trade_date}, response={response}")
            except Exception as exc:
                post_run_failures.append(("stock_bi_v1 precompute", exc))

    if post_run_failures:
        for label, exc in post_run_failures:
            print(f"{label} failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
