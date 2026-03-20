"""
Split margin-data fetchers.

Rules for this package:
- one fetcher class per file
- module names follow the MySQL table_name in snake_case
- use this package for margin financing and securities lending datasets
- if a fetcher should be scheduled by data_pipeline_ts, keep it exported from
  this package and register it in data_pipeline_ts.jobs.catalog
"""

from .stock_margin import MarginFetch
from .stock_margin_detail import MarginDetailFetch
from .stock_margin_secs import MarginSecsFetch
from .stock_slb_len import SLBLenFetch

__all__ = [
    "MarginFetch",
    "MarginDetailFetch",
    "MarginSecsFetch",
    "SLBLenFetch",
]
