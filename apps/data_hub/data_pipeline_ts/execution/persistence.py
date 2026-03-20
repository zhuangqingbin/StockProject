from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
from sqlalchemy import BigInteger, Column, Date, DateTime, Float, Index, Integer, MetaData, String, Table, Text, create_engine, inspect, text
from sqlalchemy.engine import Engine

from apps.data_hub.data_pipeline_ts.fetchers.base import ColumnDef, TableSchema
from apps.data_hub.data_pipeline_ts.jobs.specs import InfrastructureSpec, JobRunResult, JobSpec
from shared.stock_core.db import build_mysql_url as build_shared_mysql_url


RuntimeSpec = JobSpec | InfrastructureSpec
INDEX_UNSAFE_TEXT_TYPES = {
    "TEXT",
    "TINYTEXT",
    "MEDIUMTEXT",
    "LONGTEXT",
    "BLOB",
    "TINYBLOB",
    "MEDIUMBLOB",
    "LONGBLOB",
}

_engine: Engine | None = None


def build_mysql_url() -> str:
    return build_shared_mysql_url("TS_MYSQL_DATABASE")


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(build_mysql_url(), pool_recycle=3600)
    return _engine


def validate_frame_columns(table_name: str, frame: pd.DataFrame, schema: TableSchema) -> pd.DataFrame:
    expected_columns = list(schema.columns)
    actual_columns = list(frame.columns)
    if set(expected_columns) != set(actual_columns):
        raise ValueError(
            f"Schema mismatch for table={table_name}: "
            f"expected={expected_columns}, actual={actual_columns}"
    )
    return frame.reindex(columns=expected_columns)


def _infer_column_def(column_name: str, series: pd.Series) -> ColumnDef:
    normalized_name = column_name.lower()
    non_null = series.dropna()

    if normalized_name == "ts_code":
        return ColumnDef("VARCHAR(16)", nullable=True)

    if not non_null.empty:
        as_strings = non_null.astype(str)
        if (
            normalized_name.endswith("_date")
            or normalized_name in {"cal_date", "trade_date", "ann_date", "end_date", "pub_date", "imp_date", "snapshot_date"}
        ) and as_strings.map(lambda value: len(value) == 8 and value.isdigit()).all():
            return ColumnDef("CHAR(8)", nullable=True)

    if pd.api.types.is_bool_dtype(series) or normalized_name.startswith("is_"):
        return ColumnDef("TINYINT", nullable=True)

    if pd.api.types.is_numeric_dtype(series):
        return ColumnDef("DOUBLE", nullable=True)

    if non_null.empty:
        return ColumnDef("TEXT", nullable=True)

    max_length = int(non_null.astype(str).map(len).max())
    if max_length <= 8 and normalized_name.endswith("_type"):
        return ColumnDef("VARCHAR(8)", nullable=True)
    if max_length <= 16:
        return ColumnDef("VARCHAR(16)", nullable=True)
    if max_length <= 32:
        return ColumnDef("VARCHAR(32)", nullable=True)
    if max_length <= 64:
        return ColumnDef("VARCHAR(64)", nullable=True)
    if max_length <= 255:
        return ColumnDef("VARCHAR(255)", nullable=True)
    return ColumnDef("TEXT", nullable=True)


def resolve_runtime_schema(table_name: str, frame: pd.DataFrame, schema: TableSchema) -> TableSchema:
    missing_columns = [column_name for column_name in schema.columns if column_name not in frame.columns]
    if missing_columns:
        raise ValueError(
            f"Schema mismatch for table={table_name}: "
            f"schema columns missing from frame={missing_columns}, actual={list(frame.columns)}"
        )

    columns: dict[str, ColumnDef] = {}
    for column_name in frame.columns:
        column_def = schema.columns.get(column_name)
        columns[column_name] = column_def or _infer_column_def(column_name, frame[column_name])

    return TableSchema(columns=columns, composite_indexes=schema.composite_indexes)


def _quote_identifier(name: str) -> str:
    return f"`{name.replace('`', '``')}`"


def _sqlalchemy_type(column_def: ColumnDef):
    dtype = column_def.dtype.upper()
    if dtype.startswith("VARCHAR("):
        length = int(dtype.removeprefix("VARCHAR(").removesuffix(")"))
        return String(length)
    if dtype.startswith("CHAR("):
        length = int(dtype.removeprefix("CHAR(").removesuffix(")"))
        return String(length)
    if dtype == "DOUBLE":
        return Float()
    if dtype == "TINYINT":
        return Integer()
    if dtype == "INT":
        return Integer()
    if dtype == "BIGINT":
        return BigInteger()
    if dtype == "DATE":
        return Date()
    if dtype == "DATETIME":
        return DateTime()
    return Text()


def _build_table(table_name: str, schema: TableSchema, metadata: MetaData) -> Table:
    columns = [
        Column(
            column_name,
            _sqlalchemy_type(column_def),
            nullable=column_def.nullable,
            comment=column_def.comment or None,
        )
        for column_name, column_def in schema.columns.items()
    ]
    return Table(table_name, metadata, *columns)


def _column_sql(column_name: str, column_def: ColumnDef) -> str:
    nullable_sql = "NULL" if column_def.nullable else "NOT NULL"
    return f"{_quote_identifier(column_name)} {column_def.dtype} {nullable_sql}"


def _runtime_log_column_sql(column: Column, engine: Engine) -> str:
    compiled_type = column.type.compile(dialect=engine.dialect)
    nullable_sql = "NULL" if column.nullable else "NOT NULL"
    return f"{_quote_identifier(column.name)} {compiled_type} {nullable_sql}"


def _needs_column_type_repair(existing_type: object, column_def: ColumnDef) -> bool:
    desired_dtype = column_def.dtype.upper()

    normalized_existing_type = str(existing_type).upper()
    if desired_dtype.startswith("CHAR(") or desired_dtype.startswith("VARCHAR("):
        return normalized_existing_type in INDEX_UNSAFE_TEXT_TYPES

    if desired_dtype == "TEXT":
        return (
            normalized_existing_type.startswith("VARCHAR(")
            or normalized_existing_type.startswith("CHAR(")
        )

    return False


class DatabaseWriter:
    def __init__(self, engine: Engine | None = None):
        self.engine = engine or get_engine()

    def ensure_table(self, spec: RuntimeSpec, schema: TableSchema | None = None) -> None:
        schema = schema or spec.table_schema
        if schema is None:
            raise ValueError(f"Job {spec.name} is missing table_schema")

        metadata = MetaData()
        table = _build_table(spec.table_name, schema, metadata)
        metadata.create_all(self.engine, tables=[table], checkfirst=True)

        inspector = inspect(self.engine)
        existing_columns_by_name = {
            column["name"]: column for column in inspector.get_columns(spec.table_name)
        }
        repairable_columns = [
            (column_name, column_def)
            for column_name, column_def in schema.columns.items()
            if column_name in existing_columns_by_name
            and _needs_column_type_repair(
                existing_columns_by_name[column_name].get("type"),
                column_def,
            )
        ]
        if repairable_columns:
            with self.engine.begin() as connection:
                for column_name, column_def in repairable_columns:
                    connection.execute(
                        text(
                            f"ALTER TABLE {_quote_identifier(spec.table_name)} "
                            f"MODIFY COLUMN {_column_sql(column_name, column_def)}"
                        )
                    )
            inspector = inspect(self.engine)

        existing_columns = {column["name"] for column in inspector.get_columns(spec.table_name)}
        missing_columns = [
            (column_name, column_def)
            for column_name, column_def in schema.columns.items()
            if column_name not in existing_columns
        ]
        if missing_columns:
            with self.engine.begin() as connection:
                for column_name, column_def in missing_columns:
                    connection.execute(
                        text(
                            f"ALTER TABLE {_quote_identifier(spec.table_name)} "
                            f"ADD COLUMN {_column_sql(column_name, column_def)}"
                        )
                    )
            inspector = inspect(self.engine)

        existing_indexes = {tuple(index["column_names"]) for index in inspector.get_indexes(spec.table_name)}
        for index_columns in schema.composite_indexes:
            if tuple(index_columns) in existing_indexes:
                continue
            index_name = f"idx_{spec.table_name}_{'_'.join(index_columns)}"
            Index(index_name, *(table.c[column_name] for column_name in index_columns)).create(
                bind=self.engine,
                checkfirst=True,
            )

    def write(self, spec: RuntimeSpec, frame: pd.DataFrame) -> int:
        schema = spec.table_schema
        if frame.empty:
            return 0
        if schema is None:
            raise ValueError(f"Job {spec.name} is missing table_schema")

        runtime_schema = resolve_runtime_schema(spec.table_name, frame, schema)
        validated = validate_frame_columns(spec.table_name, frame, runtime_schema)
        self.ensure_table(spec, schema=runtime_schema)

        with self.engine.begin() as connection:
            self._delete_existing_scope(spec, validated, connection)
            validated.to_sql(spec.table_name, con=connection, if_exists="append", index=False)
        return int(len(validated.index))

    def _delete_existing_scope(self, spec: RuntimeSpec, frame: pd.DataFrame, connection: Any) -> None:
        if not spec.scope_columns:
            return

        scoped_values = frame.loc[:, list(spec.scope_columns)].drop_duplicates().to_dict("records")
        if not scoped_values:
            return

        conditions = " AND ".join(
            f"{_quote_identifier(column_name)} = :{column_name}"
            for column_name in spec.scope_columns
        )
        delete_sql = text(f"DELETE FROM {_quote_identifier(spec.table_name)} WHERE {conditions}")
        for scoped_row in scoped_values:
            connection.execute(delete_sql, scoped_row)

    def record_run_result(self, result: JobRunResult) -> None:
        metadata = MetaData()
        job_run_log = Table(
            "job_run_log",
            metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("run_id", String(64), nullable=True),
            Column("run_mode", String(32), nullable=True),
            Column("trigger_profile", String(64), nullable=True),
            Column("job_name", String(64), nullable=False),
            Column("table_name", String(64), nullable=True),
            Column("status", String(16), nullable=False),
            Column("rows_fetched", Integer, nullable=False),
            Column("rows_written", Integer, nullable=False),
            Column("duration_seconds", Float(), nullable=False),
            Column("error", Text(), nullable=True),
            Column("as_of_date", String(8), nullable=True),
            Column("effective_date", String(8), nullable=True),
            Column("executed_at", DateTime(), nullable=False),
        )
        metadata.create_all(self.engine, tables=[job_run_log], checkfirst=True)
        inspector = inspect(self.engine)
        existing_columns = {column["name"] for column in inspector.get_columns("job_run_log")}
        missing_columns = [
            column
            for column in job_run_log.columns
            if column.name not in existing_columns
        ]
        if missing_columns:
            with self.engine.begin() as connection:
                for column in missing_columns:
                    connection.execute(
                        text(
                            f"ALTER TABLE {_quote_identifier('job_run_log')} "
                            f"ADD COLUMN {_runtime_log_column_sql(column, self.engine)}"
                        )
                    )

        payload = {
            "run_id": result.run_id,
            "run_mode": result.run_mode,
            "trigger_profile": result.trigger_profile,
            "job_name": result.job_name,
            "table_name": result.table_name,
            "status": result.status,
            "rows_fetched": result.rows_fetched,
            "rows_written": result.rows_written,
            "duration_seconds": result.duration_seconds,
            "error": result.error,
            "as_of_date": result.as_of_date,
            "effective_date": result.effective_date,
            "executed_at": result.executed_at if isinstance(result.executed_at, datetime) else datetime.utcnow(),
        }
        with self.engine.begin() as connection:
            connection.execute(job_run_log.insert().values(**payload))
