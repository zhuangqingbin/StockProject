from __future__ import annotations

from dataclasses import replace

import pandas as pd
from sqlalchemy import inspect, text

from apps.data_hub.data_pipeline_ts.fetchers.base import ColumnDef, TableSchema
from apps.data_hub.data_pipeline_ts.jobs.profiles import ProfileId
from apps.data_hub.data_pipeline_ts.jobs.specs import JobRunResult, JobSpec
from apps.data_hub.data_pipeline_ts.execution.persistence import DatabaseWriter


def make_job_spec() -> JobSpec:
    return JobSpec(
        name="stock_daily",
        table_name="stock_daily",
        fetcher_cls=object,
        description="测试股票日线",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_CORE,
        params={"trade_date": "{{ trade_date }}"},
        scope_columns=("trade_date",),
        table_schema=TableSchema(
            columns={
                "ts_code": ColumnDef("VARCHAR(16)", nullable=False),
                "trade_date": ColumnDef("CHAR(8)", nullable=False),
                "close": ColumnDef("DOUBLE"),
            },
            composite_indexes=[("trade_date",), ("trade_date", "ts_code")],
        ),
    )


def test_writer_auto_creates_table_and_replaces_scope(sqlite_engine):
    writer = DatabaseWriter(engine=sqlite_engine)
    job_definition = make_job_spec()
    first_frame = pd.DataFrame(
        [
            {"ts_code": "000001.SZ", "trade_date": "20260317", "close": 12.3},
            {"ts_code": "000002.SZ", "trade_date": "20260317", "close": 8.7},
        ]
    )
    replacement_frame = pd.DataFrame(
        [{"ts_code": "000003.SZ", "trade_date": "20260317", "close": 9.9}]
    )

    assert writer.write(job_definition, first_frame) == 2
    assert writer.write(job_definition, replacement_frame) == 1

    result = pd.read_sql("SELECT * FROM stock_daily ORDER BY ts_code", sqlite_engine)
    assert result.to_dict("records") == [
        {"ts_code": "000003.SZ", "trade_date": "20260317", "close": 9.9}
    ]

    indexes = inspect(sqlite_engine).get_indexes("stock_daily")
    index_columns = {tuple(index["column_names"]) for index in indexes}
    assert ("trade_date",) in index_columns
    assert ("trade_date", "ts_code") in index_columns


def test_writer_records_job_run_log(sqlite_engine):
    writer = DatabaseWriter(engine=sqlite_engine)
    result = JobRunResult(
        job_name="stock_daily",
        table_name="stock_daily",
        params={"trade_date": "20260317"},
        rows_fetched=10,
        rows_written=10,
        duration_seconds=1.2,
        status="success",
    )

    writer.record_run_result(result)

    with sqlite_engine.begin() as connection:
        rows = connection.execute(text("SELECT job_name, status, rows_written FROM job_run_log")).all()

    assert rows == [("stock_daily", "success", 10)]


def test_writer_adds_missing_columns_to_existing_table(sqlite_engine):
    writer = DatabaseWriter(engine=sqlite_engine)
    job_definition = replace(
        make_job_spec(),
        table_name="evolving_daily",
        table_schema=TableSchema(
            columns={
                "ts_code": ColumnDef("VARCHAR(16)", nullable=False),
                "trade_date": ColumnDef("CHAR(8)", nullable=False),
                "close": ColumnDef("DOUBLE"),
                "open": ColumnDef("DOUBLE"),
            },
            composite_indexes=[("trade_date",), ("trade_date", "ts_code")],
        ),
    )

    with sqlite_engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE evolving_daily (
                    ts_code VARCHAR(16) NOT NULL,
                    trade_date CHAR(8) NOT NULL,
                    close DOUBLE
                )
                """
            )
        )

    frame = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20260317",
                "close": 12.3,
                "open": 12.1,
            }
        ]
    )

    assert writer.write(job_definition, frame) == 1

    result = pd.read_sql("SELECT ts_code, trade_date, close, open FROM evolving_daily", sqlite_engine)
    assert result.to_dict("records") == [
        {"ts_code": "000001.SZ", "trade_date": "20260317", "close": 12.3, "open": 12.1}
    ]


def test_writer_infers_and_persists_frame_columns_missing_from_schema(sqlite_engine):
    writer = DatabaseWriter(engine=sqlite_engine)
    job_definition = replace(
        make_job_spec(),
        table_name="doc_aligned_daily",
    )
    frame = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20260317",
                "close": 12.3,
                "list_date": "20200101",
                "status": "L",
                "turnover_rate": 3.14,
            }
        ]
    )

    assert writer.write(job_definition, frame) == 1

    result = pd.read_sql(
        "SELECT ts_code, trade_date, close, list_date, status, turnover_rate FROM doc_aligned_daily",
        sqlite_engine,
    )
    assert result.to_dict("records") == [
        {
            "ts_code": "000001.SZ",
            "trade_date": "20260317",
            "close": 12.3,
            "list_date": "20200101",
            "status": "L",
            "turnover_rate": 3.14,
        }
    ]


def test_writer_repairs_text_columns_before_creating_indexes(monkeypatch):
    executed_sql: list[str] = []

    class DummyConnection:
        def execute(self, statement):
            executed_sql.append(str(statement))

    class DummyBegin:
        def __enter__(self):
            return DummyConnection()

        def __exit__(self, exc_type, exc, tb):
            return False

    class DummyEngine:
        def begin(self):
            return DummyBegin()

    class DummyInspector:
        def get_columns(self, table_name):
            return [
                {"name": "ts_code", "type": "VARCHAR(16)"},
                {"name": "trade_date", "type": "TEXT"},
                {"name": "close", "type": "DOUBLE"},
            ]

        def get_indexes(self, table_name):
            return [
                {"column_names": ["trade_date"]},
                {"column_names": ["trade_date", "ts_code"]},
            ]

    monkeypatch.setattr(
        "apps.data_hub.data_pipeline_ts.execution.persistence.MetaData.create_all",
        lambda self, bind, tables, checkfirst: None,
    )
    monkeypatch.setattr(
        "apps.data_hub.data_pipeline_ts.execution.persistence.inspect",
        lambda engine: DummyInspector(),
    )

    writer = DatabaseWriter(engine=DummyEngine())
    writer.ensure_table(make_job_spec())

    assert executed_sql == [
        "ALTER TABLE `stock_daily` MODIFY COLUMN `trade_date` CHAR(8) NOT NULL"
    ]


def test_writer_repairs_existing_varchar_columns_to_text_when_schema_requires_it(monkeypatch):
    executed_sql: list[str] = []

    class DummyConnection:
        def execute(self, statement):
            executed_sql.append(str(statement))

    class DummyBegin:
        def __enter__(self):
            return DummyConnection()

        def __exit__(self, exc_type, exc, tb):
            return False

    class DummyEngine:
        def begin(self):
            return DummyBegin()

    class DummyInspector:
        def get_columns(self, table_name):
            return [
                {"name": "ts_code", "type": "VARCHAR(16)"},
                {"name": "ann_date", "type": "CHAR(8)"},
                {"name": "wide_metric", "type": "VARCHAR(255)"},
            ]

        def get_indexes(self, table_name):
            return [
                {"column_names": ["ann_date"]},
                {"column_names": ["ann_date", "ts_code"]},
            ]

    monkeypatch.setattr(
        "apps.data_hub.data_pipeline_ts.execution.persistence.MetaData.create_all",
        lambda self, bind, tables, checkfirst: None,
    )
    monkeypatch.setattr(
        "apps.data_hub.data_pipeline_ts.execution.persistence.inspect",
        lambda engine: DummyInspector(),
    )

    writer = DatabaseWriter(engine=DummyEngine())
    job_definition = replace(
        make_job_spec(),
        table_name="wide_financial",
        scope_columns=("ann_date",),
        table_schema=TableSchema(
            columns={
                "ts_code": ColumnDef("VARCHAR(16)", nullable=False),
                "ann_date": ColumnDef("CHAR(8)", nullable=False),
                "wide_metric": ColumnDef("TEXT"),
            },
            composite_indexes=[("ann_date",), ("ann_date", "ts_code")],
        ),
    )

    writer.ensure_table(job_definition)

    assert executed_sql == [
        "ALTER TABLE `wide_financial` MODIFY COLUMN `wide_metric` TEXT NULL"
    ]


def test_writer_repairs_existing_columns_before_adding_missing_columns(monkeypatch):
    executed_sql: list[str] = []
    inspector_calls = {"count": 0}

    class DummyConnection:
        def execute(self, statement):
            executed_sql.append(str(statement))

    class DummyBegin:
        def __enter__(self):
            return DummyConnection()

        def __exit__(self, exc_type, exc, tb):
            return False

    class DummyEngine:
        def begin(self):
            return DummyBegin()

    class DummyInspector:
        def get_columns(self, table_name):
            inspector_calls["count"] += 1
            if inspector_calls["count"] == 1:
                return [
                    {"name": "ts_code", "type": "VARCHAR(16)"},
                    {"name": "ann_date", "type": "CHAR(8)"},
                    {"name": "wide_metric", "type": "VARCHAR(255)"},
                ]
            return [
                {"name": "ts_code", "type": "VARCHAR(16)"},
                {"name": "ann_date", "type": "CHAR(8)"},
                {"name": "wide_metric", "type": "TEXT"},
            ]

        def get_indexes(self, table_name):
            return [
                {"column_names": ["ann_date"]},
                {"column_names": ["ann_date", "ts_code"]},
            ]

    monkeypatch.setattr(
        "apps.data_hub.data_pipeline_ts.execution.persistence.MetaData.create_all",
        lambda self, bind, tables, checkfirst: None,
    )
    monkeypatch.setattr(
        "apps.data_hub.data_pipeline_ts.execution.persistence.inspect",
        lambda engine: DummyInspector(),
    )

    writer = DatabaseWriter(engine=DummyEngine())
    job_definition = replace(
        make_job_spec(),
        table_name="wide_financial",
        scope_columns=("ann_date",),
        table_schema=TableSchema(
            columns={
                "ts_code": ColumnDef("VARCHAR(16)", nullable=False),
                "ann_date": ColumnDef("CHAR(8)", nullable=False),
                "wide_metric": ColumnDef("TEXT"),
                "new_metric": ColumnDef("TEXT"),
            },
            composite_indexes=[("ann_date",), ("ann_date", "ts_code")],
        ),
    )

    writer.ensure_table(job_definition)

    assert executed_sql == [
        "ALTER TABLE `wide_financial` MODIFY COLUMN `wide_metric` TEXT NULL",
        "ALTER TABLE `wide_financial` ADD COLUMN `new_metric` TEXT NULL",
    ]
