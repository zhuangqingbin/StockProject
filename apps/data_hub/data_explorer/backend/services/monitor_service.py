from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from apps.data_hub.data_explorer.backend.infrastructure.db import get_engine
from apps.data_hub.data_explorer.backend.infrastructure.mysql_introspection import (
    get_recent_job_run_rows,
    get_latest_job_run_rows,
)
from apps.data_hub.data_explorer.backend.services.catalog_service import (
    get_table_registry,
    get_table_stats,
)


def _parse_datetime(raw_value: object) -> datetime | None:
    if isinstance(raw_value, datetime):
        return raw_value
    if raw_value in {None, ""}:
        return None

    value = str(raw_value)
    for pattern in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(value, pattern)
        except ValueError:
            continue
    return None


def _resolve_table_name(
    row: dict[str, object],
    registry: dict[str, dict[str, object]],
) -> str:
    table_name = str(row.get("table_name") or "")
    if table_name:
        return table_name

    job_name = str(row.get("job_name") or "")
    for candidate_table_name, entry in registry.items():
        if entry.get("job_name") == job_name:
            return candidate_table_name
    return ""


def _normalize_job_run_row(
    row: dict[str, object],
    registry: dict[str, dict[str, object]],
) -> dict[str, object]:
    table_name = _resolve_table_name(row, registry)
    registry_entry = registry.get(table_name, {})
    executed_at = row.get("executed_at")
    run_id = str(row.get("run_id") or "")
    if not run_id:
        run_id = f"legacy-{table_name or row.get('job_name') or 'run'}-{executed_at}"

    return {
        "run_id": run_id,
        "run_mode": row.get("run_mode") or "legacy",
        "trigger_profile": row.get("trigger_profile") or registry_entry.get("trigger_profile") or "",
        "job_name": row.get("job_name") or registry_entry.get("job_name") or "",
        "table_name": table_name,
        "result": row.get("status") or "unknown",
        "status": row.get("status") or "unknown",
        "rows_fetched": row.get("rows_fetched"),
        "rows_written": row.get("rows_written"),
        "duration_seconds": row.get("duration_seconds"),
        "error": row.get("error"),
        "as_of_date": row.get("as_of_date"),
        "effective_date": row.get("effective_date"),
        "executed_at": None if executed_at is None else str(executed_at),
        "_executed_at_dt": _parse_datetime(executed_at),
    }


def get_recent_job_runs(limit: int = 200) -> list[dict[str, object]]:
    registry = get_table_registry()
    try:
        rows = get_recent_job_run_rows(get_engine("ts"), limit=limit)
    except Exception:
        return []

    normalized = [_normalize_job_run_row(row, registry) for row in rows if row.get("job_name")]
    normalized.sort(
        key=lambda row: row.get("_executed_at_dt") or datetime.min,
        reverse=True,
    )
    return normalized


def get_latest_job_runs() -> dict[str, dict[str, object]]:
    registry = get_table_registry()
    try:
        rows = get_latest_job_run_rows(get_engine("ts"))
    except Exception:
        return {}
    return {
        str(row["job_name"]): _normalize_job_run_row(dict(row), registry)
        for row in rows
        if row.get("job_name")
    }


def get_monitor_overview() -> dict[str, object]:
    registry = get_table_registry()
    stats = get_table_stats(list(registry.keys()))
    recent_job_runs = get_recent_job_runs(limit=400)
    recent_runs = list_pipeline_run_rows(limit=50, recent_job_runs=recent_job_runs)
    status_counts = Counter(
        str(stats.get(table_name, {}).get("status", "unknown"))
        for table_name in registry
    )
    now = datetime.utcnow()
    recent_failed_jobs = [
        row
        for row in recent_job_runs
        if row.get("result") == "failed"
        and (
            (executed_at := row.get("_executed_at_dt")) is None
            or executed_at >= now - timedelta(hours=24)
        )
    ]
    latest_run = recent_runs[0] if recent_runs else None

    return {
        "dataset_count": len(registry),
        "fresh_datasets": status_counts.get("normal", 0),
        "delayed_datasets": status_counts.get("delayed", 0),
        "error_datasets": status_counts.get("error", 0),
        "manual_datasets": status_counts.get("manual", 0),
        "no_data_datasets": status_counts.get("no_data", 0),
        "recent_failed_jobs": len(recent_failed_jobs),
        "recent_runs": len(recent_runs),
        "latest_run": latest_run,
    }


def list_table_monitor_rows() -> list[dict[str, object]]:
    registry = get_table_registry()
    stats = get_table_stats(list(registry.keys()))
    latest_runs = get_latest_job_runs()

    rows = []
    for table_name, entry in registry.items():
        table_stats = stats.get(table_name, {})
        latest_job_run = latest_runs.get(str(entry.get("job_name") or ""), {})
        rows.append(
            {
                "table_name": table_name,
                "category": entry["category"],
                "latest_data_date": table_stats.get("latest_data_date"),
                "last_updated": table_stats.get("last_updated"),
                "freshness": table_stats.get("status", "normal"),
                "trigger_profile": entry.get("trigger_profile", ""),
                "last_run_result": latest_job_run.get("result"),
                "last_run_id": latest_job_run.get("run_id"),
            }
        )
    rows.sort(key=lambda row: (str(row.get("freshness") != "delayed"), str(row.get("table_name"))))
    return rows


def list_job_monitor_rows() -> list[dict[str, object]]:
    registry = get_table_registry()
    latest_runs = get_latest_job_runs()
    rows = [
        {
            "run_id": job_run.get("run_id"),
            "run_mode": job_run.get("run_mode"),
            "trigger_profile": job_run.get("trigger_profile") or next(
                (
                    entry.get("trigger_profile")
                    for entry in registry.values()
                    if entry.get("job_name") == job_name
                ),
                None,
            ),
            "job_name": job_run.get("job_name") or job_name,
            "table_name": job_run.get("table_name") or next(
                (
                    table_name
                    for table_name, entry in registry.items()
                    if entry.get("job_name") == job_name
                ),
                None,
            ),
            "result": job_run.get("result") or job_run.get("status"),
            "status": job_run.get("result") or job_run.get("status"),
            "effective_date": job_run.get("effective_date"),
            "executed_at": job_run.get("executed_at"),
            "duration_seconds": job_run.get("duration_seconds"),
            "rows_written": job_run.get("rows_written"),
            "error": job_run.get("error"),
        }
        for job_name, job_run in latest_runs.items()
    ]
    rows.sort(key=lambda row: (str(row.get("result") != "failed"), str(row.get("job_name"))))
    return rows


def list_pipeline_run_rows(
    *,
    limit: int = 50,
    recent_job_runs: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    rows = recent_job_runs if recent_job_runs is not None else get_recent_job_runs(limit=400)
    grouped: dict[str, dict[str, Any]] = {}

    for row in rows:
        run_id = str(row.get("run_id") or "")
        if not run_id:
            continue

        group = grouped.setdefault(
            run_id,
            {
                "run_id": run_id,
                "run_mode": row.get("run_mode") or "legacy",
                "trigger_profiles": set(),
                "job_names": set(),
                "table_names": set(),
                "effective_dates": set(),
                "started_at": row.get("_executed_at_dt"),
                "ended_at": row.get("_executed_at_dt"),
                "failed_jobs": 0,
                "successful_jobs": 0,
            },
        )

        executed_at = row.get("_executed_at_dt")
        if isinstance(executed_at, datetime):
            if group["started_at"] is None or executed_at < group["started_at"]:
                group["started_at"] = executed_at
            if group["ended_at"] is None or executed_at > group["ended_at"]:
                group["ended_at"] = executed_at

        trigger_profile = str(row.get("trigger_profile") or "")
        if trigger_profile:
            group["trigger_profiles"].add(trigger_profile)
        job_name = str(row.get("job_name") or "")
        if job_name:
            group["job_names"].add(job_name)
        table_name = str(row.get("table_name") or "")
        if table_name:
            group["table_names"].add(table_name)
        effective_date = str(row.get("effective_date") or "")
        if effective_date:
            group["effective_dates"].add(effective_date)

        if row.get("result") == "failed":
            group["failed_jobs"] += 1
        elif row.get("result") == "success":
            group["successful_jobs"] += 1

    aggregated_rows = []
    for group in grouped.values():
        total_jobs = int(group["failed_jobs"]) + int(group["successful_jobs"])
        if group["failed_jobs"] and group["successful_jobs"]:
            status = "partial_failed"
        elif group["failed_jobs"]:
            status = "failed"
        else:
            status = "success"

        effective_dates = sorted(group["effective_dates"])
        if not effective_dates:
            effective_window = "—"
        elif len(effective_dates) == 1:
            effective_window = effective_dates[0]
        else:
            effective_window = f"{effective_dates[0]} -> {effective_dates[-1]}"

        started_at = group["started_at"]
        ended_at = group["ended_at"]
        aggregated_rows.append(
            {
                "run_id": group["run_id"],
                "run_mode": group["run_mode"],
                "status": status,
                "trigger_profiles": sorted(group["trigger_profiles"]),
                "job_count": total_jobs,
                "failed_jobs": group["failed_jobs"],
                "successful_jobs": group["successful_jobs"],
                "table_count": len(group["table_names"]),
                "effective_window": effective_window,
                "started_at": None if started_at is None else started_at.isoformat(sep=" "),
                "ended_at": None if ended_at is None else ended_at.isoformat(sep=" "),
                "_started_at_dt": started_at,
            }
        )

    aggregated_rows.sort(
        key=lambda row: row.get("_started_at_dt") or datetime.min,
        reverse=True,
    )
    return [
        {key: value for key, value in row.items() if key != "_started_at_dt"}
        for row in aggregated_rows[:limit]
    ]


def list_table_recent_runs(table_name: str, *, limit: int = 10) -> list[dict[str, object]]:
    rows = [
        row
        for row in get_recent_job_runs(limit=400)
        if row.get("table_name") == table_name
    ]
    trimmed = rows[:limit]
    return [
        {
            "run_id": row.get("run_id"),
            "run_mode": row.get("run_mode"),
            "trigger_profile": row.get("trigger_profile"),
            "job_name": row.get("job_name"),
            "result": row.get("result"),
            "effective_date": row.get("effective_date"),
            "executed_at": row.get("executed_at"),
            "duration_seconds": row.get("duration_seconds"),
            "rows_written": row.get("rows_written"),
            "error": row.get("error"),
        }
        for row in trimmed
    ]
