"""
Split stock-market-data fetchers.

Rules for this package:
- one fetcher class per file
- module names follow the MySQL table_name in snake_case
- use this package for stock market quote and trading-detail datasets
- if a fetcher should be scheduled by data_pipeline_ts, keep it exported from
  this package and register it in data_pipeline_ts.jobs.catalog
"""

from .stock_daily import StockDailyFetch
from .stock_daily_qfq import StockDailyQfqFetch
from .stock_daily_basic import StockDailyBasicFetch
from .stock_ggt_daily import GGTDailyFetch
from .stock_ggt_top10 import GGTTop10Fetch
from .stock_hsgt_top10 import HSGTTop10Fetch
from .stock_stk_limit import StkLimitFetch
from .stock_suspend_d import StockSuspendDFetch

__all__ = [
    "StockDailyFetch",
    "StockDailyQfqFetch",
    "StockDailyBasicFetch",
    "StockSuspendDFetch",
    "StkLimitFetch",
    "HSGTTop10Fetch",
    "GGTTop10Fetch",
    "GGTDailyFetch",
]
