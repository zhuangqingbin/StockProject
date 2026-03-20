from __future__ import annotations

import ast
import time
from datetime import date
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import text

from apps.data_hub.data_pipeline_ts.execution.context import ExecutionContext
from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema
from apps.data_hub.data_pipeline_ts.execution import (
    run_backfill,
    run_infrastructure,
    run_once,
    select_job_specs,
)
from apps.data_hub.data_pipeline_ts.jobs import catalog as catalog_module
from apps.data_hub.data_pipeline_ts.jobs.catalog import ALL_JOBS
from apps.data_hub.data_pipeline_ts.jobs.profiles import PROFILE_SPECS, ProfileId
from apps.data_hub.data_pipeline_ts.jobs.specs import (
    InfrastructureSpec,
    JobSpec,
)
from apps.data_hub.data_pipeline_ts.execution.persistence import (
    DatabaseWriter,
    build_mysql_url as build_orchestrator_mysql_url,
)


class DemoDailyFetch(BaseFetcher):
    fields = ["ts_code", "trade_date", "close"]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=False),
            "trade_date": ColumnDef("CHAR(8)", nullable=False),
            "close": ColumnDef("DOUBLE", nullable=True),
        },
        composite_indexes=[("trade_date",), ("trade_date", "ts_code")],
    )

    calls: list[dict[str, str]] = []

    def read_data(self, **kwargs):
        DemoDailyFetch.calls.append(kwargs)
        return pd.DataFrame(
            [{"ts_code": "000001.SZ", "trade_date": kwargs["trade_date"], "close": 12.3}]
        )


class DemoCalendarFetch(BaseFetcher):
    fields = ["ts_code", "ann_date", "close"]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=False),
            "ann_date": ColumnDef("CHAR(8)", nullable=False),
            "close": ColumnDef("DOUBLE", nullable=True),
        },
        composite_indexes=[("ann_date",), ("ann_date", "ts_code")],
    )

    calls: list[dict[str, str]] = []

    def read_data(self, **kwargs):
        DemoCalendarFetch.calls.append(kwargs)
        return pd.DataFrame(
            [{"ts_code": "000001.SZ", "ann_date": kwargs["ann_date"], "close": 12.3}]
        )


class DemoTradeCalFetch(BaseFetcher):
    fields = ["exchange", "cal_date", "is_open"]
    table_schema = TableSchema(
        columns={
            "exchange": ColumnDef("VARCHAR(16)", nullable=False),
            "cal_date": ColumnDef("CHAR(8)", nullable=False),
            "is_open": ColumnDef("INT", nullable=True),
        },
        composite_indexes=[("exchange", "cal_date")],
    )

    calls: list[dict[str, str]] = []

    def read_data(self, **kwargs):
        DemoTradeCalFetch.calls.append(kwargs)
        return pd.DataFrame(
            [{"exchange": "SSE", "cal_date": kwargs["start_date"], "is_open": 1}]
        )


class SerialProbeFetch(BaseFetcher):
    fields = ["ts_code", "trade_date", "close"]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=False),
            "trade_date": ColumnDef("CHAR(8)", nullable=False),
            "close": ColumnDef("DOUBLE", nullable=True),
        },
        composite_indexes=[("trade_date",), ("trade_date", "ts_code")],
    )

    active = 0
    max_active = 0

    def read_data(self, **kwargs):
        type(self).active += 1
        type(self).max_active = max(type(self).max_active, type(self).active)
        time.sleep(0.05)
        type(self).active -= 1
        return pd.DataFrame(
            [{"ts_code": "000001.SZ", "trade_date": kwargs["trade_date"], "close": 1.0}]
        )


def _context_factory(raw_as_of: str | None = None) -> ExecutionContext:
    return ExecutionContext(
        as_of_date=date(2026, 3, 17),
        trade_date=date(2026, 3, 17),
    )


def test_data_pipeline_ts_runtime_does_not_import_legacy_pipeline_modules():
    execution_source = Path(__file__).resolve().parents[1] / "execution" / "__init__.py"
    main_source = Path(__file__).resolve().parents[1] / "main.py"

    execution_text = execution_source.read_text(encoding="utf-8")
    main_text = main_source.read_text(encoding="utf-8")

    assert "apps.data_hub.pipeline" not in execution_text
    assert "apps.data_hub.hooks" not in execution_text
    assert "apps.data_hub.pipeline" not in main_text


def test_data_pipeline_ts_does_not_depend_on_models_module():
    jobs_init_source = Path(__file__).resolve().parents[1] / "jobs" / "__init__.py"
    execution_source = Path(__file__).resolve().parents[1] / "execution" / "__init__.py"
    main_source = Path(__file__).resolve().parents[1] / "main.py"

    assert "data_pipeline_ts.models" not in jobs_init_source.read_text(encoding="utf-8")
    assert "data_pipeline_ts.models" not in execution_source.read_text(encoding="utf-8")
    assert "data_pipeline_ts.models" not in main_source.read_text(encoding="utf-8")


def test_registry_imports_fetchers_by_tushare_category():
    catalog_source = Path(__file__).resolve().parents[1] / "jobs" / "catalog.py"
    registry_text = catalog_source.read_text(encoding="utf-8")

    assert "from apps.data_hub.data_pipeline_ts.fetchers import (" not in registry_text
    assert "from apps.data_hub.data_pipeline_ts.fetchers.basic_data import (" in registry_text
    assert "from apps.data_hub.data_pipeline_ts.fetchers.board_data import (" in registry_text
    assert "from apps.data_hub.data_pipeline_ts.fetchers.financial_data import (" in registry_text
    assert "from apps.data_hub.data_pipeline_ts.fetchers.margin_data import (" in registry_text
    assert "from apps.data_hub.data_pipeline_ts.fetchers.money_flow_data import (" in registry_text
    assert "from apps.data_hub.data_pipeline_ts.fetchers.reference_data import (" in registry_text
    assert "from apps.data_hub.data_pipeline_ts.fetchers.special_data import (" in registry_text
    assert "from apps.data_hub.data_pipeline_ts.fetchers.stock_market_data import (" in registry_text


def test_catalog_groups_jobs_by_fetcher_directory():
    category_groups = [
        ("basic_data", catalog_module.BASIC_DATA_JOBS),
        ("board_data", catalog_module.BOARD_DATA_JOBS),
        ("financial_data", catalog_module.FINANCIAL_DATA_JOBS),
        ("margin_data", catalog_module.MARGIN_DATA_JOBS),
        ("money_flow_data", catalog_module.MONEY_FLOW_DATA_JOBS),
        ("reference_data", catalog_module.REFERENCE_DATA_JOBS),
        ("special_data", catalog_module.SPECIAL_DATA_JOBS),
        ("stock_market_data", catalog_module.STOCK_MARKET_DATA_JOBS),
    ]

    for expected_directory, jobs in category_groups:
        assert jobs
        assert all(job.fetcher_cls.__module__.split(".")[-2] == expected_directory for job in jobs)

    assert not hasattr(catalog_module, "DAILY_JOBS")
    assert not hasattr(catalog_module, "FINANCIAL_JOBS")
    assert not hasattr(catalog_module, "REFERENCE_JOBS")
    assert not hasattr(catalog_module, "SPECIAL_JOBS")

    assert catalog_module.ALL_JOBS == [
        *catalog_module.BASIC_DATA_JOBS,
        *catalog_module.BOARD_DATA_JOBS,
        *catalog_module.FINANCIAL_DATA_JOBS,
        *catalog_module.MARGIN_DATA_JOBS,
        *catalog_module.MONEY_FLOW_DATA_JOBS,
        *catalog_module.REFERENCE_DATA_JOBS,
        *catalog_module.SPECIAL_DATA_JOBS,
        *catalog_module.STOCK_MARKET_DATA_JOBS,
    ]


def test_kpl_concept_cons_is_grouped_with_trade_day_extended_jobs():
    profiles_by_job = {job.name: job.profile for job in ALL_JOBS}

    assert profiles_by_job["kpl_concept_cons"] is ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED
    assert profiles_by_job["hm_list"] is ProfileId.MANUAL
    assert profiles_by_job["pledge_detail"] is ProfileId.MANUAL


def test_profile_specs_define_cron_execution_and_backfill_modes():
    assert PROFILE_SPECS[ProfileId.TRADE_DAY_PRE_OPEN].cron == "25 9 * * *"
    assert PROFILE_SPECS[ProfileId.TRADE_DAY_PRE_OPEN].execution_mode == "parallel"
    assert PROFILE_SPECS[ProfileId.TRADE_DAY_PRE_OPEN].backfill_mode == "trade_day"

    assert PROFILE_SPECS[ProfileId.FINANCIAL_CALENDAR_NIGHTLY].cron == "30 21 * * *"
    assert PROFILE_SPECS[ProfileId.FINANCIAL_CALENDAR_NIGHTLY].backfill_mode == "calendar_day"

    assert PROFILE_SPECS[ProfileId.MANUAL].cron is None
    assert PROFILE_SPECS[ProfileId.MANUAL].execution_mode == "serial"
    assert PROFILE_SPECS[ProfileId.MANUAL].backfill_mode == "manual"


def test_data_pipeline_ts_build_mysql_url_requires_ts_mysql_database(monkeypatch):
    monkeypatch.setenv("MYSQL_USER", "demo")
    monkeypatch.setenv("MYSQL_PASSWORD", "secret")
    monkeypatch.setenv("MYSQL_HOST", "db.local")
    monkeypatch.setenv("MYSQL_PORT", "3307")
    monkeypatch.setenv("MYSQL_CHARSET", "utf8mb4")
    monkeypatch.delenv("TS_MYSQL_DATABASE", raising=False)

    with pytest.raises(ValueError, match="TS_MYSQL_DATABASE"):
        build_orchestrator_mysql_url()


def test_daily_reference_jobs_use_source_date_scope():
    jobs_by_name = {job.name: job for job in ALL_JOBS}

    assert jobs_by_name["top10_holders"].profile is ProfileId.REFERENCE_CALENDAR_NIGHTLY
    assert jobs_by_name["top10_holders"].scope_columns == ("ann_date",)
    assert jobs_by_name["top10_holders"].params == {"ann_date": "{current_date}"}
    assert jobs_by_name["top10_floatholders"].profile is ProfileId.REFERENCE_CALENDAR_NIGHTLY
    assert jobs_by_name["top10_floatholders"].scope_columns == ("ann_date",)
    assert jobs_by_name["top10_floatholders"].params == {"ann_date": "{current_date}"}
    assert jobs_by_name["pledge_stat"].profile is ProfileId.REFERENCE_CALENDAR_NIGHTLY
    assert jobs_by_name["pledge_stat"].scope_columns == ("end_date",)
    assert jobs_by_name["pledge_stat"].params == {"end_date": "{current_date}"}
    assert jobs_by_name["pledge_detail"].profile is ProfileId.MANUAL
    assert jobs_by_name["pledge_detail"].scope_columns == ("snapshot_date",)
    assert jobs_by_name["pledge_detail"].params == {"snapshot_date": "{current_date}"}
    assert jobs_by_name["hm_list"].profile is ProfileId.MANUAL
    assert jobs_by_name["hm_list"].scope_columns == ("snapshot_date",)
    assert jobs_by_name["hm_list"].params == {"snapshot_date": "{current_date}"}


def test_financial_vip_jobs_use_ann_date_incremental_scope():
    jobs_by_name = {job.name: job for job in ALL_JOBS}

    for job_name in [
        "income_vip",
        "balancesheet_vip",
        "cashflow_vip",
        "fina_indicator_vip",
    ]:
        assert jobs_by_name[job_name].params == {"ann_date": "{current_date}"}
        assert jobs_by_name[job_name].scope_columns == ("ann_date",)


def test_registry_jobs_include_chinese_descriptions():
    jobs_by_name = {job.name: job for job in ALL_JOBS}

    assert jobs_by_name["stock_daily"].description == "股票日线行情"
    assert jobs_by_name["income_vip"].description == "利润表披露增量"
    assert jobs_by_name["pledge_detail"].description == "股票质押明细快照"
    assert jobs_by_name["hm_list"].description == "游资营业部龙虎榜快照"


def test_registry_job_definitions_use_explicit_keywords_and_api_names():
    catalog_source = Path(__file__).resolve().parents[1] / "jobs" / "catalog.py"
    tree = ast.parse(catalog_source.read_text(encoding="utf-8"))

    job_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_job"
    ]

    assert job_calls
    for call in job_calls:
        assert call.args == []
        keyword_names = [keyword.arg for keyword in call.keywords]
        assert keyword_names == [
            "name",
            "table_name",
            "fetcher_cls",
            "api_name",
            "description",
            "profile",
            "params",
            "scope_columns",
        ]


def test_registry_exposes_api_name_for_representative_jobs():
    jobs_by_name = {job.name: job for job in ALL_JOBS}

    assert jobs_by_name["stock_daily"].api_name == "daily"
    assert jobs_by_name["money_flow"].api_name == "moneyflow"
    assert jobs_by_name["money_flow_mkt_dc"].api_name == "moneyflow_mkt_dc"
    assert jobs_by_name["income_vip"].api_name == "income_vip"
    assert jobs_by_name["pledge_stat"].api_name == "pledge_stat"
    assert jobs_by_name["hm_list"].api_name == "hm_list"


def test_select_job_specs_filters_by_profile_and_job_name():
    specs = [
        JobSpec(
            name="stock_daily",
            table_name="stock_daily",
            fetcher_cls=DemoDailyFetch,
            description="测试股票日线",
            profile=ProfileId.TRADE_DAY_POST_CLOSE_CORE,
            params={"trade_date": "{trade_date}"},
            scope_columns=("trade_date",),
            table_schema=DemoDailyFetch.table_schema,
        ),
        JobSpec(
            name="stock_daily_basic",
            table_name="stock_daily_basic",
            fetcher_cls=DemoDailyFetch,
            description="测试股票日线基本指标",
            profile=ProfileId.TRADE_DAY_POST_CLOSE_CORE,
            params={"trade_date": "{trade_date}"},
            scope_columns=("trade_date",),
            table_schema=DemoDailyFetch.table_schema,
        ),
    ]

    filtered = select_job_specs(specs, job_names=["stock_daily"])
    assert [item.name for item in filtered] == ["stock_daily"]

    with pytest.raises(ValueError, match="Unknown job names"):
        select_job_specs(specs, job_names=["missing_job"])


def test_run_once_writes_rows_and_records_log(sqlite_engine):
    DemoDailyFetch.calls = []
    writer = DatabaseWriter(engine=sqlite_engine)
    specs = [
        JobSpec(
            name="stock_daily",
            table_name="stock_daily",
            fetcher_cls=DemoDailyFetch,
            description="测试股票日线",
            profile=ProfileId.TRADE_DAY_POST_CLOSE_CORE,
            params={"trade_date": "{trade_date}"},
            scope_columns=("trade_date",),
            table_schema=DemoDailyFetch.table_schema,
        )
    ]

    results = run_once(
        as_of="2026-03-17",
        job_specs=specs,
        writer=writer,
        context_factory=_context_factory,
    )

    assert [result.status for result in results] == ["success"]
    assert DemoDailyFetch.calls == [{"trade_date": "20260317"}]

    with sqlite_engine.begin() as connection:
        rows = connection.execute(text("SELECT ts_code, trade_date, close FROM stock_daily")).all()
        logs = connection.execute(text("SELECT job_name, status, rows_written FROM job_run_log")).all()

    assert rows == [("000001.SZ", "20260317", 12.3)]
    assert logs == [("stock_daily", "success", 1)]


def test_run_backfill_skips_non_trade_days(sqlite_engine):
    DemoDailyFetch.calls = []
    writer = DatabaseWriter(engine=sqlite_engine)
    specs = [
        JobSpec(
            name="stock_daily",
            table_name="stock_daily",
            fetcher_cls=DemoDailyFetch,
            description="测试股票日线",
            profile=ProfileId.TRADE_DAY_POST_CLOSE_CORE,
            params={"trade_date": "{trade_date}"},
            scope_columns=("trade_date",),
            table_schema=DemoDailyFetch.table_schema,
        )
    ]

    def fake_context_factory(raw_as_of: str | None = None) -> ExecutionContext:
        mapping = {
            "2026-03-17": date(2026, 3, 17),
            "2026-03-18": date(2026, 3, 17),
            "2026-03-19": date(2026, 3, 19),
        }
        as_of_date = date.fromisoformat(str(raw_as_of))
        return ExecutionContext(as_of_date=as_of_date, trade_date=mapping[str(raw_as_of)])

    run_backfill(
        start="20260317",
        end="20260319",
        job_specs=specs,
        writer=writer,
        context_factory=fake_context_factory,
    )

    assert DemoDailyFetch.calls == [
        {"trade_date": "20260317"},
        {"trade_date": "20260319"},
    ]


def test_run_backfill_keeps_as_of_date_jobs_on_non_trade_days(sqlite_engine):
    DemoDailyFetch.calls = []
    DemoCalendarFetch.calls = []
    writer = DatabaseWriter(engine=sqlite_engine)
    specs = [
        JobSpec(
            name="stock_daily",
            table_name="stock_daily",
            fetcher_cls=DemoDailyFetch,
            description="测试股票日线",
            profile=ProfileId.TRADE_DAY_POST_CLOSE_CORE,
            params={"trade_date": "{trade_date}"},
            scope_columns=("trade_date",),
            table_schema=DemoDailyFetch.table_schema,
        ),
        JobSpec(
            name="stock_forecast_vip",
            table_name="stock_forecast_vip",
            fetcher_cls=DemoCalendarFetch,
            description="测试财务公告",
            profile=ProfileId.FINANCIAL_CALENDAR_NIGHTLY,
            params={"ann_date": "{current_date}"},
            scope_columns=("ann_date",),
            table_schema=DemoCalendarFetch.table_schema,
        ),
    ]

    def fake_context_factory(raw_as_of: str | None = None) -> ExecutionContext:
        mapping = {
            "2026-03-17": date(2026, 3, 17),
            "2026-03-18": date(2026, 3, 17),
            "2026-03-19": date(2026, 3, 19),
        }
        as_of_date = date.fromisoformat(str(raw_as_of))
        return ExecutionContext(as_of_date=as_of_date, trade_date=mapping[str(raw_as_of)])

    run_backfill(
        start="20260317",
        end="20260319",
        job_specs=specs,
        writer=writer,
        context_factory=fake_context_factory,
    )

    assert DemoDailyFetch.calls == [
        {"trade_date": "20260317"},
        {"trade_date": "20260319"},
    ]
    assert DemoCalendarFetch.calls == [
        {"ann_date": "20260317"},
        {"ann_date": "20260318"},
        {"ann_date": "20260319"},
    ]


def test_run_infrastructure_requires_trade_cal_range(sqlite_engine):
    writer = DatabaseWriter(engine=sqlite_engine)
    targets = {
        "trade_cal": InfrastructureSpec(
            name="trade_cal",
            fetcher_cls=DemoTradeCalFetch,
            table_name="trade_cal",
            scope_columns=("exchange", "cal_date"),
            table_schema=DemoTradeCalFetch.table_schema,
        )
    }

    with pytest.raises(ValueError, match="start and end are required"):
        run_infrastructure(
            target_names=["trade_cal"],
            infrastructure_specs=targets,
            writer=writer,
        )


def test_run_infrastructure_writes_rows_and_records_job_run_log(sqlite_engine):
    DemoTradeCalFetch.calls = []
    writer = DatabaseWriter(engine=sqlite_engine)
    targets = {
        "trade_cal": InfrastructureSpec(
            name="trade_cal",
            fetcher_cls=DemoTradeCalFetch,
            table_name="trade_cal",
            scope_columns=("exchange", "cal_date"),
            table_schema=DemoTradeCalFetch.table_schema,
        )
    }

    results = run_infrastructure(
        target_names=["trade_cal"],
        start="20250101",
        end="20250131",
        infrastructure_specs=targets,
        writer=writer,
    )

    assert [result.status for result in results] == ["success"]
    assert DemoTradeCalFetch.calls == [{"start_date": "20250101", "end_date": "20250131"}]

    with sqlite_engine.begin() as connection:
        rows = connection.execute(text("SELECT exchange, cal_date, is_open FROM trade_cal")).all()
        logs = connection.execute(text("SELECT job_name, status, rows_written FROM job_run_log")).all()

    assert rows == [("SSE", "20250101", 1)]
    assert logs == [("trade_cal", "success", 1)]


def test_run_once_executes_manual_jobs_serially(sqlite_engine):
    SerialProbeFetch.active = 0
    SerialProbeFetch.max_active = 0
    writer = DatabaseWriter(engine=sqlite_engine)
    specs = [
        JobSpec(
            name="top10_holders",
            table_name="stock_top10_holders",
            fetcher_cls=SerialProbeFetch,
            description="测试手工任务一",
            profile=ProfileId.MANUAL,
            params={"trade_date": "{trade_date}"},
            scope_columns=("trade_date",),
            table_schema=SerialProbeFetch.table_schema,
        ),
        JobSpec(
            name="top10_floatholders",
            table_name="stock_top10_floatholders",
            fetcher_cls=SerialProbeFetch,
            description="测试手工任务二",
            profile=ProfileId.MANUAL,
            params={"trade_date": "{trade_date}"},
            scope_columns=("trade_date",),
            table_schema=SerialProbeFetch.table_schema,
        ),
    ]

    run_once(
        as_of="2026-03-17",
        job_specs=specs,
        writer=writer,
        context_factory=_context_factory,
        max_workers=8,
    )

    assert SerialProbeFetch.max_active == 1
