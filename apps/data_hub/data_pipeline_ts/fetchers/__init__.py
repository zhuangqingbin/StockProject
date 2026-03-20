from __future__ import annotations

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher
from apps.data_hub.data_pipeline_ts.fetchers.basic_data import (
    NewShareFetch,
    StockHsgtFetch,
    StockStFetch,
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
    StockDailyQfqFetch,
    StockSuspendDFetch,
)


JOB_FETCHERS: tuple[type[BaseFetcher], ...] = (
    StockDailyFetch,
    StockSuspendDFetch,
    StockDailyQfqFetch,
    StockDailyBasicFetch,
    MoneyFlowFetch,
    MoneyFlowHSGTFetch,
    MoneyFlowDCFetch,
    MoneyFlowMktDCFetch,
    MarginFetch,
    MarginDetailFetch,
    MarginSecsFetch,
    SLBLenFetch,
    StockHsgtFetch,
    StockStFetch,
    NewShareFetch,
    TopListFetch,
    TopInstFetch,
    LimitListDFetch,
    KPLListFetch,
    StkLimitFetch,
    HSGTTop10Fetch,
    GGTTop10Fetch,
    GGTDailyFetch,
    ForecastVipFetch,
    ExpressVipFetch,
    DisclosureDateFetch,
    DividendFetch,
    FinaAuditFetch,
    IncomeVipFetch,
    BalancesheetVipFetch,
    CashflowVipFetch,
    FinaIndicatorVipFetch,
    Top10HoldersFetch,
    Top10FloatHoldersFetch,
    StkHolderNumberFetch,
    StkHolderTradeFetch,
    PledgeStatFetch,
    PledgeDetailFetch,
    RepurchaseFetch,
    ShareFloatFetch,
    BlockTradeFetch,
    HMListFetch,
    KPLConceptConsFetch,
    ReportRCFetch,
    CyqPerfFetch,
    CyqChipsFetch,
    StkFactorProFetch,
    CcassHoldFetch,
    HKHoldFetch,
    StkAHComparisonFetch,
    StkSurvFetch,
)

FETCHER_REGISTRY: dict[str, type[BaseFetcher]] = {
    fetcher.__name__: fetcher for fetcher in JOB_FETCHERS
}

__all__ = ["FETCHER_REGISTRY", "JOB_FETCHERS"]
