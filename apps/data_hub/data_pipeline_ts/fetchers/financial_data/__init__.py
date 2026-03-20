"""
Split financial-data fetchers.

Rules for this package:
- one fetcher class per file
- module names follow the MySQL table_name in snake_case
- use this package for financial statement and announcement datasets
- if a fetcher should be scheduled by data_pipeline_ts, keep it exported from
  this package and register it in data_pipeline_ts.jobs.catalog
"""

from .stock_balancesheet_vip import BalancesheetVipFetch
from .stock_cashflow_vip import CashflowVipFetch
from .stock_disclosure_date import DisclosureDateFetch
from .stock_dividend import DividendFetch
from .stock_express_vip import ExpressVipFetch
from .stock_fina_audit import FinaAuditFetch
from .stock_fina_indicator_vip import FinaIndicatorVipFetch
from .stock_forecast_vip import ForecastVipFetch
from .stock_income_vip import IncomeVipFetch

__all__ = [
    "BalancesheetVipFetch",
    "CashflowVipFetch",
    "DisclosureDateFetch",
    "DividendFetch",
    "ExpressVipFetch",
    "FinaAuditFetch",
    "FinaIndicatorVipFetch",
    "ForecastVipFetch",
    "IncomeVipFetch",
]
