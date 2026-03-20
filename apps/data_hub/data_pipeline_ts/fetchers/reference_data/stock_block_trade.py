from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class BlockTradeFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=161
    大宗交易, 300积分
        按交易日期提取大宗交易数据。
    API params:
        ts_code: 股票代码
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期(YYYYMMDD)
        end_date: 结束日期(YYYYMMDD)
    """
    fields = [
        "ts_code",     # TS股票代码
        "trade_date",  # 交易日期
        "price",       # 成交价格
        "vol",         # 成交量
        "amount",      # 成交金额
        "buyer",       # 买方营业部
        "seller",      # 卖方营业部
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "price": ColumnDef("DOUBLE", nullable=True, comment="成交价格"),
            "vol": ColumnDef("DOUBLE", nullable=True, comment="成交量"),
            "amount": ColumnDef("DOUBLE", nullable=True, comment="成交金额"),
            "buyer": ColumnDef("VARCHAR(255)", nullable=True, comment="买方营业部"),
            "seller": ColumnDef("VARCHAR(255)", nullable=True, comment="卖方营业部"),
        },
        composite_indexes=[
            ('trade_date',),
            ('trade_date', 'ts_code'),
            ('ts_code',),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call("block_trade", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
