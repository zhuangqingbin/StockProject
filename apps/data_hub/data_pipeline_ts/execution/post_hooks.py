from __future__ import annotations

import os
import time
from datetime import date
from pathlib import Path
from typing import Sequence

from apps.data_hub.data_pipeline_ts.execution.persistence import DatabaseWriter
from apps.data_hub.data_pipeline_ts.jobs.profiles import ProfileId
from apps.data_hub.data_pipeline_ts.jobs.specs import JobRunResult

AUTO_PUBLISH_JOB_NAME = "quant_research_publish"
AUTO_PUBLISH_TABLE_NAME = "research_snapshot"
AUTO_PUBLISH_TRIGGER_PROFILE = ProfileId.REFERENCE_CALENDAR_NIGHTLY.value


def _is_truthy(raw_value: str | None) -> bool:
    return (raw_value or "").strip().lower() in {"1", "true", "yes", "on"}


def _auto_publish_enabled() -> bool:
    return _is_truthy(os.getenv("QV_RESEARCH_AUTO_PUBLISH_ENABLED"))


def _current_as_of_date(raw_as_of: str | None) -> str:
    if raw_as_of:
        return raw_as_of
    return date.today().isoformat()


def _build_publish_params(raw_as_of: str | None) -> dict[str, object]:
    as_of = _current_as_of_date(raw_as_of)
    output_dir = os.getenv(
        "QV_RESEARCH_AUTO_OUTPUT_DIR",
        "apps/quant_platform/research/output/full_research",
    )
    return {
        "start_date": os.getenv("QV_RESEARCH_AUTO_START_DATE", "2018-01-01"),
        "end_date": as_of,
        "output_dir": output_dir,
        "picks_limit": int(os.getenv("QV_RESEARCH_AUTO_PICKS_LIMIT", "20")),
        "include_chip_distribution": not _is_truthy(os.getenv("QV_RESEARCH_AUTO_SKIP_CHIP_DISTRIBUTION")),
    }


def _should_trigger_auto_publish(
    *,
    mode: str,
    profiles: Sequence[str] | None,
    job_names: Sequence[str] | None,
    results: Sequence[JobRunResult],
) -> bool:
    if mode != "once" or not _auto_publish_enabled() or not results or job_names:
        return False
    if any(result.status != "success" for result in results):
        return False
    requested_profiles = set(profiles or [])
    if requested_profiles and AUTO_PUBLISH_TRIGGER_PROFILE not in requested_profiles:
        return False
    return any(result.trigger_profile == AUTO_PUBLISH_TRIGGER_PROFILE for result in results)


def _run_quant_research_publish(params: dict[str, object]) -> dict[str, object]:
    from apps.quant_platform.research.publishing import publish_research_snapshot
    from apps.quant_platform.research.scripts.run_factor_research import run_full_factor_research

    output_dir = Path(str(params["output_dir"]))
    run_full_factor_research(
        start_date=str(params["start_date"]),
        end_date=str(params["end_date"]),
        output_dir=output_dir,
        include_chip_distribution=bool(params.get("include_chip_distribution", True)),
    )
    return publish_research_snapshot(
        output_root=output_dir.parent,
        full_research_dir=output_dir,
        picks_limit=int(params["picks_limit"]),
    )


def maybe_run_quant_research_publish(
    *,
    mode: str,
    profiles: Sequence[str] | None,
    job_names: Sequence[str] | None,
    results: Sequence[JobRunResult],
    as_of: str | None,
    writer: DatabaseWriter | None = None,
) -> list[JobRunResult]:
    if not _should_trigger_auto_publish(mode=mode, profiles=profiles, job_names=job_names, results=results):
        return []

    params = _build_publish_params(as_of)
    started_at = time.perf_counter()
    compact_as_of = _current_as_of_date(as_of).replace("-", "")

    try:
        manifest = _run_quant_research_publish(params)
        factor_count = int(manifest.get("factor_count", 0))
        publish_result = JobRunResult(
            job_name=AUTO_PUBLISH_JOB_NAME,
            table_name=AUTO_PUBLISH_TABLE_NAME,
            params=params,
            rows_fetched=factor_count,
            rows_written=factor_count,
            duration_seconds=time.perf_counter() - started_at,
            status="success",
            run_mode="once",
            trigger_profile=AUTO_PUBLISH_TRIGGER_PROFILE,
            as_of_date=compact_as_of,
            effective_date=compact_as_of,
        )
    except Exception as exc:
        publish_result = JobRunResult(
            job_name=AUTO_PUBLISH_JOB_NAME,
            table_name=AUTO_PUBLISH_TABLE_NAME,
            params=params,
            rows_fetched=0,
            rows_written=0,
            duration_seconds=time.perf_counter() - started_at,
            status="failed",
            error=str(exc),
            run_mode="once",
            trigger_profile=AUTO_PUBLISH_TRIGGER_PROFILE,
            as_of_date=compact_as_of,
            effective_date=compact_as_of,
        )

    if writer is not None:
        writer.record_run_result(publish_result)
    return [publish_result]
