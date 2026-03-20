from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.data_hub.data_pipeline_ts.execution.persistence import get_engine
from apps.data_hub.data_pipeline_ts.jobs.catalog import ALL_JOBS, INFRASTRUCTURE_TARGETS
from apps.data_hub.data_pipeline_ts.schema_calibration import (
    compare_frames_to_schema,
    resolve_sample_param_sets,
    resolve_sparse_column_param_sets,
    unobserved_schema_columns,
)


def runtime_specs():
    return [*ALL_JOBS, *INFRASTRUCTURE_TARGETS.values()]


def specs_by_name():
    return {spec.name: spec for spec in runtime_specs()}


def report_path_from_arg(raw_value: str) -> Path:
    path = Path(raw_value)
    if path.is_absolute():
        return path
    return Path.cwd() / path


def module_path_for_spec_name(name: str) -> Path:
    spec = specs_by_name()[name]
    return Path.cwd() / (spec.fetcher_cls.__module__.replace(".", "/") + ".py")


def build_report(report_path: Path) -> None:
    engine = get_engine()
    results = []
    failures = []

    for index, spec in enumerate(runtime_specs(), start=1):
        started_at = time.time()
        param_sets = resolve_sample_param_sets(spec, engine)
        print(
            f"[{index}/{len(runtime_specs())}] {spec.name} sample_count={len(param_sets)} param_sets={param_sets}",
            flush=True,
        )
        try:
            fetcher = spec.fetcher_cls()
            frames = [fetcher.fetch(**params) for params in param_sets]
            if spec.table_schema is not None:
                missing_columns = unobserved_schema_columns(frames, spec.table_schema)
                extra_param_sets = [
                    params
                    for params in resolve_sparse_column_param_sets(
                        spec,
                        engine,
                        missing_columns,
                        max_param_sets=min(max(len(missing_columns), 6), 40),
                    )
                    if params not in param_sets
                ]
                if extra_param_sets:
                    print(
                        f"  extra_sample_count={len(extra_param_sets)} extra_param_sets={extra_param_sets}",
                        flush=True,
                    )
                    param_sets.extend(extra_param_sets)
                    frames.extend(fetcher.fetch(**params) for params in extra_param_sets)
            if frames:
                frame = pd.concat(frames, ignore_index=True, sort=False)
            else:
                frame = pd.DataFrame()
            diffs = compare_frames_to_schema(frames, spec.table_schema) if spec.table_schema is not None else {}
            result = {
                "name": spec.name,
                "table_name": spec.table_name,
                "rows": int(len(frame.index)),
                "params": param_sets[0] if param_sets else {},
                "param_sets": param_sets,
                "sample_count": len(param_sets),
                "diff_count": len(diffs),
                "diffs": {column_name: column_def.dtype for column_name, column_def in diffs.items()},
                "duration_seconds": round(time.time() - started_at, 3),
            }
            results.append(result)
            print(
                f"  ok rows={result['rows']} diffs={result['diff_count']} seconds={result['duration_seconds']}",
                flush=True,
            )
        except Exception as exc:  # pragma: no cover - exercised against live API
            failure = {
                "name": spec.name,
                "table_name": spec.table_name,
                "params": param_sets[0] if param_sets else {},
                "param_sets": param_sets,
                "sample_count": len(param_sets),
                "error": repr(exc),
                "duration_seconds": round(time.time() - started_at, 3),
            }
            failures.append(failure)
            print(
                f"  failed seconds={failure['duration_seconds']} error={failure['error']}",
                flush=True,
            )

    payload = {"results": results, "failures": failures}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report={report_path}", flush=True)
    print(f"success={len(results)} failures={len(failures)}", flush=True)


def apply_report(report_path: Path) -> None:
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    changed_fetchers = 0
    changed_columns = 0

    for result in payload["results"]:
        diffs: dict[str, str] = result.get("diffs", {})
        if not diffs:
            continue

        fetcher_path = module_path_for_spec_name(result["name"])
        source = fetcher_path.read_text(encoding="utf-8")
        updated_source = source
        for column_name, dtype in diffs.items():
            pattern = re.compile(rf'("{re.escape(column_name)}": ColumnDef\(")([^"]+)(")')
            updated_source, count = pattern.subn(rf'\1{dtype}\3', updated_source, count=1)
            if count != 1:
                raise ValueError(
                    f"Failed to update {result['name']}.{column_name} in {fetcher_path}"
                )

        if updated_source != source:
            fetcher_path.write_text(updated_source, encoding="utf-8")
            changed_fetchers += 1
            changed_columns += len(diffs)
            print(f"updated {fetcher_path} columns={len(diffs)}", flush=True)

    print(f"applied changed_fetchers={changed_fetchers} changed_columns={changed_columns}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibrate fetcher schemas from live TuShare samples.")
    parser.add_argument(
        "--report-path",
        default="apps/data_hub/data_pipeline_ts/.cache/schema_calibration_report.json",
        help="JSON report path",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply an existing report to fetcher schema files",
    )
    args = parser.parse_args()

    report_path = report_path_from_arg(args.report_path)
    if args.apply:
        apply_report(report_path)
        return

    build_report(report_path)


if __name__ == "__main__":
    main()
