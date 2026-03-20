"""
Split money-flow-data fetchers.

Rules for this package:
- one fetcher class per file
- module names follow the MySQL table_name in snake_case
- use this package for stock-level and market-level money-flow datasets
- if a fetcher should be scheduled by data_pipeline_ts, keep it exported from
  this package and register it in data_pipeline_ts.jobs.catalog
"""

from .stock_money_flow import MoneyFlowFetch
from .stock_money_flow_dc import MoneyFlowDCFetch
from .stock_money_flow_hsgt import MoneyFlowHSGTFetch
from .stock_money_flow_mkt_dc import MoneyFlowMktDCFetch

__all__ = [
    "MoneyFlowFetch",
    "MoneyFlowHSGTFetch",
    "MoneyFlowDCFetch",
    "MoneyFlowMktDCFetch",
]
