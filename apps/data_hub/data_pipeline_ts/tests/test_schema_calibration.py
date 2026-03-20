from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from apps.data_hub.data_pipeline_ts.fetchers.base import ColumnDef, TableSchema
from apps.data_hub.data_pipeline_ts.jobs.specs import InfrastructureSpec, JobSpec
from apps.data_hub.data_pipeline_ts.jobs.profiles import ProfileId
from apps.data_hub.data_pipeline_ts.schema_calibration import (
    compare_frame_to_schema,
    compare_frames_to_schema,
    infer_column_def_from_series,
    resolve_sample_params,
    resolve_sample_param_sets,
    resolve_sparse_column_param_sets,
)


def make_job_spec(
    *,
    name: str = "demo",
    table_name: str = "demo_table",
    params: dict[str, object] | None = None,
    scope_columns: tuple[str, ...] = (),
) -> JobSpec:
    return JobSpec(
        name=name,
        table_name=table_name,
        fetcher_cls=object,
        description="demo",
        profile=ProfileId.MANUAL,
        params=dict(params or {}),
        scope_columns=scope_columns,
        table_schema=TableSchema(columns={}),
    )


def test_infer_column_def_from_numeric_like_object_series_returns_double():
    series = pd.Series(["1", "2.5", None, "0"])

    assert infer_column_def_from_series("div_receiv", series) == ColumnDef("DOUBLE", nullable=True)


def test_infer_column_def_from_date_like_series_returns_char_8():
    series = pd.Series(["20260318", "20260317", None])

    assert infer_column_def_from_series("ann_date", series) == ColumnDef("CHAR(8)", nullable=True)


def test_infer_column_def_from_div_listdate_series_returns_char_8():
    series = pd.Series(["20260318", "20260317", None])

    assert infer_column_def_from_series("div_listdate", series) == ColumnDef("CHAR(8)", nullable=True)


def test_infer_column_def_from_short_type_series_returns_varchar():
    series = pd.Series(["1", "2", "10", None])

    assert infer_column_def_from_series("report_type", series) == ColumnDef("VARCHAR(8)", nullable=True)


def test_infer_column_def_from_zero_one_type_series_stays_varchar():
    series = pd.Series(["0", "1", "1"])

    assert infer_column_def_from_series("comp_type", series) == ColumnDef("VARCHAR(8)", nullable=True)


def test_infer_column_def_from_long_text_series_returns_text():
    series = pd.Series(["x" * 300, "short", None])

    assert infer_column_def_from_series("business_scope", series) == ColumnDef("TEXT", nullable=True)


def test_infer_column_def_from_ts_code_series_returns_varchar_16():
    series = pd.Series(["000001.SZ", "600000.SH"])

    assert infer_column_def_from_series("ts_code", series) == ColumnDef("VARCHAR(16)", nullable=True)


def test_infer_column_def_from_symbol_series_keeps_string_type():
    series = pd.Series(["000001", "600000"])

    assert infer_column_def_from_series("symbol", series) == ColumnDef("VARCHAR(8)", nullable=True)


def test_infer_column_def_from_code_series_keeps_string_type():
    series = pd.Series(["001234", "920069"])

    assert infer_column_def_from_series("sub_code", series) == ColumnDef("VARCHAR(8)", nullable=True)


def test_infer_column_def_from_time_series_keeps_string_type():
    series = pd.Series(["92503", "143650", "95830"])

    assert infer_column_def_from_series("first_time", series) == ColumnDef("VARCHAR(8)", nullable=True)


def test_infer_column_def_from_zero_one_series_returns_tinyint():
    series = pd.Series(["0", "1", "0"])

    assert infer_column_def_from_series("side", series) == ColumnDef("TINYINT", nullable=True)


def test_compare_frame_to_schema_returns_changed_columns_only():
    frame = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "ann_date": ["20260318"],
            "div_receiv": ["12.5"],
            "holder_name": ["测试股东"],
        }
    )
    schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True),
            "ann_date": ColumnDef("CHAR(8)", nullable=True),
            "div_receiv": ColumnDef("TEXT", nullable=True),
            "holder_name": ColumnDef("VARCHAR(255)", nullable=True),
        }
    )

    assert compare_frame_to_schema(frame, schema) == {
        "div_receiv": ColumnDef("DOUBLE", nullable=True),
    }


def test_compare_frames_to_schema_uses_historical_non_null_values():
    latest_frame = pd.DataFrame(
        {
            "ann_date": ["20260318"],
            "lending_funds": [None],
        }
    )
    historical_frame = pd.DataFrame(
        {
            "ann_date": ["20200103"],
            "lending_funds": ["4353213000.0"],
        }
    )
    schema = TableSchema(
        columns={
            "ann_date": ColumnDef("CHAR(8)", nullable=True),
            "lending_funds": ColumnDef("TEXT", nullable=True),
        }
    )

    assert compare_frames_to_schema([latest_frame, historical_frame], schema) == {
        "lending_funds": ColumnDef("DOUBLE", nullable=True),
    }


def test_resolve_sample_params_uses_latest_param_column_value(sqlite_engine):
    with sqlite_engine.begin() as connection:
        connection.execute(text("CREATE TABLE stock_daily (trade_date CHAR(8), close DOUBLE)"))
        connection.execute(
            text(
                """
                INSERT INTO stock_daily (trade_date, close)
                VALUES ('20260317', 1.0), ('20260318', 2.0)
                """
            )
        )

    spec = make_job_spec(
        name="stock_daily",
        table_name="stock_daily",
        params={"trade_date": "{trade_date}"},
        scope_columns=("trade_date",),
    )

    assert resolve_sample_params(spec, sqlite_engine) == {"trade_date": "20260318"}


def test_resolve_sample_param_sets_spreads_across_successful_history(sqlite_engine):
    with sqlite_engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE job_run_log (
                    job_name VARCHAR(64),
                    status VARCHAR(16),
                    rows_written INTEGER,
                    effective_date CHAR(8),
                    as_of_date CHAR(8)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO job_run_log (job_name, status, rows_written, effective_date, as_of_date)
                VALUES
                    ('balancesheet_vip', 'success', 12, '20200103', '20200103'),
                    ('balancesheet_vip', 'success', 18, '20210129', '20210129'),
                    ('balancesheet_vip', 'success', 21, '20220128', '20220128'),
                    ('balancesheet_vip', 'success', 9, '20230131', '20230131'),
                    ('balancesheet_vip', 'success', 24, '20260318', '20260318'),
                    ('balancesheet_vip', 'success', 0, '20260319', '20260319')
                """
            )
        )

    spec = make_job_spec(
        name="balancesheet_vip",
        table_name="stock_balancesheet_vip",
        params={"ann_date": "{current_date}"},
        scope_columns=("ann_date",),
    )

    assert resolve_sample_param_sets(spec, sqlite_engine, max_samples=3) == [
        {"ann_date": "20200103"},
        {"ann_date": "20220128"},
        {"ann_date": "20260318"},
    ]


def test_resolve_sparse_column_param_sets_uses_target_column_history(sqlite_engine):
    with sqlite_engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE stock_balancesheet_vip (
                    ann_date CHAR(8),
                    acc_exp DOUBLE,
                    deferred_inc DOUBLE
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO stock_balancesheet_vip (ann_date, acc_exp, deferred_inc)
                VALUES
                    ('20260318', NULL, NULL),
                    ('20200425', 14.0, NULL),
                    ('20200310', NULL, 577249.48)
                """
            )
        )

    spec = make_job_spec(
        name="balancesheet_vip",
        table_name="stock_balancesheet_vip",
        params={"ann_date": "{current_date}"},
        scope_columns=("ann_date",),
    )

    assert resolve_sparse_column_param_sets(
        spec,
        sqlite_engine,
        ["acc_exp", "deferred_inc"],
        max_param_sets=4,
    ) == [
        {"ann_date": "20200310"},
        {"ann_date": "20200425"},
    ]


def test_resolve_sample_params_uses_scope_column_when_requested_param_is_missing(sqlite_engine):
    with sqlite_engine.begin() as connection:
        connection.execute(text("CREATE TABLE stock_new_share (ipo_date CHAR(8), ts_code VARCHAR(16))"))
        connection.execute(
            text(
                """
                INSERT INTO stock_new_share (ipo_date, ts_code)
                VALUES ('20260305', '301000.SZ'), ('20260318', '301001.SZ')
                """
            )
        )

    spec = make_job_spec(
        name="new_share",
        table_name="stock_new_share",
        params={"start_date": "{trade_date}", "end_date": "{trade_date}"},
        scope_columns=("ipo_date",),
    )

    assert resolve_sample_params(spec, sqlite_engine) == {
        "start_date": "20260318",
        "end_date": "20260318",
    }


def test_resolve_sample_params_returns_trade_cal_range_for_infrastructure(sqlite_engine):
    with sqlite_engine.begin() as connection:
        connection.execute(text("CREATE TABLE trade_cal (exchange VARCHAR(32), cal_date CHAR(8))"))
        connection.execute(
            text(
                """
                INSERT INTO trade_cal (exchange, cal_date)
                VALUES ('SSE', '20260317'), ('SSE', '20260318')
                """
            )
        )

    spec = InfrastructureSpec(
        name="trade_cal",
        fetcher_cls=object,
        table_name="trade_cal",
        scope_columns=("exchange", "cal_date"),
        api_name="trade_cal",
        table_schema=TableSchema(columns={}),
    )

    assert resolve_sample_params(spec, sqlite_engine) == {
        "start_date": "20260218",
        "end_date": "20260318",
    }


def test_resolve_sample_params_handles_missing_stock_basic_for_pledge_detail(sqlite_engine):
    spec = make_job_spec(
        name="pledge_detail",
        table_name="stock_pledge_detail",
    )

    assert resolve_sample_params(spec, sqlite_engine) == {}


def test_resolve_sample_params_uses_existing_pledge_detail_ts_code_when_available(sqlite_engine):
    with sqlite_engine.begin() as connection:
        connection.execute(text("CREATE TABLE stock_pledge_detail (ts_code VARCHAR(16))"))
        connection.execute(
            text(
                """
                INSERT INTO stock_pledge_detail (ts_code)
                VALUES ('000001.SZ'), ('600000.SH')
                """
            )
        )

    spec = make_job_spec(
        name="pledge_detail",
        table_name="stock_pledge_detail",
    )

    assert resolve_sample_params(spec, sqlite_engine) == {"ts_code": "600000.SH"}
