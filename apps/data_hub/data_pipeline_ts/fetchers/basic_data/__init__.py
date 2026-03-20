"""
Split basic-data fetchers.

Rules for this package:
- one fetcher class per file
- module names follow the MySQL table_name in snake_case
- import from here when working directly with the basic-data group
- if a fetcher should be scheduled by data_pipeline_ts, keep it exported from
  this package and register it in data_pipeline_ts.jobs.catalog
"""

from .stock_new_share import NewShareFetch
from .stock_basic import StockBasicFetch
from .stock_company import StockCompanyFetch
from .stock_hsgt import STOCK_HSGT_TYPES, StockHsgtFetch
from .stock_st import StockStFetch
from .trade_cal import TradeCalFetch

__all__ = [
    "NewShareFetch",
    "StockBasicFetch",
    "StockCompanyFetch",
    "STOCK_HSGT_TYPES",
    "StockHsgtFetch",
    "StockStFetch",
    "TradeCalFetch",
]
