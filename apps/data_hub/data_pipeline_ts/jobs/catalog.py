from __future__ import annotations

from typing import Any

from apps.data_hub.data_pipeline_ts.fetchers.basic_data import (
    NewShareFetch,
    StockBasicFetch,
    StockCompanyFetch,
    StockHsgtFetch,
    StockStFetch,
    TradeCalFetch,
)
from apps.data_hub.data_pipeline_ts.fetchers.board_data import (
    HMListFetch,
    KPLConceptConsFetch,
    KPLListFetch,
    LimitListDFetch,
    TopInstFetch,
    TopListFetch,
)
from apps.data_hub.data_pipeline_ts.fetchers.financial_data import (
    BalancesheetVipFetch,
    CashflowVipFetch,
    DisclosureDateFetch,
    DividendFetch,
    ExpressVipFetch,
    FinaAuditFetch,
    FinaIndicatorVipFetch,
    ForecastVipFetch,
    IncomeVipFetch,
)
from apps.data_hub.data_pipeline_ts.fetchers.margin_data import (
    MarginDetailFetch,
    MarginFetch,
    MarginSecsFetch,
    SLBLenFetch,
)
from apps.data_hub.data_pipeline_ts.fetchers.money_flow_data import (
    MoneyFlowDCFetch,
    MoneyFlowFetch,
    MoneyFlowHSGTFetch,
    MoneyFlowMktDCFetch,
)
from apps.data_hub.data_pipeline_ts.fetchers.reference_data import (
    BlockTradeFetch,
    PledgeDetailFetch,
    PledgeStatFetch,
    RepurchaseFetch,
    ShareFloatFetch,
    StkHolderNumberFetch,
    StkHolderTradeFetch,
    Top10FloatHoldersFetch,
    Top10HoldersFetch,
)
from apps.data_hub.data_pipeline_ts.fetchers.special_data import (
    CcassHoldFetch,
    CyqChipsFetch,
    CyqPerfFetch,
    HKHoldFetch,
    ReportRCFetch,
    StkAHComparisonFetch,
    StkFactorProFetch,
    StkSurvFetch,
)
from apps.data_hub.data_pipeline_ts.fetchers.stock_market_data import (
    GGTDailyFetch,
    GGTTop10Fetch,
    HSGTTop10Fetch,
    StkLimitFetch,
    StockDailyBasicFetch,
    StockDailyFetch,
    StockSuspendDFetch,
)
from apps.data_hub.data_pipeline_ts.jobs.profiles import (
    PROFILE_NAMES,
    PROFILE_SPECS,
    SCHEDULED_PROFILES,
    ProfileId,
)
from apps.data_hub.data_pipeline_ts.jobs.specs import FetchStrategy, InfrastructureSpec, JobSpec


def _job(
    *,
    name: str,
    table_name: str,
    fetcher_cls: type[Any],
    api_name: str,
    description: str,
    profile: ProfileId,
    params: dict[str, object] | None = None,
    scope_columns: tuple[str, ...] = (),
    fetch_strategies: tuple[FetchStrategy, ...] = ("direct",),
) -> JobSpec:
    return JobSpec(
        name=name,
        table_name=table_name,
        fetcher_cls=fetcher_cls,
        api_name=api_name,
        description=description,
        profile=profile,
        params=dict(params or {}),
        scope_columns=scope_columns,
        fetch_strategies=fetch_strategies,
        table_schema=getattr(fetcher_cls, "table_schema", None),
    )


def _infra(
    *,
    name: str,
    fetcher_cls: type[Any],
    table_name: str,
    api_name: str,
    scope_columns: tuple[str, ...],
) -> InfrastructureSpec:
    return InfrastructureSpec(
        name=name,
        fetcher_cls=fetcher_cls,
        table_name=table_name,
        scope_columns=scope_columns,
        api_name=api_name,
        table_schema=getattr(fetcher_cls, "table_schema", None),
    )


BASIC_DATA_JOBS = [
    _job(
        name="stock_hsgt", table_name="stock_hsgt", fetcher_cls=StockHsgtFetch, api_name="stock_hsgt", description="沪深港通成份",
        profile=ProfileId.TRADE_DAY_PRE_OPEN, fetch_strategies=("enum_fanout_type",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="stock_st", table_name="stock_st", fetcher_cls=StockStFetch, api_name="stock_st", description="风险警示股票",
        profile=ProfileId.TRADE_DAY_PRE_OPEN, fetch_strategies=("direct",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="new_share", table_name="stock_new_share", fetcher_cls=NewShareFetch, api_name="new_share", description="新股发行",
        profile=ProfileId.TRADE_DAY_PRE_OPEN, fetch_strategies=("direct",), params={"start_date": "{trade_date}", "end_date": "{trade_date}"}, scope_columns=("ipo_date",),
    ),
]

BOARD_DATA_JOBS = [
    _job(
        name="top_list", table_name="stock_top_list", fetcher_cls=TopListFetch, api_name="top_list", description="龙虎榜每日明细",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_CORE, fetch_strategies=("direct", "post_fetch_dedup"), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="top_inst", table_name="stock_top_inst", fetcher_cls=TopInstFetch, api_name="top_inst", description="龙虎榜机构明细",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, fetch_strategies=("direct",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="limit_list_d", table_name="stock_limit_list_d", fetcher_cls=LimitListDFetch, api_name="limit_list_d", description="涨跌停统计",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, fetch_strategies=("row_cap_fallback_exchange",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="kpl_list", table_name="stock_kpl_list", fetcher_cls=KPLListFetch, api_name="kpl_list", description="开盘啦题材榜",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, fetch_strategies=("enum_fanout_tag",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="kpl_concept_cons", table_name="stock_kpl_concept_cons", fetcher_cls=KPLConceptConsFetch, api_name="kpl_concept_cons", description="开盘啦题材成份",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, fetch_strategies=("direct",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="hm_list", table_name="stock_hm_list", fetcher_cls=HMListFetch, api_name="hm_list", description="游资营业部龙虎榜快照",
        profile=ProfileId.MANUAL, fetch_strategies=("direct", "snapshot_column"), params={"snapshot_date": "{current_date}"}, scope_columns=("snapshot_date",),
    ),
]

FINANCIAL_DATA_JOBS = [
    _job(
        name="forecast_vip", table_name="stock_forecast_vip", fetcher_cls=ForecastVipFetch, api_name="forecast_vip", description="业绩预告增量",
        profile=ProfileId.FINANCIAL_CALENDAR_NIGHTLY, fetch_strategies=("direct",), params={"ann_date": "{current_date}"}, scope_columns=("ann_date",),
    ),
    _job(
        name="express_vip", table_name="stock_express_vip", fetcher_cls=ExpressVipFetch, api_name="express_vip", description="业绩快报增量",
        profile=ProfileId.FINANCIAL_CALENDAR_NIGHTLY, fetch_strategies=("direct",), params={"ann_date": "{current_date}"}, scope_columns=("ann_date",),
    ),
    _job(
        name="disclosure_date", table_name="stock_disclosure_date", fetcher_cls=DisclosureDateFetch, api_name="disclosure_date", description="财报披露计划",
        profile=ProfileId.FINANCIAL_CALENDAR_NIGHTLY, fetch_strategies=("direct",), params={"ann_date": "{current_date}"}, scope_columns=("ann_date",),
    ),
    _job(
        name="dividend", table_name="stock_dividend", fetcher_cls=DividendFetch, api_name="dividend", description="分红送股公告增量",
        profile=ProfileId.FINANCIAL_CALENDAR_NIGHTLY, fetch_strategies=("direct",), params={"ann_date": "{current_date}"}, scope_columns=("ann_date",),
    ),
    _job(
        name="fina_audit", table_name="stock_fina_audit", fetcher_cls=FinaAuditFetch, api_name="fina_audit", description="财务审计意见增量",
        profile=ProfileId.MANUAL, fetch_strategies=("full_market_stock_code_fanout",), params={"ann_date": "{current_date}"}, scope_columns=("ann_date",),
    ),
    _job(
        name="income_vip", table_name="stock_income_vip", fetcher_cls=IncomeVipFetch, api_name="income_vip", description="利润表披露增量",
        profile=ProfileId.FINANCIAL_CALENDAR_NIGHTLY, fetch_strategies=("direct",), params={"ann_date": "{current_date}"}, scope_columns=("ann_date",),
    ),
    _job(
        name="balancesheet_vip", table_name="stock_balancesheet_vip", fetcher_cls=BalancesheetVipFetch, api_name="balancesheet_vip", description="资产负债表披露增量",
        profile=ProfileId.FINANCIAL_CALENDAR_NIGHTLY, fetch_strategies=("direct",), params={"ann_date": "{current_date}"}, scope_columns=("ann_date",),
    ),
    _job(
        name="cashflow_vip", table_name="stock_cashflow_vip", fetcher_cls=CashflowVipFetch, api_name="cashflow_vip", description="现金流量表披露增量",
        profile=ProfileId.FINANCIAL_CALENDAR_NIGHTLY, fetch_strategies=("direct",), params={"ann_date": "{current_date}"}, scope_columns=("ann_date",),
    ),
    _job(
        name="fina_indicator_vip", table_name="stock_fina_indicator_vip", fetcher_cls=FinaIndicatorVipFetch, api_name="fina_indicator_vip", description="财务指标披露增量",
        profile=ProfileId.FINANCIAL_CALENDAR_NIGHTLY, fetch_strategies=("direct",), params={"ann_date": "{current_date}"}, scope_columns=("ann_date",),
    ),
]

MARGIN_DATA_JOBS = [
    _job(
        name="margin", table_name="stock_margin", fetcher_cls=MarginFetch, api_name="margin", description="融资融券汇总",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, fetch_strategies=("row_cap_fallback_exchange_id",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="margin_detail", table_name="stock_margin_detail", fetcher_cls=MarginDetailFetch, api_name="margin_detail", description="融资融券明细",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, fetch_strategies=("direct",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="margin_secs", table_name="stock_margin_secs", fetcher_cls=MarginSecsFetch, api_name="margin_secs", description="融券卖出量",
        profile=ProfileId.TRADE_DAY_PRE_OPEN, fetch_strategies=("row_cap_fallback_exchange",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="slb_len", table_name="stock_slb_len", fetcher_cls=SLBLenFetch, api_name="slb_len", description="转融通期限统计",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, fetch_strategies=("direct",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
]

MONEY_FLOW_DATA_JOBS = [
    _job(
        name="money_flow", table_name="stock_money_flow", fetcher_cls=MoneyFlowFetch, api_name="moneyflow", description="个股资金流向",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_CORE, fetch_strategies=("direct",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="money_flow_hsgt", table_name="stock_money_flow_hsgt", fetcher_cls=MoneyFlowHSGTFetch, api_name="moneyflow_hsgt", description="沪深港通资金流向",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_CORE, fetch_strategies=("direct",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="money_flow_dc", table_name="stock_money_flow_dc", fetcher_cls=MoneyFlowDCFetch, api_name="moneyflow_dc", description="东方财富资金流向",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, fetch_strategies=("direct",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="money_flow_mkt_dc", table_name="stock_money_flow_mkt_dc", fetcher_cls=MoneyFlowMktDCFetch, api_name="moneyflow_mkt_dc", description="东方财富大盘资金流向",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, fetch_strategies=("direct",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
]

REFERENCE_DATA_JOBS = [
    _job(
        name="top10_holders", table_name="stock_top10_holders", fetcher_cls=Top10HoldersFetch, api_name="top10_holders", description="十大股东增量",
        profile=ProfileId.REFERENCE_CALENDAR_NIGHTLY, fetch_strategies=("direct",), params={"ann_date": "{current_date}"}, scope_columns=("ann_date",),
    ),
    _job(
        name="top10_floatholders", table_name="stock_top10_floatholders", fetcher_cls=Top10FloatHoldersFetch, api_name="top10_floatholders", description="十大流通股东增量",
        profile=ProfileId.REFERENCE_CALENDAR_NIGHTLY, fetch_strategies=("direct",), params={"ann_date": "{current_date}"}, scope_columns=("ann_date",),
    ),
    _job(
        name="stk_holdernumber", table_name="stock_stk_holdernumber", fetcher_cls=StkHolderNumberFetch, api_name="stk_holdernumber", description="股东户数增量",
        profile=ProfileId.REFERENCE_CALENDAR_NIGHTLY, fetch_strategies=("direct",), params={"ann_date": "{current_date}"}, scope_columns=("ann_date",),
    ),
    _job(
        name="stk_holdertrade", table_name="stock_stk_holdertrade", fetcher_cls=StkHolderTradeFetch, api_name="stk_holdertrade", description="股东增减持增量",
        profile=ProfileId.REFERENCE_CALENDAR_NIGHTLY, fetch_strategies=("direct",), params={"ann_date": "{current_date}"}, scope_columns=("ann_date",),
    ),
    _job(
        name="pledge_stat", table_name="stock_pledge_stat", fetcher_cls=PledgeStatFetch, api_name="pledge_stat", description="股票质押统计增量",
        profile=ProfileId.REFERENCE_CALENDAR_NIGHTLY, fetch_strategies=("direct",), params={"end_date": "{current_date}"}, scope_columns=("end_date",),
    ),
    _job(
        name="pledge_detail", table_name="stock_pledge_detail", fetcher_cls=PledgeDetailFetch, api_name="pledge_detail", description="股票质押明细快照",
        profile=ProfileId.MANUAL, fetch_strategies=("full_market_stock_code_fanout", "snapshot_column"), params={"snapshot_date": "{current_date}"}, scope_columns=("snapshot_date",),
    ),
    _job(
        name="repurchase", table_name="stock_repurchase", fetcher_cls=RepurchaseFetch, api_name="repurchase", description="股票回购增量",
        profile=ProfileId.REFERENCE_CALENDAR_NIGHTLY, fetch_strategies=("direct",), params={"ann_date": "{current_date}"}, scope_columns=("ann_date",),
    ),
    _job(
        name="share_float", table_name="stock_share_float", fetcher_cls=ShareFloatFetch, api_name="share_float", description="限售股解禁增量",
        profile=ProfileId.REFERENCE_CALENDAR_NIGHTLY, fetch_strategies=("direct",), params={"ann_date": "{current_date}"}, scope_columns=("ann_date",),
    ),
    _job(
        name="block_trade", table_name="stock_block_trade", fetcher_cls=BlockTradeFetch, api_name="block_trade", description="大宗交易",
        profile=ProfileId.REFERENCE_TRADE_DAY_POST_CLOSE, fetch_strategies=("direct",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
]

SPECIAL_DATA_JOBS = [
    _job(
        name="report_rc", table_name="stock_report_rc", fetcher_cls=ReportRCFetch, api_name="report_rc", description="卖方盈利预测数据",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, fetch_strategies=("direct",), params={"report_date": "{current_date}"}, scope_columns=("report_date",),
    ),
    _job(
        name="cyq_perf", table_name="stock_cyq_perf", fetcher_cls=CyqPerfFetch, api_name="cyq_perf", description="每日筹码及胜率",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, fetch_strategies=("direct",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="cyq_chips", table_name="stock_cyq_chips", fetcher_cls=CyqChipsFetch, api_name="cyq_chips", description="每日筹码分布",
        profile=ProfileId.MANUAL, fetch_strategies=("full_market_stock_code_fanout", "custom_rate_limit_handling"), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="stk_factor_pro", table_name="stock_stk_factor_pro", fetcher_cls=StkFactorProFetch, api_name="stk_factor_pro", description="股票技术面因子(专业版)",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, fetch_strategies=("direct",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="ccass_hold", table_name="stock_ccass_hold", fetcher_cls=CcassHoldFetch, api_name="ccass_hold", description="中央结算系统持股统计",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, fetch_strategies=("direct",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="hk_hold", table_name="stock_hk_hold", fetcher_cls=HKHoldFetch, api_name="hk_hold", description="沪深股通持股明细",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, fetch_strategies=("direct",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="stk_ah_comparison", table_name="stock_stk_ah_comparison", fetcher_cls=StkAHComparisonFetch, api_name="stk_ah_comparison", description="AH股比价",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, fetch_strategies=("direct",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="stk_surv", table_name="stock_stk_surv", fetcher_cls=StkSurvFetch, api_name="stk_surv", description="机构调研数据",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, fetch_strategies=("direct",), params={"trade_date": "{current_date}"}, scope_columns=("surv_date",),
    ),
]

STOCK_MARKET_DATA_JOBS = [
    _job(
        name="stock_daily", table_name="stock_daily", fetcher_cls=StockDailyFetch, api_name="daily", description="股票日线行情",
        profile=ProfileId.MANUAL, fetch_strategies=("direct",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="stock_daily_basic", table_name="stock_daily_basic", fetcher_cls=StockDailyBasicFetch, api_name="daily_basic", description="股票日线基本指标",
        profile=ProfileId.MANUAL, fetch_strategies=("direct",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="stock_suspend_d", table_name="stock_suspend_d", fetcher_cls=StockSuspendDFetch, api_name="suspend_d", description="每日停复牌信息增量",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_CORE, fetch_strategies=("direct",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="stk_limit", table_name="stock_stk_limit", fetcher_cls=StkLimitFetch, api_name="stk_limit", description="个股涨跌停价格",
        profile=ProfileId.TRADE_DAY_PRE_OPEN, fetch_strategies=("direct",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="hsgt_top10", table_name="stock_hsgt_top10", fetcher_cls=HSGTTop10Fetch, api_name="hsgt_top10", description="沪深港通十大成交股",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, fetch_strategies=("direct",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="ggt_top10", table_name="stock_ggt_top10", fetcher_cls=GGTTop10Fetch, api_name="ggt_top10", description="港股通十大成交股",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, fetch_strategies=("direct",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
    _job(
        name="ggt_daily", table_name="stock_ggt_daily", fetcher_cls=GGTDailyFetch, api_name="ggt_daily", description="港股通每日成交统计",
        profile=ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED, fetch_strategies=("direct",), params={"trade_date": "{trade_date}"}, scope_columns=("trade_date",),
    ),
]

ALL_JOBS = [
    *BASIC_DATA_JOBS,
    *BOARD_DATA_JOBS,
    *FINANCIAL_DATA_JOBS,
    *MARGIN_DATA_JOBS,
    *MONEY_FLOW_DATA_JOBS,
    *REFERENCE_DATA_JOBS,
    *SPECIAL_DATA_JOBS,
    *STOCK_MARKET_DATA_JOBS,
]


def _group_jobs_by_profile(job_specs: list[JobSpec]) -> dict[ProfileId, tuple[JobSpec, ...]]:
    grouped: dict[ProfileId, list[JobSpec]] = {}
    for job in job_specs:
        grouped.setdefault(job.profile, []).append(job)
    return {profile: tuple(jobs) for profile, jobs in grouped.items()}


INFRASTRUCTURE_TARGETS = {
    "stock_basic": _infra(name="stock_basic", fetcher_cls=StockBasicFetch, table_name="stock_basic", api_name="stock_basic", scope_columns=("ts_code",)),
    "stock_company": _infra(name="stock_company", fetcher_cls=StockCompanyFetch, table_name="stock_company", api_name="stock_company", scope_columns=("ts_code",)),
    "trade_cal": _infra(name="trade_cal", fetcher_cls=TradeCalFetch, table_name="trade_cal", api_name="trade_cal", scope_columns=("exchange", "cal_date")),
}

JOBS_BY_PROFILE = _group_jobs_by_profile(ALL_JOBS)

__all__ = [
    "ALL_JOBS",
    "BASIC_DATA_JOBS",
    "BOARD_DATA_JOBS",
    "FINANCIAL_DATA_JOBS",
    "INFRASTRUCTURE_TARGETS",
    "JOBS_BY_PROFILE",
    "MARGIN_DATA_JOBS",
    "MONEY_FLOW_DATA_JOBS",
    "PROFILE_NAMES",
    "PROFILE_SPECS",
    "SCHEDULED_PROFILES",
    "REFERENCE_DATA_JOBS",
    "SPECIAL_DATA_JOBS",
    "STOCK_MARKET_DATA_JOBS",
]
