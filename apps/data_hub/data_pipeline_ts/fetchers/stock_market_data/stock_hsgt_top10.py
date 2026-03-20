from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class HSGTTop10Fetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=48
    沪深股通十大成交股, 无积分限制
        获取沪深股通每日前十大成交详细数据。
    API params:
        ts_code: 股票代码
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期(YYYYMMDD)
        end_date: 结束日期(YYYYMMDD)
        market_type: 市场类型
    """
    fields = [
        "trade_date",  # 交易日期
        "ts_code",     # TS股票代码
        "name",        # 股票名称
        "close",       # 收盘价
        "change",      # 涨跌额
        "rank",        # 资金排名
        "market_type", # 市场类型
        "amount",      # 累计成交金额
        "net_amount",  # 净成交金额
        "buy",         # 买入金额
        "sell",        # 卖出金额
    ]
    table_schema = TableSchema(
        columns={
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "name": ColumnDef("VARCHAR(32)", nullable=True, comment="股票名称"),
            "close": ColumnDef("DOUBLE", nullable=True, comment="收盘价"),
            "change": ColumnDef("DOUBLE", nullable=True, comment="涨跌额"),
            "rank": ColumnDef("INT", nullable=True, comment="资金排名"),
            "market_type": ColumnDef("VARCHAR(8)", nullable=True, comment="市场类型"),
            "amount": ColumnDef("DOUBLE", nullable=True, comment="累计成交金额"),
            "net_amount": ColumnDef("DOUBLE", nullable=True, comment="净成交金额"),
            "buy": ColumnDef("DOUBLE", nullable=True, comment="买入金额"),
            "sell": ColumnDef("DOUBLE", nullable=True, comment="卖出金额"),
        },
        composite_indexes=[
            ('trade_date',),
            ('trade_date', 'ts_code'),
            ('ts_code',),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call("hsgt_top10", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
