from __future__ import annotations

import argparse
from typing import Sequence

from apps.data_hub.data_pipeline_ts.execution import (
    _parse_csv_values,
    run_backfill,
    run_infrastructure,
    run_once,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run data_hub data_pipeline_ts jobs.")
    parser.add_argument("--mode", choices=("once", "backfill", "infrastructure"), default="once")
    parser.add_argument("--profiles", help="Comma-separated trigger profiles.")
    parser.add_argument("--jobs", help="Comma-separated job names.")
    parser.add_argument("--targets", help="Comma-separated infrastructure target names.")
    parser.add_argument("--as-of", help="Calendar date, format YYYY-MM-DD.")
    parser.add_argument("--start", help="Start date, format YYYYMMDD.")
    parser.add_argument("--end", help="End date, format YYYYMMDD.")
    parser.add_argument("--max-workers", type=int, help="Override max worker count per profile.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    profiles = _parse_csv_values(args.profiles)
    jobs = _parse_csv_values(args.jobs)

    if args.mode == "infrastructure":
        targets = _parse_csv_values(args.targets)
        if not targets:
            raise ValueError("--mode infrastructure requires --targets")
        run_infrastructure(target_names=targets, start=args.start, end=args.end)
        return 0

    if args.mode == "backfill":
        if not args.start or not args.end:
            raise ValueError("--mode backfill requires --start and --end")
        run_backfill(
            start=args.start,
            end=args.end,
            profiles=profiles,
            job_names=jobs,
            max_workers=args.max_workers,
        )
        return 0

    run_once(
        as_of=args.as_of,
        profiles=profiles,
        job_names=jobs,
        max_workers=args.max_workers,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
