from __future__ import annotations

from pathlib import Path
import subprocess

from sqlalchemy import text


def test_quote_identifier_uses_backticks():
    from apps.data_hub.data_pipeline_ts.scripts.backfill_date_counts import _quote_identifier

    assert _quote_identifier("stock_report_rc") == "`stock_report_rc`"


def test_collect_job_date_counts_for_range_job(sqlite_engine):
    from apps.data_hub.data_pipeline_ts.scripts.backfill_date_counts import collect_job_date_counts

    with sqlite_engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE stock_kpl_list (
                    trade_date TEXT,
                    tag TEXT,
                    ts_code TEXT
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO stock_kpl_list (trade_date, tag, ts_code) VALUES
                ('20260401', '涨停', '000001.SZ'),
                ('20260401', '炸板', '000002.SZ'),
                ('20260402', '涨停', '000003.SZ'),
                ('20260402', '涨停', '000004.SZ')
                """
            )
        )

    report = collect_job_date_counts(
        engine=sqlite_engine,
        job_name="kpl_list",
        start_date="20260401",
        end_date="20260402",
    )

    assert report.job_name == "kpl_list"
    assert report.table_name == "stock_kpl_list"
    assert report.date_column == "trade_date"
    assert report.rows == [("20260401", 2), ("20260402", 2)]
    assert report.total_rows == 4


def test_collect_job_date_counts_for_snapshot_job(sqlite_engine):
    from apps.data_hub.data_pipeline_ts.scripts.backfill_date_counts import collect_job_date_counts

    with sqlite_engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE stock_hm_list (
                    snapshot_date TEXT,
                    name TEXT
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO stock_hm_list (snapshot_date, name) VALUES
                ('20260411', 'A'),
                ('20260411', 'B')
                """
            )
        )

    report = collect_job_date_counts(
        engine=sqlite_engine,
        job_name="hm_list",
        snapshot_date="20260411",
    )

    assert report.job_name == "hm_list"
    assert report.table_name == "stock_hm_list"
    assert report.date_column == "snapshot_date"
    assert report.rows == [("20260411", 2)]
    assert report.total_rows == 2


def test_render_job_date_counts_report_includes_rows_and_total(sqlite_engine):
    from apps.data_hub.data_pipeline_ts.scripts.backfill_date_counts import (
        collect_job_date_counts,
        render_job_date_counts_report,
    )

    with sqlite_engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE stock_report_rc (
                    report_date TEXT,
                    ts_code TEXT
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO stock_report_rc (report_date, ts_code) VALUES
                ('20260401', '000001.SZ'),
                ('20260403', '000002.SZ')
                """
            )
        )

    report = collect_job_date_counts(
        engine=sqlite_engine,
        job_name="report_rc",
        start_date="20260401",
        end_date="20260411",
    )
    rendered = render_job_date_counts_report(report)

    assert "job=report_rc table=stock_report_rc date_column=report_date" in rendered
    assert "window=20260401~20260411" in rendered
    assert "20260401 1" in rendered
    assert "20260403 1" in rendered
    assert "total_rows=2" in rendered


def test_backfill_date_counts_script_runs_via_script_path_help():
    repo_root = Path(__file__).resolve().parents[4]
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "backfill_date_counts.py"

    result = subprocess.run(
        ["./apps/.venv/bin/python", str(script_path), "--help"],
        check=False,
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Report per-date row counts for selected backfill jobs." in result.stdout
