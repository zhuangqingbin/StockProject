from __future__ import annotations

import pandas as pd

from apps.data_hub.data_pipeline_ak.fetchers.base import BaseFetcher, ColumnDef, TableSchema
from apps.data_hub.data_pipeline_ak.provider.client import AkShareClient


class AkshareTradeCalendarFetch(BaseFetcher):
    fields = ["trade_date"]
    table_schema = TableSchema(columns={"trade_date": ColumnDef("DATE", nullable=False)})

    def __init__(self, client=None):
        super().__init__(client=client or AkShareClient().module)

    def read_data(self, **kwargs):
        frame = self.client.tool_trade_date_hist_sina()
        result = pd.DataFrame(frame).rename(columns={"trade_date": "trade_date"})
        if result.empty:
            return pd.DataFrame(columns=self.fields)
        result["trade_date"] = pd.to_datetime(result["trade_date"]).dt.strftime("%Y-%m-%d")
        return result.reindex(columns=self.fields)
