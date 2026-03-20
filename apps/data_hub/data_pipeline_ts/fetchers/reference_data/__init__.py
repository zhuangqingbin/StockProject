"""
Split reference-data fetchers.

Rules for this package:
- one fetcher class per file
- module names follow the MySQL table_name in snake_case
- use this package for shareholder, pledge, repurchase, unlock, and block-trade datasets
- if a fetcher should be scheduled by data_pipeline_ts, keep it exported from
  this package and register it in data_pipeline_ts.jobs.catalog
"""

from .stock_block_trade import BlockTradeFetch
from .stock_pledge_detail import PledgeDetailFetch
from .stock_pledge_stat import PledgeStatFetch
from .stock_repurchase import RepurchaseFetch
from .stock_share_float import ShareFloatFetch
from .stock_stk_holdernumber import StkHolderNumberFetch
from .stock_stk_holdertrade import StkHolderTradeFetch
from .stock_top10_floatholders import Top10FloatHoldersFetch
from .stock_top10_holders import Top10HoldersFetch

__all__ = [
    "Top10HoldersFetch",
    "Top10FloatHoldersFetch",
    "StkHolderNumberFetch",
    "StkHolderTradeFetch",
    "PledgeStatFetch",
    "PledgeDetailFetch",
    "RepurchaseFetch",
    "ShareFloatFetch",
    "BlockTradeFetch",
]
