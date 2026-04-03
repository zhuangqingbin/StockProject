from __future__ import annotations

import inspect

from apps.data_hub.data_pipeline_ts.fetchers.financial_data.stock_balancesheet_vip import (
    BalancesheetVipFetch,
)
from apps.data_hub.data_pipeline_ts.fetchers.financial_data.stock_cashflow_vip import (
    CashflowVipFetch,
)
from apps.data_hub.data_pipeline_ts.fetchers.financial_data.stock_disclosure_date import (
    DisclosureDateFetch,
)
from apps.data_hub.data_pipeline_ts.fetchers.financial_data.stock_dividend import DividendFetch
from apps.data_hub.data_pipeline_ts.fetchers.financial_data.stock_express_vip import ExpressVipFetch
from apps.data_hub.data_pipeline_ts.fetchers.financial_data.stock_fina_audit import FinaAuditFetch
from apps.data_hub.data_pipeline_ts.fetchers.financial_data.stock_fina_indicator_vip import (
    FinaIndicatorVipFetch,
)
from apps.data_hub.data_pipeline_ts.fetchers.financial_data.stock_forecast_vip import ForecastVipFetch
from apps.data_hub.data_pipeline_ts.fetchers.financial_data.stock_income_vip import IncomeVipFetch


def _extract_section_params(fetcher_cls: type, section_name: str = "API params") -> dict[str, str]:
    doc = inspect.getdoc(fetcher_cls)
    assert doc, f"missing docstring for {fetcher_cls.__name__}"

    in_section = False
    params: dict[str, str] = {}
    for raw_line in doc.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line == f"{section_name}:":
            in_section = True
            continue
        if not in_section:
            continue
        if line.endswith("params:") and line != f"{section_name}:":
            break
        if ": " not in line:
            break
        name, description = line.split(": ", 1)
        params[name.strip()] = description.strip()
    return params


EXPECTED_API_PARAMS = {
    IncomeVipFetch: {
        "ts_code": "股票代码",
        "ann_date": "公告日期(YYYYMMDD)",
        "f_ann_date": "实际公告日期(YYYYMMDD)",
        "start_date": "公告日开始日期(YYYYMMDD)",
        "end_date": "公告日结束日期(YYYYMMDD)",
        "period": "报告期(YYYYMMDD)",
        "report_type": "报告类型",
        "comp_type": "公司类型",
    },
    BalancesheetVipFetch: {
        "ts_code": "股票代码",
        "ann_date": "公告日期(YYYYMMDD)",
        "start_date": "公告日开始日期(YYYYMMDD)",
        "end_date": "公告日结束日期(YYYYMMDD)",
        "period": "报告期(YYYYMMDD)",
        "report_type": "报告类型",
        "comp_type": "公司类型",
    },
    CashflowVipFetch: {
        "ts_code": "股票代码",
        "ann_date": "公告日期(YYYYMMDD)",
        "f_ann_date": "实际公告日期(YYYYMMDD)",
        "start_date": "公告日开始日期(YYYYMMDD)",
        "end_date": "公告日结束日期(YYYYMMDD)",
        "period": "报告期(YYYYMMDD)",
        "report_type": "报告类型",
        "comp_type": "公司类型",
        "is_calc": "是否计算报表",
    },
    FinaIndicatorVipFetch: {
        "ts_code": "股票代码",
        "ann_date": "公告日期(YYYYMMDD)",
        "start_date": "报告期开始日期(YYYYMMDD)",
        "end_date": "报告期结束日期(YYYYMMDD)",
        "period": "报告期(YYYYMMDD)",
    },
    ForecastVipFetch: {
        "ts_code": "股票代码",
        "ann_date": "公告日期(YYYYMMDD)",
        "start_date": "公告开始日期(YYYYMMDD)",
        "end_date": "公告结束日期(YYYYMMDD)",
        "period": "报告期(YYYYMMDD)",
        "type": "预告类型",
    },
    ExpressVipFetch: {
        "ts_code": "股票代码",
        "ann_date": "公告日期(YYYYMMDD)",
        "start_date": "公告开始日期(YYYYMMDD)",
        "end_date": "公告结束日期(YYYYMMDD)",
        "period": "报告期(YYYYMMDD)",
    },
    FinaAuditFetch: {
        "ts_code": "股票代码",
        "ann_date": "公告日期(YYYYMMDD)",
        "start_date": "公告开始日期(YYYYMMDD)",
        "end_date": "公告结束日期(YYYYMMDD)",
        "period": "报告期(YYYYMMDD)",
    },
    DividendFetch: {
        "ts_code": "股票代码",
        "ann_date": "公告日期(YYYYMMDD)",
        "record_date": "股权登记日(YYYYMMDD)",
        "ex_date": "除权除息日(YYYYMMDD)",
        "imp_ann_date": "实施公告日(YYYYMMDD)",
    },
    DisclosureDateFetch: {
        "ts_code": "股票代码",
        "end_date": "报告期(YYYYMMDD)",
        "pre_date": "预计披露日期(YYYYMMDD)",
        "ann_date": "最新披露公告日(YYYYMMDD)",
        "actual_date": "实际披露日期(YYYYMMDD)",
    },
}


def test_financial_fetcher_api_param_docs_match_expected_contracts() -> None:
    for fetcher_cls, expected_params in EXPECTED_API_PARAMS.items():
        assert _extract_section_params(fetcher_cls) == expected_params
