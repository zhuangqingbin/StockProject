from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class GGTDailyFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=196
    港股通每日成交统计, 2000积分
        获取港股通每日成交信息。
    API params:
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期(YYYYMMDD)
        end_date: 结束日期(YYYYMMDD)
    """
    fields = [
        "trade_date",  # 交易日期
        "buy_amount",  # 买入成交金额
        "buy_volume",  # 买入成交笔数
        "sell_amount", # 卖出成交金额
        "sell_volume", # 卖出成交笔数
    ]
    table_schema = TableSchema(
        columns={
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "buy_amount": ColumnDef("DOUBLE", nullable=True, comment="买入成交金额"),
            "buy_volume": ColumnDef("DOUBLE", nullable=True, comment="买入成交笔数"),
            "sell_amount": ColumnDef("DOUBLE", nullable=True, comment="卖出成交金额"),
            "sell_volume": ColumnDef("DOUBLE", nullable=True, comment="卖出成交笔数"),
        },
        composite_indexes=[
            ('trade_date',),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call("ggt_daily", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
