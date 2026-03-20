from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class StkLimitFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=183
    每日涨跌停价格, 2000积分
        获取每日涨跌停价格。
    API params:
        ts_code: 股票代码(支持多个，逗号分隔)
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
    """
    fields = [
        "trade_date", # 交易日期
        "ts_code",    # TS股票代码
        "pre_close",  # 昨日收盘价
        "up_limit",   # 涨停价
        "down_limit", # 跌停价
    ]
    table_schema = TableSchema(
        columns={
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "pre_close": ColumnDef("DOUBLE", nullable=True, comment="昨日收盘价"),
            "up_limit": ColumnDef("DOUBLE", nullable=True, comment="涨停价"),
            "down_limit": ColumnDef("DOUBLE", nullable=True, comment="跌停价"),
        },
        composite_indexes=[
            ('trade_date',),
            ('trade_date', 'ts_code'),
            ('ts_code',),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call("stk_limit", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
