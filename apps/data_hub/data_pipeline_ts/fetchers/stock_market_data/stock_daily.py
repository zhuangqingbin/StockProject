from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class StockDailyFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=27
    A股日线行情
        交易日每天15点-16点之间入库。本接口是未复权行情，停牌期间不提供数据。
    API params:
        ts_code: 股票代码 (trade_date 二选一)
        trade_date: 交易日期(YYYYMMDD) (ts_code 二选一)
        start_date: 开始日期(YYYYMMDD)
        end_date: 结束日期(YYYYMMDD)
    """
    fields = [
        "ts_code",    # TS股票代码
        "trade_date", # 交易日期
        "open",       # 开盘价
        "high",       # 最高价
        "low",        # 最低价
        "close",      # 收盘价
        "pre_close",  # 昨收价
        "change",     # 涨跌额
        "pct_chg",    # 涨跌幅
        "vol",        # 成交量
        "amount",     # 成交额
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "open": ColumnDef("DOUBLE", nullable=True, comment="开盘价"),
            "high": ColumnDef("DOUBLE", nullable=True, comment="最高价"),
            "low": ColumnDef("DOUBLE", nullable=True, comment="最低价"),
            "close": ColumnDef("DOUBLE", nullable=True, comment="收盘价"),
            "pre_close": ColumnDef("DOUBLE", nullable=True, comment="昨收价"),
            "change": ColumnDef("DOUBLE", nullable=True, comment="涨跌额"),
            "pct_chg": ColumnDef("DOUBLE", nullable=True, comment="涨跌幅"),
            "vol": ColumnDef("DOUBLE", nullable=True, comment="成交量"),
            "amount": ColumnDef("DOUBLE", nullable=True, comment="成交额"),
        },
        composite_indexes=[
            ('trade_date',),
            ('trade_date', 'ts_code'),
            ('ts_code',),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call("daily", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
