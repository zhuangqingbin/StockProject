from __future__ import annotations

from sqlalchemy import text

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema
from apps.data_hub.data_pipeline_ts.jobs.profiles import ProfileId
from apps.data_hub.data_pipeline_ts.jobs.specs import JobSpec


class DemoDirectFetch(BaseFetcher):
    fields = ["trade_date", "ts_code", "close"]
    table_schema = TableSchema(
        columns={
            "trade_date": ColumnDef("CHAR(8)", nullable=False),
            "ts_code": ColumnDef("VARCHAR(16)", nullable=False),
            "close": ColumnDef("DOUBLE", nullable=True),
        },
        composite_indexes=[("trade_date",), ("trade_date", "ts_code")],
    )

    def read_data(self, **kwargs):
        return [{"trade_date": kwargs["trade_date"], "ts_code": "000001.SZ", "close": 12.3}]


def test_run_direct_job_writes_rows_and_records_runtime_log(sqlite_engine):
    from apps.data_hub.data_pipeline_ts.execution.persistence import DatabaseWriter
    from apps.data_hub.data_pipeline_ts.run_job import run_direct_job

    writer = DatabaseWriter(engine=sqlite_engine)
    spec = JobSpec(
        name="demo_direct",
        table_name="demo_direct",
        fetcher_cls=DemoDirectFetch,
        description="demo direct job",
        profile=ProfileId.MANUAL,
        params={},
        scope_columns=("trade_date",),
        table_schema=DemoDirectFetch.table_schema,
    )

    result = run_direct_job(
        job_name="demo_direct",
        params={"trade_date": "20260317"},
        job_specs=[spec],
        writer=writer,
    )

    assert result.status == "success"
    assert result.run_mode == "direct"
    assert result.rows_fetched == 1
    assert result.rows_written == 1

    with sqlite_engine.begin() as connection:
        rows = connection.execute(
            text("SELECT trade_date, ts_code, close FROM demo_direct")
        ).all()
        logs = connection.execute(
            text("SELECT job_name, run_mode, status, rows_written FROM job_run_log")
        ).all()

    assert rows == [("20260317", "000001.SZ", 12.3)]
    assert logs == [("demo_direct", "direct", "success", 1)]


def test_parse_param_assignments_supports_json_literals():
    from apps.data_hub.data_pipeline_ts.run_job import parse_param_assignments

    params = parse_param_assignments(
        [
            "start_date=20260101",
            'stock_codes=["600000.SH","000001.SZ"]',
            "strict=true",
        ]
    )

    assert params == {
        "start_date": "20260101",
        "stock_codes": ["600000.SH", "000001.SZ"],
        "strict": True,
    }
