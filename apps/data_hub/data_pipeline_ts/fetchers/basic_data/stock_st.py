from __future__ import annotations

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class StockStFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=397
    ST股票列表, 3000积分
        获取ST股票列表，可根据交易日期获取历史上每天的ST列表。
    API params:
        ts_code: 股票代码
        trade_date: 交易日期 YYYYMMDD
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
    """
    fields = [
        "ts_code",  # 股票代码
        "name",  # 股票名称
        "trade_date",  # 交易日期
        "type",  # 类型
        "type_name",  # 类型名称
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="股票代码"),
            "name": ColumnDef("VARCHAR(32)", nullable=True, comment="股票名称"),
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "type": ColumnDef("VARCHAR(32)", nullable=True, comment="类型"),
            "type_name": ColumnDef("VARCHAR(128)", nullable=True, comment="类型名称"),
        },
        composite_indexes=[
            ("trade_date",),
            ("trade_date", "ts_code"),
            ("ts_code",),
        ],
    )

    def read_data(self, **kwargs):
        frame = self.client.call("stock_st", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
