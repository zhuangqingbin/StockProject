from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Sequence

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from apps.data_hub.data_pipeline_ts.execution.persistence import get_engine


@dataclass(frozen=True)
class CountSpec:
    table_name: str
    date_column: str
    mode: str


@dataclass(frozen=True)
class JobDateCountReport:
    job_name: str
    table_name: str
    date_column: str
    rows: list[tuple[str, int]]
    total_rows: int
    mode: str
    window_label: str
    table_exists: bool


COUNT_SPECS: dict[str, CountSpec] = {
    "kpl_list": CountSpec(table_name="stock_kpl_list", date_column="trade_date", mode="range"),
    "report_rc": CountSpec(table_name="stock_report_rc", date_column="report_date", mode="range"),
    "cyq_chips": CountSpec(table_name="stock_cyq_chips", date_column="trade_date", mode="range"),
    "fina_audit": CountSpec(table_name="stock_fina_audit", date_column="ann_date", mode="range"),
    "hm_list": CountSpec(table_name="stock_hm_list", date_column="snapshot_date", mode="snapshot"),
    "pledge_detail": CountSpec(table_name="stock_pledge_detail", date_column="snapshot_date", mode="snapshot"),
}


def _quote_identifier(name: str) -> str:
    return f"`{name}`"


def _build_window_label(mode: str, *, start_date: str | None, end_date: str | None, snapshot_date: str | None) -> str:
    if mode == "snapshot":
        return snapshot_date or ""
    return f"{start_date or ''}~{end_date or ''}"


def collect_job_date_counts(
    *,
    engine: Engine,
    job_name: str,
    start_date: str | None = None,
    end_date: str | None = None,
    snapshot_date: str | None = None,
) -> JobDateCountReport:
    spec = COUNT_SPECS.get(job_name)
    if spec is None:
        raise ValueError(f"Unsupported job for date counts: {job_name}")

    if spec.mode == "range" and (not start_date or not end_date):
        raise ValueError(f"{job_name} date counts require start_date and end_date")
    if spec.mode == "snapshot" and not snapshot_date:
        raise ValueError(f"{job_name} date counts require snapshot_date")

    inspector = inspect(engine)
    if not inspector.has_table(spec.table_name):
        return JobDateCountReport(
            job_name=job_name,
            table_name=spec.table_name,
            date_column=spec.date_column,
            rows=[],
            total_rows=0,
            mode=spec.mode,
            window_label=_build_window_label(
                spec.mode,
                start_date=start_date,
                end_date=end_date,
                snapshot_date=snapshot_date,
            ),
            table_exists=False,
        )

    quoted_table = _quote_identifier(spec.table_name)
    quoted_column = _quote_identifier(spec.date_column)
    if spec.mode == "snapshot":
        sql = text(
            f"""
            SELECT {quoted_column} AS bucket, COUNT(*) AS row_count
            FROM {quoted_table}
            WHERE {quoted_column} = :snapshot_date
            GROUP BY {quoted_column}
            ORDER BY {quoted_column}
            """
        )
        params = {"snapshot_date": snapshot_date}
    else:
        sql = text(
            f"""
            SELECT {quoted_column} AS bucket, COUNT(*) AS row_count
            FROM {quoted_table}
            WHERE {quoted_column} BETWEEN :start_date AND :end_date
            GROUP BY {quoted_column}
            ORDER BY {quoted_column}
            """
        )
        params = {"start_date": start_date, "end_date": end_date}

    with engine.begin() as connection:
        rows = connection.execute(sql, params).all()

    normalized_rows = [(str(bucket), int(row_count)) for bucket, row_count in rows]
    return JobDateCountReport(
        job_name=job_name,
        table_name=spec.table_name,
        date_column=spec.date_column,
        rows=normalized_rows,
        total_rows=sum(count for _, count in normalized_rows),
        mode=spec.mode,
        window_label=_build_window_label(
            spec.mode,
            start_date=start_date,
            end_date=end_date,
            snapshot_date=snapshot_date,
        ),
        table_exists=True,
    )


def render_job_date_counts_report(report: JobDateCountReport) -> str:
    lines = [
        "[date-counts]",
        f"job={report.job_name} table={report.table_name} date_column={report.date_column}",
        f"window={report.window_label}",
    ]
    if not report.table_exists:
        lines.append("status=table_missing")
        lines.append("total_rows=0")
        return "\n".join(lines)

    if not report.rows:
        lines.append("status=no_rows")
        lines.append("total_rows=0")
        return "\n".join(lines)

    for bucket, row_count in report.rows:
        lines.append(f"{bucket} {row_count}")
    lines.append(f"total_rows={report.total_rows}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report per-date row counts for selected backfill jobs.")
    parser.add_argument("--job", required=True, choices=sorted(COUNT_SPECS))
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--snapshot-date")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = collect_job_date_counts(
        engine=get_engine(),
        job_name=args.job,
        start_date=args.start_date,
        end_date=args.end_date,
        snapshot_date=args.snapshot_date,
    )
    print(render_job_date_counts_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
