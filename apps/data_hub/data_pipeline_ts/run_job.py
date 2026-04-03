from __future__ import annotations

import argparse
import json
import time
from typing import Any, Mapping, Sequence
from uuid import uuid4

from apps.data_hub.data_pipeline_ts.execution.persistence import DatabaseWriter
from apps.data_hub.data_pipeline_ts.execution.rendering import _ensure_dataframe
from apps.data_hub.data_pipeline_ts.execution.selection import select_job_specs
from apps.data_hub.data_pipeline_ts.jobs.specs import JobRunResult, JobSpec


def _parse_param_value(raw_value: str) -> Any:
    value = raw_value.strip()
    if not value:
        return ""
    if value in {"true", "false", "null"} or value[0] in {'[', '{', '"'}:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def parse_param_assignments(assignments: Sequence[str] | None) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for assignment in assignments or ():
        if "=" not in assignment:
            raise ValueError(f"invalid --param {assignment!r}, expected key=value")
        key, raw_value = assignment.split("=", 1)
        normalized_key = key.strip()
        if not normalized_key:
            raise ValueError(f"invalid --param {assignment!r}, key cannot be empty")
        params[normalized_key] = _parse_param_value(raw_value)
    return params


def run_direct_job(
    *,
    job_name: str,
    params: Mapping[str, Any],
    job_specs: Sequence[JobSpec] | None = None,
    writer: DatabaseWriter | None = None,
) -> JobRunResult:
    spec = select_job_specs(job_specs, job_names=[job_name])[0]
    database_writer = writer or DatabaseWriter()
    run_id = uuid4().hex
    started_at = time.perf_counter()
    resolved_params = dict(params)

    try:
        fetcher = spec.fetcher_cls()
        frame = _ensure_dataframe(fetcher.fetch(**resolved_params))
        rows_fetched = int(len(frame.index))
        rows_written = database_writer.write(spec, frame) if rows_fetched else 0
        result = JobRunResult(
            job_name=spec.name,
            table_name=spec.table_name,
            params=resolved_params,
            rows_fetched=rows_fetched,
            rows_written=rows_written,
            duration_seconds=time.perf_counter() - started_at,
            status="success",
            run_id=run_id,
            run_mode="direct",
            trigger_profile=spec.profile.value,
        )
    except Exception as exc:
        result = JobRunResult(
            job_name=spec.name,
            table_name=spec.table_name,
            params=resolved_params,
            rows_fetched=0,
            rows_written=0,
            duration_seconds=time.perf_counter() - started_at,
            status="failed",
            error=str(exc),
            run_id=run_id,
            run_mode="direct",
            trigger_profile=spec.profile.value,
        )

    database_writer.record_run_result(result)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a single data_pipeline_ts job with explicit key=value params."
    )
    parser.add_argument("--job", required=True, help="Job name from jobs/catalog.py")
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        help="Repeated key=value param. JSON arrays/objects/bools are supported.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_direct_job(job_name=args.job, params=parse_param_assignments(args.param))
    print(
        json.dumps(
            {
                "job_name": result.job_name,
                "table_name": result.table_name,
                "status": result.status,
                "rows_fetched": result.rows_fetched,
                "rows_written": result.rows_written,
                "run_id": result.run_id,
                "params": result.params,
                "error": result.error,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if result.status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
