from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call, patch
import warnings

import pandas as pd
import pytest
from sqlalchemy import text

from apps.data_hub.data_pipeline_ts.fetchers import FETCHER_REGISTRY
from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher
from apps.data_hub.data_pipeline_ts.fetchers.board_data.stock_top_list import TopListFetch
from apps.data_hub.data_pipeline_ts.fetchers.board_data.stock_limit_list_d import LimitListDFetch
from apps.data_hub.data_pipeline_ts.fetchers.board_data.stock_hm_list import HMListFetch
from apps.data_hub.data_pipeline_ts.fetchers.financial_data.stock_disclosure_date import DisclosureDateFetch
from apps.data_hub.data_pipeline_ts.fetchers.financial_data.stock_income_vip import IncomeVipFetch
from apps.data_hub.data_pipeline_ts.fetchers.financial_data.stock_balancesheet_vip import BalancesheetVipFetch
from apps.data_hub.data_pipeline_ts.fetchers.financial_data.stock_cashflow_vip import CashflowVipFetch
from apps.data_hub.data_pipeline_ts.fetchers.financial_data.stock_fina_indicator_vip import FinaIndicatorVipFetch
from apps.data_hub.data_pipeline_ts.fetchers.financial_data.stock_forecast_vip import ForecastVipFetch
from apps.data_hub.data_pipeline_ts.fetchers.infrastructure import (
    StockBasicFetch,
    StockCompanyFetch,
    TradeCalFetch,
)
from apps.data_hub.data_pipeline_ts.fetchers.reference_data.stock_pledge_detail import PledgeDetailFetch
from apps.data_hub.data_pipeline_ts.fetchers.reference_data.stock_pledge_stat import PledgeStatFetch
from apps.data_hub.data_pipeline_ts.fetchers.reference_data.stock_top10_floatholders import Top10FloatHoldersFetch
from apps.data_hub.data_pipeline_ts.fetchers.reference_data.stock_top10_holders import Top10HoldersFetch
from apps.data_hub.data_pipeline_ts.fetchers.special_data.stock_report_rc import ReportRCFetch
from apps.data_hub.data_pipeline_ts.fetchers.special_data.stock_stk_factor_pro import StkFactorProFetch
from apps.data_hub.data_pipeline_ts.fetchers.stock_market_data.stock_daily import StockDailyFetch
from apps.data_hub.data_pipeline_ts.fetchers.stock_market_data.stock_hsgt_top10 import HSGTTop10Fetch
from apps.data_hub.data_pipeline_ts.fetchers.stock_market_data.stock_ggt_top10 import GGTTop10Fetch
from apps.data_hub.data_pipeline_ts.fetchers.money_flow_data.stock_money_flow_hsgt import MoneyFlowHSGTFetch
from apps.data_hub.data_pipeline_ts.fetchers.margin_data.stock_margin import MARGIN_EXCHANGE_IDS, MarginFetch
from apps.data_hub.data_pipeline_ts.fetchers.margin_data.stock_margin_secs import MARGIN_SECS_EXCHANGES, MarginSecsFetch
from apps.data_hub.data_pipeline_ts.fetchers.board_data.stock_kpl_list import KPL_LIST_TAGS, KPLListFetch
from apps.data_hub.data_pipeline_ts.fetchers.board_data.stock_top_inst import TopInstFetch
from apps.data_hub.data_pipeline_ts.fetchers.basic_data.stock_hsgt import (
    STOCK_HSGT_TYPES,
    StockHsgtFetch,
)
from apps.data_hub.data_pipeline_ts.fetchers.basic_data.stock_new_share import NewShareFetch
from apps.data_hub.data_pipeline_ts.fetchers.basic_data.stock_st import StockStFetch
from apps.data_hub.data_pipeline_ts.jobs.catalog import ALL_JOBS
from apps.data_hub.data_pipeline_ts.jobs.profiles import ProfileId


EXPECTED_JOB_FETCHERS = {
    "StockDailyFetch",
    "StockSuspendDFetch",
    "StockDailyBasicFetch",
    "MoneyFlowFetch",
    "MoneyFlowHSGTFetch",
    "MoneyFlowDCFetch",
    "MoneyFlowMktDCFetch",
    "MarginFetch",
    "MarginDetailFetch",
    "MarginSecsFetch",
    "SLBLenFetch",
    "StockHsgtFetch",
    "StockStFetch",
    "NewShareFetch",
    "TopListFetch",
    "TopInstFetch",
    "LimitListDFetch",
    "KPLListFetch",
    "StkLimitFetch",
    "HSGTTop10Fetch",
    "GGTTop10Fetch",
    "GGTDailyFetch",
    "ForecastVipFetch",
    "ExpressVipFetch",
    "DisclosureDateFetch",
    "DividendFetch",
    "FinaAuditFetch",
    "IncomeVipFetch",
    "BalancesheetVipFetch",
    "CashflowVipFetch",
    "FinaIndicatorVipFetch",
    "Top10HoldersFetch",
    "Top10FloatHoldersFetch",
    "StkHolderNumberFetch",
    "StkHolderTradeFetch",
    "PledgeStatFetch",
    "PledgeDetailFetch",
    "RepurchaseFetch",
    "ShareFloatFetch",
    "BlockTradeFetch",
    "HMListFetch",
    "KPLConceptConsFetch",
    "ReportRCFetch",
    "CyqPerfFetch",
    "CyqChipsFetch",
    "StkFactorProFetch",
    "CcassHoldFetch",
    "HKHoldFetch",
    "StkAHComparisonFetch",
    "StkSurvFetch",
}

def test_fetcher_registry_contains_all_job_fetchers():
    assert set(FETCHER_REGISTRY) == EXPECTED_JOB_FETCHERS


def test_financial_catalog_registers_dividend_and_fina_audit_like_other_financial_jobs():
    jobs_by_name = {job.name: job for job in ALL_JOBS}

    assert "dividend" in jobs_by_name
    assert "fina_audit" in jobs_by_name

    dividend_job = jobs_by_name["dividend"]
    fina_audit_job = jobs_by_name["fina_audit"]

    assert dividend_job.table_name == "stock_dividend"
    assert dividend_job.api_name == "dividend"
    assert dividend_job.params == {"ann_date": "{current_date}"}
    assert dividend_job.scope_columns == ("ann_date",)

    assert fina_audit_job.table_name == "stock_fina_audit"
    assert fina_audit_job.api_name == "fina_audit"
    assert fina_audit_job.params == {"ann_date": "{current_date}"}
    assert fina_audit_job.scope_columns == ("ann_date",)


def test_all_jobs_register_non_empty_fetch_strategies():
    assert all(job.fetch_strategies for job in ALL_JOBS)


@pytest.mark.parametrize(
    ("job_name", "fetch_strategies"),
    [
        ("dividend", ("direct",)),
        ("stock_hsgt", ("enum_fanout_type",)),
        ("kpl_list", ("enum_fanout_tag",)),
        ("limit_list_d", ("row_cap_fallback_exchange",)),
        ("margin", ("row_cap_fallback_exchange_id",)),
        ("margin_secs", ("row_cap_fallback_exchange",)),
        ("fina_audit", ("full_market_stock_code_fanout",)),
        ("pledge_detail", ("full_market_stock_code_fanout", "snapshot_column")),
        ("hm_list", ("direct", "snapshot_column")),
        ("cyq_chips", ("full_market_stock_code_fanout", "custom_rate_limit_handling")),
        ("top_list", ("direct", "post_fetch_dedup")),
    ],
)
def test_catalog_registers_fetch_strategies_for_special_jobs(job_name, fetch_strategies):
    jobs_by_name = {job.name: job for job in ALL_JOBS}

    assert jobs_by_name[job_name].fetch_strategies == fetch_strategies


def test_index_daily_job_is_not_registered():
    jobs_by_name = {job.name: job for job in ALL_JOBS}

    assert "index_daily" not in jobs_by_name


def test_removed_weekly_and_monthly_market_jobs_are_not_registered():
    jobs_by_name = {job.name: job for job in ALL_JOBS}

    assert "stock_weekly" not in jobs_by_name
    assert "stock_monthly" not in jobs_by_name
    assert "stock_weekly_qfq" not in jobs_by_name
    assert "stock_monthly_qfq" not in jobs_by_name


def test_removed_special_data_auction_jobs_are_not_registered():
    jobs_by_name = {job.name: job for job in ALL_JOBS}

    assert "stk_auction_o" not in jobs_by_name
    assert "stk_auction_c" not in jobs_by_name


def test_money_flow_mkt_dc_job_registers_like_other_money_flow_jobs():
    jobs_by_name = {job.name: job for job in ALL_JOBS}

    assert "money_flow_mkt_dc" in jobs_by_name

    job = jobs_by_name["money_flow_mkt_dc"]
    assert job.table_name == "stock_money_flow_mkt_dc"
    assert job.api_name == "moneyflow_mkt_dc"
    assert job.profile == ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED
    assert job.params == {"trade_date": "{trade_date}"}
    assert job.scope_columns == ("trade_date",)


@pytest.mark.parametrize(
    ("job_name", "table_name", "api_name", "params", "profile", "scope_columns"),
    [
        ("report_rc", "stock_report_rc", "report_rc", {"report_date": "{current_date}"}, ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, ("report_date",)),
        ("cyq_perf", "stock_cyq_perf", "cyq_perf", {"trade_date": "{trade_date}"}, ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, ("trade_date",)),
        ("cyq_chips", "stock_cyq_chips", "cyq_chips", {"trade_date": "{trade_date}"}, ProfileId.MANUAL, ("trade_date", "ts_code")),
        ("stk_factor_pro", "stock_stk_factor_pro", "stk_factor_pro", {"trade_date": "{trade_date}"}, ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, ("trade_date",)),
        ("ccass_hold", "stock_ccass_hold", "ccass_hold", {"trade_date": "{trade_date}"}, ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, ("trade_date",)),
        ("hk_hold", "stock_hk_hold", "hk_hold", {"trade_date": "{trade_date}"}, ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, ("trade_date",)),
        ("stk_ah_comparison", "stock_stk_ah_comparison", "stk_ah_comparison", {"trade_date": "{trade_date}"}, ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, ("trade_date",)),
        ("stk_surv", "stock_stk_surv", "stk_surv", {"trade_date": "{current_date}"}, ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, ("surv_date",)),
    ],
)
def test_special_data_jobs_register_as_trade_date_driven_jobs(job_name, table_name, api_name, params, profile, scope_columns):
    jobs_by_name = {job.name: job for job in ALL_JOBS}

    assert job_name in jobs_by_name

    job = jobs_by_name[job_name]
    assert job.table_name == table_name
    assert job.api_name == api_name
    assert job.profile == profile
    assert job.params == params
    assert job.scope_columns == scope_columns


@pytest.mark.parametrize(
    ("job_name", "table_name", "api_name", "params", "profile"),
    [
        ("stock_suspend_d", "stock_suspend_d", "suspend_d", {"trade_date": "{current_date}"}, ProfileId.TRADE_DAY_POST_CLOSE_CORE),
        ("stock_daily", "stock_daily", "daily", {"trade_date": "{trade_date}"}, ProfileId.MANUAL),
        ("stock_daily_basic", "stock_daily_basic", "daily_basic", {"trade_date": "{trade_date}"}, ProfileId.MANUAL),
    ],
)
def test_calendar_market_jobs_register_expected_core_jobs(job_name, table_name, api_name, params, profile):
    jobs_by_name = {job.name: job for job in ALL_JOBS}

    assert job_name in jobs_by_name

    job = jobs_by_name[job_name]
    assert job.table_name == table_name
    assert job.api_name == api_name
    assert job.profile == profile
    assert job.params == params
    assert job.scope_columns == ("trade_date",)


def test_job_fetchers_live_in_modules_named_after_table_name():
    expected_module_by_fetcher = {
        job.fetcher_cls.__name__: job.table_name
        for job in ALL_JOBS
    }

    for fetcher_name, table_name in expected_module_by_fetcher.items():
        assert FETCHER_REGISTRY[fetcher_name].__module__.split(".")[-1] == table_name


def test_infrastructure_fetchers_are_importable_but_not_in_registry():
    assert StockBasicFetch.__name__ not in FETCHER_REGISTRY
    assert StockCompanyFetch.__name__ not in FETCHER_REGISTRY
    assert TradeCalFetch.__name__ not in FETCHER_REGISTRY


def test_dataset_specific_helper_modules_have_been_removed():
    app_root = Path(__file__).resolve().parents[2]

    assert not (app_root / "common" / "stock_universe.py").exists()
    assert not (app_root / "fetchers" / "tushare" / "reference_data" / "stock_universe.py").exists()
    assert not (app_root / "fetchers" / "tushare" / "financial_data" / "report_period.py").exists()


def test_fetcher_source_files_no_longer_use_build_table_schema():
    fetcher_root = Path(__file__).resolve().parents[1] / "fetchers"

    for path in fetcher_root.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        assert "build_table_schema(" not in path.read_text(encoding="utf-8")


def test_wide_financial_fetcher_sources_no_longer_use_convert_large_varchar_columns_to_text():
    fetcher_paths = [
        Path(IncomeVipFetch.__module__.replace(".", "/") + ".py"),
        Path(BalancesheetVipFetch.__module__.replace(".", "/") + ".py"),
        Path(CashflowVipFetch.__module__.replace(".", "/") + ".py"),
        Path(FinaIndicatorVipFetch.__module__.replace(".", "/") + ".py"),
    ]

    for relative_path in fetcher_paths:
        source = (Path(__file__).resolve().parents[4] / relative_path).read_text(encoding="utf-8")
        assert "convert_large_varchar_columns_to_text(" not in source


def test_fetcher_source_files_define_table_schema_inside_class_body():
    fetcher_root = Path(__file__).resolve().parents[1] / "fetchers"

    for path in fetcher_root.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        source = path.read_text(encoding="utf-8")
        assert ".table_schema = TableSchema(" not in source


def test_all_tushare_fetchers_own_explicit_table_schema():
    tushare_fetchers = [*FETCHER_REGISTRY.values(), StockBasicFetch, StockCompanyFetch, TradeCalFetch]

    assert all("table_schema" in fetcher_cls.__dict__ for fetcher_cls in tushare_fetchers)


def test_all_tushare_fetchers_no_longer_declare_source_endpoint():
    tushare_fetchers = [*FETCHER_REGISTRY.values(), StockBasicFetch, StockCompanyFetch, TradeCalFetch]

    assert not hasattr(BaseFetcher, "source_endpoint")
    assert all("source_endpoint" not in fetcher_cls.__dict__ for fetcher_cls in tushare_fetchers)


def test_disclosure_date_schema_uses_text_for_modify_date():
    assert DisclosureDateFetch.table_schema.columns["modify_date"].dtype == "TEXT"


def test_stock_company_schema_uses_text_for_long_business_fields():
    assert StockCompanyFetch.table_schema.columns["main_business"].dtype == "TEXT"
    assert StockCompanyFetch.table_schema.columns["business_scope"].dtype == "TEXT"


def test_stk_surv_schema_uses_wide_text_columns_for_long_survey_fields():
    fetcher = FETCHER_REGISTRY["StkSurvFetch"]

    assert fetcher.table_schema.columns["rece_place"].dtype == "TEXT"
    assert fetcher.table_schema.columns["rece_mode"].dtype == "TEXT"
    assert fetcher.table_schema.columns["content"].dtype == "LONGTEXT"


def test_share_float_schema_uses_text_for_holder_name():
    fetcher = FETCHER_REGISTRY["ShareFloatFetch"]

    assert fetcher.table_schema.columns["holder_name"].dtype == "TEXT"


def test_stk_holdertrade_schema_uses_text_for_holder_name():
    fetcher = FETCHER_REGISTRY["StkHolderTradeFetch"]

    assert fetcher.table_schema.columns["holder_name"].dtype == "TEXT"


def test_stock_daily_fetch_keeps_column_order_and_schema():
    client = MagicMock()
    client.call.return_value = pd.DataFrame({"trade_date": ["20260317"], "ts_code": ["000001.SZ"], "close": [12.3]})

    fetcher = StockDailyFetch(client=client)
    result = fetcher.fetch(trade_date="20260317")

    assert list(result.columns) == fetcher.fields
    assert fetcher.table_schema.columns["trade_date"].dtype == "CHAR(8)"
    client.call.assert_called_once()
    client.call.assert_called_once_with("daily", fields=",".join(fetcher.fields), trade_date="20260317")

def test_stock_suspend_d_fetch_keeps_column_order_and_schema():
    assert "StockSuspendDFetch" in FETCHER_REGISTRY
    fetcher_cls = FETCHER_REGISTRY["StockSuspendDFetch"]
    client = MagicMock()
    client.call.return_value = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "trade_date": ["20260317"],
            "suspend_timing": ["09:43-10:13,11:08-14:55"],
            "suspend_type": ["S"],
        }
    )

    fetcher = fetcher_cls(client=client)
    result = fetcher.fetch(trade_date="20260317")

    assert list(result.columns) == fetcher.fields
    assert fetcher.table_schema.columns["suspend_timing"].dtype == "TEXT"
    assert fetcher.table_schema.columns["suspend_type"].dtype == "VARCHAR(8)"
    client.call.assert_called_once_with("suspend_d", fields=",".join(fetcher.fields), trade_date="20260317")


def test_dividend_fetch_keeps_column_order_and_schema():
    assert "DividendFetch" in FETCHER_REGISTRY
    fetcher_cls = FETCHER_REGISTRY["DividendFetch"]
    client = MagicMock()
    client.call.return_value = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "end_date": ["20241231"],
            "ann_date": ["20260317"],
            "div_proc": ["实施"],
            "stk_div": [0.1],
            "stk_bo_rate": [0.0],
            "stk_co_rate": [0.0],
            "cash_div": [0.2],
            "cash_div_tax": [0.25],
            "record_date": ["20260320"],
            "ex_date": ["20260321"],
            "pay_date": ["20260324"],
            "div_listdate": ["20260324"],
            "imp_ann_date": ["20260318"],
            "base_date": ["20241231"],
            "base_share": [1000000.0],
        }
    )

    fetcher = fetcher_cls(client=client)
    result = fetcher.fetch(ann_date="20260317")

    assert list(result.columns) == fetcher.fields
    assert fetcher.table_schema.columns["div_proc"].dtype == "VARCHAR(32)"
    assert fetcher.table_schema.columns["base_share"].dtype == "DOUBLE"
    client.call.assert_called_once_with("dividend", fields=",".join(fetcher.fields), ann_date="20260317")


def test_removed_weekly_and_monthly_market_fetchers_are_not_exported():
    assert "StockWeeklyFetch" not in FETCHER_REGISTRY
    assert "StockMonthlyFetch" not in FETCHER_REGISTRY
    assert "StockWeeklyQfqFetch" not in FETCHER_REGISTRY
    assert "StockMonthlyQfqFetch" not in FETCHER_REGISTRY


def test_report_rc_fetch_passes_kwargs_directly():
    assert "ReportRCFetch" in FETCHER_REGISTRY
    fetcher_cls = FETCHER_REGISTRY["ReportRCFetch"]
    client = MagicMock()
    client.call.return_value = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "name": ["平安银行"],
            "report_date": ["20260318"],
            "report_title": ["盈利预测更新"],
            "report_type": ["公司研究"],
            "classify": ["一般报告"],
            "org_name": ["测试券商"],
            "author_name": ["分析师甲"],
            "quarter": ["2026Q4"],
            "op_rt": [100.0],
            "op_pr": [80.0],
            "tp": [85.0],
            "np": [70.0],
            "eps": [1.2],
            "pe": [10.0],
            "rd": [2.0],
            "roe": [12.5],
            "ev_ebitda": [8.5],
            "rating": ["买入"],
            "max_price": [18.0],
            "min_price": [15.0],
            "imp_dg": ["高"],
            "create_time": ["2026-03-18 20:15:00"],
        }
    )

    fetcher = fetcher_cls(client=client)
    result = fetcher.fetch(trade_date="20260318")

    assert list(result.columns) == fetcher.fields
    assert fetcher.table_schema.columns["report_date"].dtype == "CHAR(8)"
    assert fetcher.table_schema.columns["create_time"].dtype == "DATETIME"
    client.call.assert_called_once_with(
        "report_rc",
        fields=",".join(fetcher.fields),
        trade_date="20260318",
    )


def test_report_rc_fetch_accepts_direct_report_date():
    assert "ReportRCFetch" in FETCHER_REGISTRY
    fetcher_cls = FETCHER_REGISTRY["ReportRCFetch"]
    client = MagicMock()
    client.call.return_value = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "name": ["平安银行"],
            "report_date": ["20260318"],
            "report_title": ["盈利预测更新"],
            "report_type": ["公司研究"],
            "classify": ["一般报告"],
            "org_name": ["测试券商"],
            "author_name": ["分析师甲"],
            "quarter": ["2026Q4"],
            "op_rt": [100.0],
            "op_pr": [80.0],
            "tp": [85.0],
            "np": [70.0],
            "eps": [1.2],
            "pe": [10.0],
            "rd": [2.0],
            "roe": [12.5],
            "ev_ebitda": [8.5],
            "rating": ["买入"],
            "max_price": [18.0],
            "min_price": [15.0],
            "imp_dg": ["高"],
            "create_time": ["2026-03-18 20:15:00"],
        }
    )

    fetcher = fetcher_cls(client=client)
    result = fetcher.fetch(report_date="20260318")

    assert list(result.columns) == fetcher.fields
    client.call.assert_called_once_with(
        "report_rc",
        fields=",".join(fetcher.fields),
        report_date="20260318",
    )


def test_report_rc_fetch_uses_rate_limited_default_client_config():
    fetcher = ReportRCFetch()

    assert fetcher.client.config.max_calls_per_minute == 2


def test_report_rc_fetch_reuses_shared_default_client():
    first = ReportRCFetch()
    second = ReportRCFetch()

    assert first.client is second.client


def test_special_data_holding_fetchers_use_bigint_for_large_share_counts():
    assert FETCHER_REGISTRY["CcassHoldFetch"].table_schema.columns["shareholding"].dtype == "BIGINT"
    assert FETCHER_REGISTRY["HKHoldFetch"].table_schema.columns["vol"].dtype == "BIGINT"


def test_ccass_hold_schema_uses_text_for_long_security_names():
    assert FETCHER_REGISTRY["CcassHoldFetch"].table_schema.columns["name"].dtype == "TEXT"


def test_hk_hold_schema_uses_text_for_long_security_names():
    assert FETCHER_REGISTRY["HKHoldFetch"].table_schema.columns["name"].dtype == "TEXT"


def test_cyq_chips_fetch_fans_out_by_stock_codes_for_trade_date_runs():
    assert "CyqChipsFetch" in FETCHER_REGISTRY
    fetcher_cls = FETCHER_REGISTRY["CyqChipsFetch"]
    client = MagicMock()
    client.call.side_effect = [
        pd.DataFrame({"ts_code": ["000001.SZ", "000002.SZ", "000001.SZ"]}),
        pd.DataFrame(columns=["ts_code"]),
        pd.DataFrame(columns=["ts_code"]),
        pd.DataFrame(
            {
                "ts_code": ["000001.SZ", "000001.SZ"],
                "trade_date": ["20260318", "20260318"],
                "price": [12.31, 12.30],
                "percent": [0.31, 0.28],
            }
        ),
        pd.DataFrame(columns=["ts_code", "trade_date", "price", "percent"]),
    ]

    fetcher = fetcher_cls(client=client)
    result = fetcher.fetch(trade_date="20260318")

    assert list(result.columns) == fetcher.fields
    assert result["ts_code"].tolist() == ["000001.SZ", "000001.SZ"]
    assert client.call.call_args_list == [
        call("stock_basic", exchange="", list_status="L", fields="ts_code"),
        call("stock_basic", exchange="", list_status="D", fields="ts_code"),
        call("stock_basic", exchange="", list_status="P", fields="ts_code"),
        call("cyq_chips", ts_code="000001.SZ", fields=",".join(fetcher.fields), start_date="20260318", end_date="20260318"),
        call("cyq_chips", ts_code="000002.SZ", fields=",".join(fetcher.fields), start_date="20260318", end_date="20260318"),
    ]


def test_cyq_chips_fetch_uses_explicit_stock_codes_without_stock_basic_fanout():
    assert "CyqChipsFetch" in FETCHER_REGISTRY
    fetcher_cls = FETCHER_REGISTRY["CyqChipsFetch"]
    client = MagicMock()
    client.call.return_value = pd.DataFrame(
        {
            "ts_code": ["600000.SH"],
            "trade_date": ["20260318"],
            "price": [10.12],
            "percent": [0.45],
        }
    )

    fetcher = fetcher_cls(client=client)
    result = fetcher.fetch(stock_codes=["600000.SH"], trade_date="20260318")

    assert list(result.columns) == fetcher.fields
    client.call.assert_called_once_with(
        "cyq_chips",
        ts_code="600000.SH",
        fields=",".join(fetcher.fields),
        start_date="20260318",
        end_date="20260318",
    )


def test_cyq_chips_fetch_normalizes_single_boundary_dates():
    fetcher_cls = FETCHER_REGISTRY["CyqChipsFetch"]
    client = MagicMock()
    client.call.return_value = pd.DataFrame(
        {
            "ts_code": ["600000.SH"],
            "trade_date": ["20260318"],
            "price": [10.12],
            "percent": [0.45],
        }
    )

    fetcher = fetcher_cls(client=client)
    result = fetcher.fetch(stock_codes=["600000.SH"], start_date="20260318")

    assert list(result.columns) == fetcher.fields
    client.call.assert_called_once_with(
        "cyq_chips",
        ts_code="600000.SH",
        fields=",".join(fetcher.fields),
        start_date="20260318",
        end_date="20260318",
    )


def test_cyq_chips_fetch_retries_transient_single_stock_failures():
    fetcher_cls = FETCHER_REGISTRY["CyqChipsFetch"]
    client = MagicMock()
    client.call.side_effect = [
        pd.DataFrame({"ts_code": ["000001.SZ", "000002.SZ"]}),
        pd.DataFrame(columns=["ts_code"]),
        pd.DataFrame(columns=["ts_code"]),
        RuntimeError("TuShare call failed: cyq_chips"),
        pd.DataFrame(
            {
                "ts_code": ["000001.SZ"],
                "trade_date": ["20260318"],
                "price": [10.12],
                "percent": [0.45],
            }
        ),
        pd.DataFrame(columns=["ts_code", "trade_date", "price", "percent"]),
    ]

    fetcher = fetcher_cls(client=client)
    result = fetcher.fetch(trade_date="20260318")

    assert list(result.columns) == fetcher.fields
    assert result["ts_code"].tolist() == ["000001.SZ"]
    assert client.call.call_args_list == [
        call("stock_basic", exchange="", list_status="L", fields="ts_code"),
        call("stock_basic", exchange="", list_status="D", fields="ts_code"),
        call("stock_basic", exchange="", list_status="P", fields="ts_code"),
        call("cyq_chips", ts_code="000001.SZ", fields=",".join(fetcher.fields), start_date="20260318", end_date="20260318"),
        call("cyq_chips", ts_code="000001.SZ", fields=",".join(fetcher.fields), start_date="20260318", end_date="20260318"),
        call("cyq_chips", ts_code="000002.SZ", fields=",".join(fetcher.fields), start_date="20260318", end_date="20260318"),
    ]


def test_cyq_chips_fetch_treats_no_data_errors_as_empty_results():
    fetcher_cls = FETCHER_REGISTRY["CyqChipsFetch"]
    client = MagicMock()

    def call_side_effect(endpoint: str, **kwargs: object) -> pd.DataFrame:
        assert endpoint == "cyq_chips"
        if kwargs["ts_code"] == "000023.SZ":
            error = RuntimeError("TuShare call failed: cyq_chips")
            error.__cause__ = Exception("指定数据不存在，请确认参数！")
            raise error
        return pd.DataFrame(
            {
                "ts_code": ["000001.SZ"],
                "trade_date": ["20260318"],
                "price": [10.12],
                "percent": [0.45],
            }
        )

    client.call.side_effect = call_side_effect

    fetcher = fetcher_cls(client=client)
    result = fetcher.fetch(stock_codes=["000023.SZ", "000001.SZ"], trade_date="20260318")

    assert list(result.columns) == fetcher.fields
    assert result["ts_code"].tolist() == ["000001.SZ"]
    assert client.call.call_args_list == [
        call("cyq_chips", ts_code="000023.SZ", fields=",".join(fetcher.fields), start_date="20260318", end_date="20260318"),
        call("cyq_chips", ts_code="000001.SZ", fields=",".join(fetcher.fields), start_date="20260318", end_date="20260318"),
    ]


def test_cyq_chips_fetch_waits_and_retries_after_rate_limit_errors():
    fetcher_cls = FETCHER_REGISTRY["CyqChipsFetch"]
    client = MagicMock()
    rate_limit_error = RuntimeError("TuShare call failed: cyq_chips")
    rate_limit_error.__cause__ = Exception("抱歉，您每分钟最多访问该接口200次，权限的具体详情访问：https://tushare.pro/document/1?doc_id=108。")
    client.call.side_effect = [
        rate_limit_error,
        pd.DataFrame(
            {
                "ts_code": ["600793.SH"],
                "trade_date": ["20260318"],
                "price": [10.12],
                "percent": [0.45],
            }
        ),
    ]

    fetcher = fetcher_cls(client=client)
    with patch("apps.data_hub.data_pipeline_ts.fetchers.special_data.stock_cyq_chips.time.sleep") as sleep_mock:
        result = fetcher.fetch(stock_codes=["600793.SH"], trade_date="20260318")

    assert list(result.columns) == fetcher.fields
    assert result["ts_code"].tolist() == ["600793.SH"]
    sleep_mock.assert_called_once_with(60.0)
    assert client.call.call_args_list == [
        call("cyq_chips", ts_code="600793.SH", fields=",".join(fetcher.fields), start_date="20260318", end_date="20260318"),
        call("cyq_chips", ts_code="600793.SH", fields=",".join(fetcher.fields), start_date="20260318", end_date="20260318"),
    ]


def test_cyq_chips_fetch_rejects_single_ts_code_argument():
    fetcher_cls = FETCHER_REGISTRY["CyqChipsFetch"]
    client = MagicMock()
    fetcher = fetcher_cls(client=client)

    with pytest.raises(ValueError, match="cyq_chips fetches require stock_codes"):
        fetcher.fetch(ts_code="600000.SH", trade_date="20260318")

    client.call.assert_not_called()


def test_fina_audit_fetch_fans_out_by_stock_codes_for_scheduled_ann_date_runs():
    assert "FinaAuditFetch" in FETCHER_REGISTRY
    fetcher_cls = FETCHER_REGISTRY["FinaAuditFetch"]
    client = MagicMock()
    client.call.side_effect = [
        pd.DataFrame({"ts_code": ["000001.SZ", "000002.SZ", "000001.SZ"]}),
        pd.DataFrame(
            {
                "ts_code": ["000001.SZ"],
                "ann_date": ["20260317"],
                "end_date": ["20241231"],
                "audit_result": ["标准无保留意见"],
                "audit_fees": [1200000.0],
                "audit_agency": ["会计师事务所A"],
                "audit_sign": ["签字会计师甲"],
            }
        ),
        pd.DataFrame(
            columns=[
                "ts_code",
                "ann_date",
                "end_date",
                "audit_result",
                "audit_fees",
                "audit_agency",
                "audit_sign",
            ]
        ),
    ]

    fetcher = fetcher_cls(client=client)
    result = fetcher.fetch(ann_date="20260317")

    assert list(result.columns) == fetcher.fields
    assert result.to_dict("records") == [
        {
            "ts_code": "000001.SZ",
            "ann_date": "20260317",
            "end_date": "20241231",
            "audit_result": "标准无保留意见",
            "audit_fees": 1200000.0,
            "audit_agency": "会计师事务所A",
            "audit_sign": "签字会计师甲",
        }
    ]
    assert fetcher.table_schema.columns["audit_fees"].dtype == "DOUBLE"
    assert fetcher.table_schema.columns["audit_result"].dtype == "VARCHAR(64)"
    assert client.call.call_args_list == [
        call("stock_basic", exchange="", list_status="L", fields="ts_code"),
        call("fina_audit", ts_code="000001.SZ", fields=",".join(fetcher.fields), ann_date="20260317"),
        call("fina_audit", ts_code="000002.SZ", fields=",".join(fetcher.fields), ann_date="20260317"),
    ]


def test_fina_audit_fetch_uses_explicit_stock_codes_without_stock_basic_fanout():
    assert "FinaAuditFetch" in FETCHER_REGISTRY
    fetcher_cls = FETCHER_REGISTRY["FinaAuditFetch"]
    client = MagicMock()
    client.call.return_value = pd.DataFrame(
        {
            "ts_code": ["600000.SH"],
            "ann_date": ["20260317"],
            "end_date": ["20241231"],
            "audit_result": ["标准无保留意见"],
            "audit_fees": [890000.0],
            "audit_agency": ["会计师事务所B"],
            "audit_sign": ["签字会计师乙"],
        }
    )

    fetcher = fetcher_cls(client=client)
    result = fetcher.fetch(stock_codes=["600000.SH"], ann_date="20260317")

    assert list(result.columns) == fetcher.fields
    client.call.assert_called_once_with(
        "fina_audit",
        ts_code="600000.SH",
        fields=",".join(fetcher.fields),
        ann_date="20260317",
    )


def test_fina_audit_fetch_rejects_single_ts_code_argument():
    assert "FinaAuditFetch" in FETCHER_REGISTRY
    fetcher_cls = FETCHER_REGISTRY["FinaAuditFetch"]
    client = MagicMock()
    fetcher = fetcher_cls(client=client)

    with pytest.raises(ValueError, match="fina_audit fetches require stock_codes"):
        fetcher.fetch(ts_code="600000.SH", ann_date="20260317")

    client.call.assert_not_called()


def test_fina_audit_fetch_requires_ann_date():
    assert "FinaAuditFetch" in FETCHER_REGISTRY
    fetcher_cls = FETCHER_REGISTRY["FinaAuditFetch"]
    client = MagicMock()
    fetcher = fetcher_cls(client=client)

    with pytest.raises(ValueError, match="fina_audit fetches require ann_date or start_date/end_date"):
        fetcher.fetch(stock_codes=["600000.SH"])

    client.call.assert_not_called()


def test_fina_audit_fetch_accepts_start_end_date_ranges_without_ann_date():
    assert "FinaAuditFetch" in FETCHER_REGISTRY
    fetcher_cls = FETCHER_REGISTRY["FinaAuditFetch"]
    client = MagicMock()
    client.call.return_value = pd.DataFrame(
        {
            "ts_code": ["600000.SH"],
            "ann_date": ["20260317"],
            "end_date": ["20241231"],
            "audit_result": ["标准无保留意见"],
            "audit_fees": [890000.0],
            "audit_agency": ["会计师事务所B"],
            "audit_sign": ["签字会计师乙"],
        }
    )

    fetcher = fetcher_cls(client=client)
    result = fetcher.fetch(
        stock_codes=["600000.SH"],
        start_date="20260301",
        end_date="20260331",
    )

    assert list(result.columns) == fetcher.fields
    client.call.assert_called_once_with(
        "fina_audit",
        ts_code="600000.SH",
        fields=",".join(fetcher.fields),
        start_date="20260301",
        end_date="20260331",
    )


def test_stock_hsgt_fetch_fans_out_by_default_types():
    client = MagicMock()
    client.call.side_effect = [
        pd.DataFrame({"ts_code": [f"00000{index}.SZ"], "trade_date": ["20260317"], "type": [type_value], "name": ["x"], "type_name": ["y"]})
        for index, type_value in enumerate(STOCK_HSGT_TYPES, start=1)
    ]

    fetcher = StockHsgtFetch(client=client)
    result = fetcher.fetch(trade_date="20260317")

    assert set(result["type"]) == set(STOCK_HSGT_TYPES)
    assert client.call.call_args_list == [
        call(
            "stock_hsgt",
            type=type_value,
            trade_date="20260317",
            fields=",".join(fetcher.fields),
        )
        for type_value in STOCK_HSGT_TYPES
    ]


def test_kpl_list_fetch_fans_out_by_default_tags():
    client = MagicMock()
    client.call.side_effect = [
        pd.DataFrame(
            {
                "trade_date": ["20260317"],
                "ts_code": [f"00000{index}.SZ"],
                "name": ["name"],
                "close": [12.3],
                "pct_chg": [1.2],
                "volume": [100],
                "amount": [200],
                "turnover_rate": [1.0],
                "lu_desc": ["desc"],
                "tag": [tag],
                "theme": ["theme"],
                "status": ["status"],
                "limit_order": [1],
                "limit_amount": [2],
            }
        )
        for index, tag in enumerate(KPL_LIST_TAGS, start=1)
    ]

    fetcher = KPLListFetch(client=client)
    result = fetcher.fetch(trade_date="20260317")

    assert set(result["tag"]) == set(KPL_LIST_TAGS)
    assert client.call.call_args_list == [
        call(
            "kpl_list",
            tag=tag,
            trade_date="20260317",
            fields=",".join(fetcher.fields),
        )
        for tag in KPL_LIST_TAGS
    ]


def test_kpl_list_fetch_uses_rate_limited_default_client_config():
    fetcher = KPLListFetch()

    assert fetcher.client.config.min_interval_seconds == 0.35
    assert fetcher.client.config.max_calls_per_minute == 190


def test_kpl_list_fetch_waits_and_retries_after_rate_limit_errors():
    client = MagicMock()
    rate_limit_error = RuntimeError("TuShare call failed: kpl_list")
    rate_limit_error.__cause__ = Exception("抱歉，您每分钟最多访问该接口200次，权限的具体详情访问：https://tushare.pro/document/1?doc_id=108。")
    client.call.side_effect = [
        rate_limit_error,
        *[
            pd.DataFrame(
                {
                    "trade_date": ["20260317"],
                    "ts_code": [f"00000{index}.SZ"],
                    "name": ["name"],
                    "lu_time": [None],
                    "ld_time": [None],
                    "open_time": [None],
                    "last_time": [None],
                    "lu_desc": ["desc"],
                    "tag": [tag],
                    "theme": ["theme"],
                    "net_change": [1.0],
                    "bid_amount": [2.0],
                    "status": ["status"],
                    "bid_change": [3.0],
                    "bid_turnover": [4.0],
                    "lu_bid_vol": [5.0],
                    "pct_chg": [6.0],
                    "bid_pct_chg": [7.0],
                    "rt_pct_chg": [8.0],
                    "limit_order": [9.0],
                    "amount": [10.0],
                    "turnover_rate": [11.0],
                    "free_float": [12.0],
                    "lu_limit_order": [13.0],
                }
            )
            for index, tag in enumerate(KPL_LIST_TAGS, start=1)
        ],
    ]

    fetcher = KPLListFetch(client=client)
    with patch("apps.data_hub.data_pipeline_ts.fetchers.board_data.stock_kpl_list.time.sleep") as sleep_mock:
        result = fetcher.fetch(trade_date="20260317")

    assert set(result["tag"]) == set(KPL_LIST_TAGS)
    sleep_mock.assert_called_once_with(60.0)
    assert client.call.call_args_list == [
        call(
            "kpl_list",
            tag=KPL_LIST_TAGS[0],
            trade_date="20260317",
            fields=",".join(fetcher.fields),
        ),
        call(
            "kpl_list",
            tag=KPL_LIST_TAGS[0],
            trade_date="20260317",
            fields=",".join(fetcher.fields),
        ),
        *[
            call(
                "kpl_list",
                tag=tag,
                trade_date="20260317",
                fields=",".join(fetcher.fields),
            )
            for tag in KPL_LIST_TAGS[1:]
        ],
    ]


def test_kpl_list_fetch_supports_start_end_date_range_once():
    client = MagicMock()
    client.call.side_effect = [
        pd.DataFrame(
            {
                "trade_date": ["20191231"],
                "ts_code": [f"00000{index}.SZ"],
                "name": ["name"],
                "lu_time": [None],
                "ld_time": [None],
                "open_time": [None],
                "last_time": [None],
                "lu_desc": ["desc"],
                "tag": [tag],
                "theme": ["theme"],
                "net_change": [1.0],
                "bid_amount": [2.0],
                "status": ["status"],
                "bid_change": [3.0],
                "bid_turnover": [4.0],
                "lu_bid_vol": [5.0],
                "pct_chg": [6.0],
                "bid_pct_chg": [7.0],
                "rt_pct_chg": [8.0],
                "limit_order": [9.0],
                "amount": [10.0],
                "turnover_rate": [11.0],
                "free_float": [12.0],
                "lu_limit_order": [13.0],
            }
        )
        for index, tag in enumerate(KPL_LIST_TAGS, start=1)
    ]

    fetcher = KPLListFetch(client=client)
    result = fetcher.fetch(start_date="20171201", end_date="20200101")

    assert set(result["tag"]) == set(KPL_LIST_TAGS)
    assert client.call.call_args_list == [
        call(
            "kpl_list",
            tag=tag,
            start_date="20171201",
            end_date="20200101",
            fields=",".join(fetcher.fields),
        )
        for tag in KPL_LIST_TAGS
    ]


def test_kpl_list_fetch_avoids_futurewarning_when_concatenating_sparse_frames():
    client = MagicMock()
    client.call.side_effect = [
        pd.DataFrame(
            [
                {
                    "ts_code": "002902.SZ",
                    "name": "铭普光磁",
                    "trade_date": "20260319",
                    "lu_time": "14:09:06",
                    "ld_time": None,
                    "open_time": None,
                    "last_time": "14:09:06",
                    "lu_desc": "通信",
                    "tag": "涨停",
                    "theme": "光模块、通信",
                    "net_change": 201739621.0,
                    "bid_amount": None,
                    "status": "首板",
                    "bid_change": None,
                    "bid_turnover": None,
                    "lu_bid_vol": None,
                    "pct_chg": None,
                    "bid_pct_chg": None,
                    "rt_pct_chg": None,
                    "limit_order": 167333232.0,
                    "amount": 913343902.0,
                    "turnover_rate": 25.02,
                    "free_float": 3798898747.0,
                    "lu_limit_order": 710513408.0,
                }
            ]
        ),
        pd.DataFrame(
            [
                {
                    "ts_code": "000001.SZ",
                    "name": "样例",
                    "trade_date": "20260319",
                    "lu_time": None,
                    "ld_time": None,
                    "open_time": None,
                    "last_time": None,
                    "lu_desc": None,
                    "tag": "炸板",
                    "theme": "题材",
                    "net_change": None,
                    "bid_amount": 1.0,
                    "status": "首板",
                    "bid_change": 2.0,
                    "bid_turnover": 3.0,
                    "lu_bid_vol": 4.0,
                    "pct_chg": 5.0,
                    "bid_pct_chg": 6.0,
                    "rt_pct_chg": 7.0,
                    "limit_order": 8.0,
                    "amount": 9.0,
                    "turnover_rate": 10.0,
                    "free_float": 11.0,
                    "lu_limit_order": 12.0,
                }
            ]
        ),
        pd.DataFrame(columns=KPLListFetch.fields),
        pd.DataFrame(columns=KPLListFetch.fields),
        pd.DataFrame(columns=KPLListFetch.fields),
    ]

    fetcher = KPLListFetch(client=client)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = fetcher.fetch(trade_date="20260319")

    assert len(result.index) == 2
    assert not [warning for warning in caught if isinstance(warning.message, FutureWarning)]


@pytest.mark.parametrize(
    ("fetcher_cls", "message"),
    [
        (StockHsgtFetch, "stock_hsgt fetches require trade_date"),
        (KPLListFetch, "kpl_list fetches require trade_date or start_date/end_date"),
    ],
)
def test_trade_date_only_fetchers_require_trade_date(fetcher_cls, message):
    client = MagicMock()
    fetcher = fetcher_cls(client=client)

    with pytest.raises(ValueError, match=message):
        fetcher.fetch()

    client.call.assert_not_called()


def test_top_list_fetch_deduplicates_duplicate_primary_key_rows():
    duplicate_rows = pd.DataFrame(
        [
            {
                "trade_date": "20260317",
                "ts_code": "600307.SH",
                "name": "酒钢宏兴",
                "close": 2.2,
                "pct_change": 10.0,
                "turnover_rate": 3.21,
                "amount": 434805828.0,
                "l_sell": None,
                "l_buy": 218524761.0,
                "l_amount": 218524761.0,
                "net_amount": 218524761.0,
                "net_rate": 50.26,
                "amount_rate": 50.26,
                "float_values": 13779386332.8,
                "reason": "单只标的证券的当日融资买入数量达到当日该证券总交易量的50％以上",
            },
            {
                "trade_date": "20260317",
                "ts_code": "600307.SH",
                "name": "酒钢宏兴",
                "close": 2.2,
                "pct_change": 10.0,
                "turnover_rate": 3.21,
                "amount": 434805828.0,
                "l_sell": None,
                "l_buy": 218524761.0,
                "l_amount": 218524761.0,
                "net_amount": 218524761.0,
                "net_rate": 50.26,
                "amount_rate": 50.26,
                "float_values": 13779386332.8,
                "reason": "单只标的证券的当日融资买入数量达到当日该证券总交易量的50％以上",
            },
        ]
    )
    client = MagicMock()
    client.call.return_value = duplicate_rows

    fetcher = TopListFetch(client=client)
    result = fetcher.fetch(trade_date="20260317")

    assert len(result) == 1
    assert result.iloc[0]["ts_code"] == "600307.SH"
    client.call.assert_called_once_with("top_list", fields=",".join(fetcher.fields), trade_date="20260317")


def test_forecast_vip_fetch_uses_text_columns_for_long_reason_fields():
    assert ForecastVipFetch.table_schema.columns["summary"].dtype == "TEXT"
    assert ForecastVipFetch.table_schema.columns["change_reason"].dtype == "TEXT"


def test_real_sample_schema_calibration_targets_are_committed():
    assert MoneyFlowHSGTFetch.table_schema.columns["hgt"].dtype == "DOUBLE"
    assert FETCHER_REGISTRY["MoneyFlowMktDCFetch"].table_schema.columns["net_amount"].dtype == "DOUBLE"
    assert MarginFetch.table_schema.columns["rzye"].dtype == "DOUBLE"
    assert NewShareFetch.table_schema.columns["ballot"].dtype == "DOUBLE"
    assert TopListFetch.table_schema.columns["reason"].dtype == "TEXT"
    assert TopInstFetch.table_schema.columns["side"].dtype == "TINYINT"
    assert TopInstFetch.table_schema.columns["reason"].dtype == "TEXT"
    assert KPLListFetch.table_schema.columns["lu_desc"].dtype == "TEXT"
    assert HSGTTop10Fetch.table_schema.columns["rank"].dtype == "INT"
    assert HSGTTop10Fetch.table_schema.columns["market_type"].dtype == "VARCHAR(8)"
    assert GGTTop10Fetch.table_schema.columns["rank"].dtype == "INT"
    assert GGTTop10Fetch.table_schema.columns["market_type"].dtype == "VARCHAR(8)"
    assert ForecastVipFetch.table_schema.columns["last_parent_net"].dtype == "DOUBLE"
    assert IncomeVipFetch.table_schema.columns["report_type"].dtype == "VARCHAR(8)"
    assert IncomeVipFetch.table_schema.columns["diluted_eps"].dtype == "DOUBLE"
    assert BalancesheetVipFetch.table_schema.columns["div_receiv"].dtype == "DOUBLE"
    assert BalancesheetVipFetch.table_schema.columns["lending_funds"].dtype == "DOUBLE"
    assert BalancesheetVipFetch.table_schema.columns["acc_exp"].dtype == "DOUBLE"
    assert BalancesheetVipFetch.table_schema.columns["deferred_inc"].dtype == "DOUBLE"
    assert CashflowVipFetch.table_schema.columns["invest_loss"].dtype == "DOUBLE"
    assert FinaIndicatorVipFetch.table_schema.columns["salescash_to_or"].dtype == "DOUBLE"
    assert PledgeStatFetch.table_schema.columns["rest_pledge"].dtype == "DOUBLE"
    assert StockCompanyFetch.table_schema.columns["email"].dtype == "VARCHAR(128)"
    assert StockCompanyFetch.table_schema.columns["employees"].dtype == "INT"


def test_limit_list_d_fetch_uses_text_column_for_limit_state():
    assert LimitListDFetch.table_schema.columns["limit"].dtype == "VARCHAR(16)"


def test_margin_fetch_uses_single_request_when_result_is_below_row_cap():
    client = MagicMock()
    client.call.return_value = pd.DataFrame(
        {
            "trade_date": ["20260317", "20260317", "20260317"],
            "exchange_id": ["SSE", "SZSE", "BSE"],
            "rzye": [1.0, 2.0, 3.0],
            "rzmre": [4.0, 5.0, 6.0],
            "rzche": [7.0, 8.0, 9.0],
            "rqye": [10.0, 11.0, 12.0],
            "rqmcl": [13.0, 14.0, 15.0],
            "rzrqye": [16.0, 17.0, 18.0],
            "rqyl": [19.0, 20.0, 21.0],
        }
    )

    fetcher = MarginFetch(client=client)
    result = fetcher.fetch(trade_date="20260317")

    assert list(result.columns) == fetcher.fields
    assert result["exchange_id"].tolist() == ["SSE", "SZSE", "BSE"]
    client.call.assert_called_once_with(
        "margin",
        fields=",".join(fetcher.fields),
        trade_date="20260317",
    )


def test_margin_fetch_falls_back_to_exchange_fanout_at_row_cap():
    client = MagicMock()
    capped_frame = pd.DataFrame(
        {
            "trade_date": ["20260317"] * 4000,
            "exchange_id": ["SSE"] * 4000,
            "rzye": [1.0] * 4000,
            "rzmre": [2.0] * 4000,
            "rzche": [3.0] * 4000,
            "rqye": [4.0] * 4000,
            "rqmcl": [5.0] * 4000,
            "rzrqye": [6.0] * 4000,
            "rqyl": [7.0] * 4000,
        }
    )
    sse_frame = pd.DataFrame(
        {
            "trade_date": ["20260317"],
            "exchange_id": ["SSE"],
            "rzye": [1.0],
            "rzmre": [2.0],
            "rzche": [3.0],
            "rqye": [4.0],
            "rqmcl": [5.0],
            "rzrqye": [6.0],
            "rqyl": [7.0],
        }
    )
    szse_frame = pd.DataFrame(
        {
            "trade_date": ["20260317"],
            "exchange_id": ["SZSE"],
            "rzye": [8.0],
            "rzmre": [9.0],
            "rzche": [10.0],
            "rqye": [11.0],
            "rqmcl": [12.0],
            "rzrqye": [13.0],
            "rqyl": [14.0],
        }
    )
    bse_frame = pd.DataFrame(
        {
            "trade_date": ["20260317"],
            "exchange_id": ["BSE"],
            "rzye": [15.0],
            "rzmre": [16.0],
            "rzche": [17.0],
            "rqye": [18.0],
            "rqmcl": [19.0],
            "rzrqye": [20.0],
            "rqyl": [21.0],
        }
    )
    client.call.side_effect = [capped_frame, sse_frame, szse_frame, bse_frame]

    fetcher = MarginFetch(client=client)
    result = fetcher.fetch(trade_date="20260317")

    assert list(result.columns) == fetcher.fields
    assert result["exchange_id"].tolist() == list(MARGIN_EXCHANGE_IDS)
    assert client.call.call_args_list == [
        call("margin", fields=",".join(fetcher.fields), trade_date="20260317"),
        call("margin", fields=",".join(fetcher.fields), exchange_id="SSE", trade_date="20260317"),
        call("margin", fields=",".join(fetcher.fields), exchange_id="SZSE", trade_date="20260317"),
        call("margin", fields=",".join(fetcher.fields), exchange_id="BSE", trade_date="20260317"),
    ]


def test_margin_secs_fetch_uses_single_request_when_result_is_below_row_cap():
    client = MagicMock()
    client.call.return_value = pd.DataFrame(
        {
            "trade_date": ["20260317", "20260317", "20260317"],
            "ts_code": ["600000.SH", "000001.SZ", "430001.BJ"],
            "name": ["浦发银行", "平安银行", "北证样例"],
            "exchange": ["SSE", "SZSE", "BSE"],
        }
    )

    fetcher = MarginSecsFetch(client=client)
    result = fetcher.fetch(trade_date="20260317")

    assert list(result.columns) == fetcher.fields
    assert result["exchange"].tolist() == list(MARGIN_SECS_EXCHANGES)
    client.call.assert_called_once_with(
        "margin_secs",
        fields=",".join(fetcher.fields),
        trade_date="20260317",
    )


def test_margin_secs_fetch_falls_back_to_exchange_fanout_at_row_cap():
    client = MagicMock()
    capped_frame = pd.DataFrame(
        {
            "trade_date": ["20260317"] * 6000,
            "ts_code": [f"600{i:04d}.SH" for i in range(6000)],
            "name": ["名称"] * 6000,
            "exchange": ["SSE"] * 6000,
        }
    )
    sse_frame = pd.DataFrame(
        {
            "trade_date": ["20260317"],
            "ts_code": ["600000.SH"],
            "name": ["浦发银行"],
            "exchange": ["SSE"],
        }
    )
    szse_frame = pd.DataFrame(
        {
            "trade_date": ["20260317"],
            "ts_code": ["000001.SZ"],
            "name": ["平安银行"],
            "exchange": ["SZSE"],
        }
    )
    bse_frame = pd.DataFrame(
        {
            "trade_date": ["20260317"],
            "ts_code": ["430001.BJ"],
            "name": ["北证样例"],
            "exchange": ["BSE"],
        }
    )
    client.call.side_effect = [capped_frame, sse_frame, szse_frame, bse_frame]

    fetcher = MarginSecsFetch(client=client)
    result = fetcher.fetch(trade_date="20260317")

    assert list(result.columns) == fetcher.fields
    assert result["exchange"].tolist() == list(MARGIN_SECS_EXCHANGES)
    assert client.call.call_args_list == [
        call("margin_secs", fields=",".join(fetcher.fields), trade_date="20260317"),
        call("margin_secs", fields=",".join(fetcher.fields), exchange="SSE", trade_date="20260317"),
        call("margin_secs", fields=",".join(fetcher.fields), exchange="SZSE", trade_date="20260317"),
        call("margin_secs", fields=",".join(fetcher.fields), exchange="BSE", trade_date="20260317"),
    ]


def test_limit_list_d_fetch_uses_single_request_when_result_is_below_row_cap():
    client = MagicMock()
    client.call.return_value = pd.DataFrame(
        {
            "trade_date": ["20260317", "20260317"],
            "ts_code": ["600000.SH", "000001.SZ"],
            "industry": ["银行", "银行"],
            "name": ["浦发银行", "平安银行"],
            "close": [10.0, 11.0],
            "pct_chg": [10.0, -10.0],
            "amount": [1.0, 2.0],
            "limit_amount": [None, 3.0],
            "float_mv": [4.0, 5.0],
            "total_mv": [6.0, 7.0],
            "turnover_ratio": [8.0, 9.0],
            "fd_amount": [10.0, 11.0],
            "first_time": ["09:30:00", None],
            "last_time": ["14:56:00", "14:58:00"],
            "open_times": [0, 1],
            "up_stat": ["1/1", None],
            "limit_times": [1, 0],
            "limit": ["U", "D"],
        }
    )

    fetcher = LimitListDFetch(client=client)
    result = fetcher.fetch(trade_date="20260317")

    assert list(result.columns) == fetcher.fields
    assert result["ts_code"].tolist() == ["600000.SH", "000001.SZ"]
    client.call.assert_called_once_with(
        "limit_list_d",
        fields=",".join(fetcher.fields),
        trade_date="20260317",
    )


def test_limit_list_d_fetch_falls_back_to_exchange_fanout_at_row_cap():
    client = MagicMock()
    capped_frame = pd.DataFrame(
        {
            "trade_date": ["20260317"] * 2500,
            "ts_code": [f"600{i:03d}.SH" for i in range(2500)],
            "industry": ["行业"] * 2500,
            "name": ["名称"] * 2500,
            "close": [10.0] * 2500,
            "pct_chg": [10.0] * 2500,
            "amount": [1.0] * 2500,
            "limit_amount": [None] * 2500,
            "float_mv": [4.0] * 2500,
            "total_mv": [6.0] * 2500,
            "turnover_ratio": [8.0] * 2500,
            "fd_amount": [10.0] * 2500,
            "first_time": ["09:30:00"] * 2500,
            "last_time": ["14:56:00"] * 2500,
            "open_times": [0] * 2500,
            "up_stat": ["1/1"] * 2500,
            "limit_times": [1] * 2500,
            "limit": ["U"] * 2500,
        }
    )
    sh_frame = pd.DataFrame(
        {
            "trade_date": ["20260317"],
            "ts_code": ["600000.SH"],
            "industry": ["银行"],
            "name": ["浦发银行"],
            "close": [10.0],
            "pct_chg": [10.0],
            "amount": [1.0],
            "limit_amount": [0.0],
            "float_mv": [4.0],
            "total_mv": [6.0],
            "turnover_ratio": [8.0],
            "fd_amount": [10.0],
            "first_time": ["09:30:00"],
            "last_time": ["14:56:00"],
            "open_times": [0],
            "up_stat": ["1/1"],
            "limit_times": [1],
            "limit": ["U"],
        }
    )
    sz_frame = pd.DataFrame(
        {
            "trade_date": ["20260317"],
            "ts_code": ["000001.SZ"],
            "industry": ["银行"],
            "name": ["平安银行"],
            "close": [11.0],
            "pct_chg": [-10.0],
            "amount": [2.0],
            "limit_amount": [3.0],
            "float_mv": [5.0],
            "total_mv": [7.0],
            "turnover_ratio": [9.0],
            "fd_amount": [11.0],
            "first_time": [""],
            "last_time": ["14:58:00"],
            "open_times": [1],
            "up_stat": [""],
            "limit_times": [0],
            "limit": ["D"],
        }
    )
    bj_frame = pd.DataFrame(columns=LimitListDFetch.fields)
    client.call.side_effect = [capped_frame, sh_frame, sz_frame, bj_frame]

    fetcher = LimitListDFetch(client=client)
    result = fetcher.fetch(trade_date="20260317")

    assert list(result.columns) == fetcher.fields
    assert result["ts_code"].tolist() == ["600000.SH", "000001.SZ"]
    assert client.call.call_args_list == [
        call("limit_list_d", fields=",".join(fetcher.fields), trade_date="20260317"),
        call("limit_list_d", fields=",".join(fetcher.fields), exchange="SH", trade_date="20260317"),
        call("limit_list_d", fields=",".join(fetcher.fields), exchange="SZ", trade_date="20260317"),
        call("limit_list_d", fields=",".join(fetcher.fields), exchange="BJ", trade_date="20260317"),
    ]


def test_hm_list_fetch_uses_text_columns_for_long_text_fields():
    assert HMListFetch.table_schema.columns["desc"].dtype == "TEXT"
    assert HMListFetch.table_schema.columns["orgs"].dtype == "TEXT"


def test_hm_list_fetch_uses_snapshot_date_from_params_without_passing_it_to_api():
    client = MagicMock()
    client.call.return_value = pd.DataFrame(
        {
            "name": ["章盟主"],
            "desc": ["活跃游资"],
            "orgs": ["宁波桑田路"],
        }
    )

    fetcher = HMListFetch(client=client)
    result = fetcher.fetch(snapshot_date="20260318")

    assert list(result.columns) == fetcher.fields
    assert list(result["snapshot_date"]) == ["20260318"]
    client.call.assert_called_once_with("hm_list", fields=",".join(fetcher.fields[:-1]))

def _all_tushare_fetchers() -> list[type[BaseFetcher]]:
    return [*FETCHER_REGISTRY.values(), StockBasicFetch, StockCompanyFetch, TradeCalFetch]


def test_fetcher_fields_and_table_schema_columns_have_identical_order():
    for fetcher_cls in _all_tushare_fetchers():
        assert list(fetcher_cls.table_schema.columns) == fetcher_cls.fields


def test_money_flow_mkt_dc_fetch_keeps_column_order_and_schema():
    fetcher_cls = FETCHER_REGISTRY["MoneyFlowMktDCFetch"]
    client = MagicMock()
    client.call.return_value = pd.DataFrame(
        {
            "trade_date": ["20260317"],
            "close_sh": [3342.1],
            "pct_change_sh": [0.58],
            "close_sz": [10712.5],
            "pct_change_sz": [1.02],
            "net_amount": [218524761.0],
            "net_amount_rate": [12.3],
            "buy_elg_amount": [120000000.0],
            "buy_elg_amount_rate": [6.2],
            "buy_lg_amount": [80000000.0],
            "buy_lg_amount_rate": [4.1],
            "buy_md_amount": [30000000.0],
            "buy_md_amount_rate": [1.5],
            "buy_sm_amount": [-15000000.0],
            "buy_sm_amount_rate": [-0.8],
        }
    )

    fetcher = fetcher_cls(client=client)
    result = fetcher.fetch(trade_date="20260317")

    assert list(result.columns) == fetcher.fields
    assert fetcher.table_schema.columns["trade_date"].dtype == "CHAR(8)"
    assert fetcher.table_schema.columns["net_amount"].dtype == "DOUBLE"
    client.call.assert_called_once_with(
        "moneyflow_mkt_dc",
        fields=",".join(fetcher.fields),
        trade_date="20260317",
    )


def test_fetcher_table_schema_indexes_only_reference_declared_fields():
    for fetcher_cls in _all_tushare_fetchers():
        declared_fields = set(fetcher_cls.table_schema.columns)
        for index in fetcher_cls.table_schema.composite_indexes:
            assert set(index).issubset(declared_fields), (
                f"invalid composite index for {fetcher_cls.__name__}: {index}"
            )


def test_fetcher_table_schema_columns_all_have_comments():
    for fetcher_cls in _all_tushare_fetchers():
        for field_name, column in fetcher_cls.table_schema.columns.items():
            assert column.comment.strip(), f"missing comment for {fetcher_cls.__name__}.{field_name}"


def test_stk_factor_pro_fetch_uses_tushare_chinese_comments():
    columns = StkFactorProFetch.table_schema.columns
    expected_comments = {
        "open_qfq": "开盘价（前复权）",
        "pre_close": "昨收价(前复权)--为daily接口的pre_close,以当时复权因子计算值跟前一日close_qfq对不上，可不用",
        "turnover_rate_f": "换手率（自由流通股）",
        "ktn_upper_qfq": "肯特纳交易通道, N选20日，ATR选10日-CLOSE, HIGH, LOW, N=20, M=10",
        "lowdays": "LOWRANGE(LOW)表示当前最低价是近多少周期内最低价的最小值",
        "xsii_td4_qfq": "薛斯通道II-CLOSE, HIGH, LOW, N=102, M=7",
    }

    for field_name, expected_comment in expected_comments.items():
        assert columns[field_name].comment == expected_comment

    for field_name in StkFactorProFetch.fields:
        if field_name not in {"ts_code", "trade_date"}:
            assert columns[field_name].comment != field_name


def test_top10_holders_fetch_uses_ann_date_directly():
    client = MagicMock()
    client.call.return_value = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "ann_date": ["20260317"],
            "end_date": ["20251231"],
            "holder_name": ["holder-a"],
            "hold_amount": [1.0],
            "hold_ratio": [2.0],
            "hold_change": [0.1],
            "holder_type": ["person"],
        }
    )

    fetcher = Top10HoldersFetch(client=client)
    result = fetcher.fetch(ann_date="20260317")

    assert list(result.columns) == fetcher.fields
    client.call.assert_called_once_with(
        "top10_holders",
        fields=",".join(fetcher.fields),
        ann_date="20260317",
    )


def test_top10_floatholders_fetch_uses_ann_date_directly():
    client = MagicMock()
    client.call.return_value = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "ann_date": ["20260317"],
            "end_date": ["20251231"],
            "holder_name": ["holder-a"],
            "hold_amount": [1.0],
            "hold_ratio": [2.0],
            "hold_change": [0.1],
            "holder_type": ["person"],
        }
    )

    fetcher = Top10FloatHoldersFetch(client=client)
    result = fetcher.fetch(ann_date="20260317")

    assert list(result.columns) == fetcher.fields
    client.call.assert_called_once_with(
        "top10_floatholders",
        fields=",".join(fetcher.fields),
        ann_date="20260317",
    )


@pytest.mark.parametrize(
    ("fetcher_cls", "message"),
    [
        (PledgeDetailFetch, "pass snapshot_date explicitly"),
        (HMListFetch, "pass snapshot_date explicitly"),
    ],
)
def test_fetchers_reject_as_of_date_after_alias_removal(fetcher_cls, message):
    client = MagicMock()
    fetcher = fetcher_cls(client=client)

    with pytest.raises(ValueError, match=message):
        fetcher.fetch(as_of_date="20260317")

    client.call.assert_not_called()


def test_selected_reference_fetcher_sources_no_longer_mention_as_of_date():
    fetcher_paths = [
        Path(PledgeStatFetch.__module__.replace(".", "/") + ".py"),
        Path(Top10HoldersFetch.__module__.replace(".", "/") + ".py"),
        Path(Top10FloatHoldersFetch.__module__.replace(".", "/") + ".py"),
    ]

    for relative_path in fetcher_paths:
        source = (Path(__file__).resolve().parents[4] / relative_path).read_text(encoding="utf-8")
        assert "as_of_date" not in source
        assert "_coerce_date" not in source


def test_selected_reference_fetcher_sources_no_longer_pop_required_dates():
    fetcher_paths = [
        Path(PledgeStatFetch.__module__.replace(".", "/") + ".py"),
        Path(Top10HoldersFetch.__module__.replace(".", "/") + ".py"),
        Path(Top10FloatHoldersFetch.__module__.replace(".", "/") + ".py"),
    ]

    for relative_path in fetcher_paths:
        source = (Path(__file__).resolve().parents[4] / relative_path).read_text(encoding="utf-8")
        assert 'kwargs.pop("ann_date"' not in source
        assert 'kwargs.pop("end_date"' not in source


@pytest.mark.parametrize(
    ("fetcher_cls", "api_name"),
    [
        (IncomeVipFetch, "income_vip"),
        (BalancesheetVipFetch, "balancesheet_vip"),
        (CashflowVipFetch, "cashflow_vip"),
        (FinaIndicatorVipFetch, "fina_indicator_vip"),
    ],
)
def test_financial_period_fetches_use_ann_date_incrementally(fetcher_cls, api_name):
    client = MagicMock()
    client.call.return_value = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "ann_date": ["20260317"],
            "end_date": ["20251231"],
        }
    )

    fetcher = fetcher_cls(client=client)
    fetcher.fetch(ann_date="20260317")

    client.call.assert_called_once_with(
        api_name,
        ann_date="20260317",
        fields=",".join(fetcher.fields),
    )


def test_pledge_detail_fetch_uses_snapshot_date_from_params_and_fans_out_by_stock_code():
    client = MagicMock()
    client.call.side_effect = [
        pd.DataFrame({"ts_code": ["000001.SZ", "000002.SZ"]}),
        pd.DataFrame(
            {
                "ts_code": ["000001.SZ"],
                "ann_date": ["20260317"],
                "holder_name": ["holder_a"],
                "pledge_amount": [1000.0],
                "start_date": ["20260301"],
                "end_date": ["20260401"],
                "is_release": [0],
            }
        ),
        pd.DataFrame(
            {
                "ts_code": ["000002.SZ"],
                "ann_date": ["20260316"],
                "holder_name": ["holder_b"],
                "pledge_amount": [500.0],
                "start_date": ["20260201"],
                "end_date": ["20260501"],
                "is_release": [1],
            }
        ),
    ]

    fetcher = PledgeDetailFetch(client=client)
    result = fetcher.fetch(snapshot_date="20260318")

    assert list(result.columns) == fetcher.fields
    assert set(result["ts_code"]) == {"000001.SZ", "000002.SZ"}
    assert list(result["snapshot_date"]) == ["20260318", "20260318"]
    assert client.call.call_args_list[0].kwargs == {
        "exchange": "",
        "list_status": "L",
        "fields": "ts_code",
    }
    assert client.call.call_args_list[1].args == ("pledge_detail",)
    assert client.call.call_args_list[1].kwargs == {
        "ts_code": "000001.SZ",
        "fields": ",".join(fetcher.fields[:-1]),
    }
    assert client.call.call_args_list[2].args == ("pledge_detail",)
    assert client.call.call_args_list[2].kwargs == {
        "ts_code": "000002.SZ",
        "fields": ",".join(fetcher.fields[:-1]),
    }


def test_pledge_detail_fetch_uses_explicit_stock_codes_without_stock_basic_fanout():
    client = MagicMock()
    client.call.return_value = pd.DataFrame(
        {
            "ts_code": ["600000.SH"],
            "ann_date": ["20260317"],
            "holder_name": ["holder_a"],
            "pledge_amount": [1000.0],
            "start_date": ["20260301"],
            "end_date": ["20260401"],
            "is_release": [0],
        }
    )

    fetcher = PledgeDetailFetch(client=client)
    result = fetcher.fetch(snapshot_date="20260318", stock_codes=["600000.SH"])

    assert list(result.columns) == fetcher.fields
    assert list(result["snapshot_date"]) == ["20260318"]
    client.call.assert_called_once_with(
        "pledge_detail",
        ts_code="600000.SH",
        fields=",".join(fetcher.fields[:-1]),
    )


def test_pledge_detail_fetch_rejects_single_ts_code_argument():
    client = MagicMock()
    fetcher = PledgeDetailFetch(client=client)

    with pytest.raises(ValueError, match="pledge_detail fetches require stock_codes"):
        fetcher.fetch(snapshot_date="20260318", ts_code="600000.SH")

    client.call.assert_not_called()


@pytest.mark.parametrize("fetcher_cls", [PledgeDetailFetch, HMListFetch])
def test_snapshot_fetchers_require_snapshot_date(fetcher_cls):
    client = MagicMock()
    fetcher = fetcher_cls(client=client)

    with pytest.raises(ValueError, match="require snapshot_date"):
        fetcher.fetch()

    client.call.assert_not_called()


def test_pledge_stat_fetch_uses_end_date_directly():
    client = MagicMock()
    client.call.return_value = pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000002.SZ"],
            "end_date": ["20260317", "20260317"],
            "pledge_count": [1, 2],
            "unrest_pledge": ["10", "20"],
            "rest_pledge": ["0", "1"],
            "total_share": [100.0, 200.0],
            "pledge_ratio": [10.0, 20.0],
        }
    )

    fetcher = PledgeStatFetch(client=client)
    result = fetcher.fetch(end_date="20260317")

    assert list(result.columns) == fetcher.fields
    client.call.assert_called_once_with(
        "pledge_stat",
        fields=",".join(fetcher.fields),
        end_date="20260317",
    )


def test_pledge_detail_fetch_ignores_pledge_stat_shortcut_and_uses_stock_basic(sqlite_engine):
    with sqlite_engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE stock_pledge_stat (
                    ts_code TEXT,
                    end_date TEXT,
                    pledge_count INTEGER
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO stock_pledge_stat (ts_code, end_date, pledge_count)
                VALUES
                    ('000001.SZ', '20260313', 2),
                    ('000002.SZ', '20260313', 0),
                    ('000003.SZ', '20260312', 5)
                """
            )
        )

    client = MagicMock()
    client.call.side_effect = [
        pd.DataFrame({"ts_code": ["000001.SZ", "000002.SZ"]}),
        pd.DataFrame(
            {
                "ts_code": ["000001.SZ"],
                "ann_date": ["20260317"],
                "holder_name": ["holder_a"],
                "pledge_amount": [1000.0],
                "start_date": ["20260301"],
                "end_date": ["20260401"],
                "is_release": [0],
            }
        ),
        pd.DataFrame(
            {
                "ts_code": ["000002.SZ"],
                "ann_date": ["20260317"],
                "holder_name": ["holder_b"],
                "pledge_amount": [2000.0],
                "start_date": ["20260302"],
                "end_date": ["20260402"],
                "is_release": [1],
            }
        ),
    ]

    fetcher = PledgeDetailFetch(client=client)
    result = fetcher.fetch(snapshot_date="20260318")

    assert list(result["ts_code"]) == ["000001.SZ", "000002.SZ"]
    assert list(result["snapshot_date"]) == ["20260318", "20260318"]
    assert client.call.call_args_list[0].args == ("stock_basic",)
    assert client.call.call_args_list[0].kwargs == {
        "exchange": "",
        "list_status": "L",
        "fields": "ts_code",
    }
    assert client.call.call_args_list[1].args == ("pledge_detail",)
    assert client.call.call_args_list[1].kwargs == {
        "ts_code": "000001.SZ",
        "fields": ",".join(fetcher.fields[:-1]),
    }
    assert client.call.call_args_list[2].args == ("pledge_detail",)
    assert client.call.call_args_list[2].kwargs == {
        "ts_code": "000002.SZ",
        "fields": ",".join(fetcher.fields[:-1]),
    }
