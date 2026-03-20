from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class StockDailyBasicFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=32
    每日指标, 2000积分
        获取全部股票每日重要的基本面指标，单次最多返回 6000 行。
    API params:
        ts_code: 股票代码 (trade_date 二选一)
        trade_date: 交易日期(YYYYMMDD) (ts_code 二选一)
        start_date: 开始日期(YYYYMMDD)
        end_date: 结束日期(YYYYMMDD)
    """
    fields = [
        "ts_code",         # TS股票代码
        "trade_date",      # 交易日期
        "close",           # 当日收盘价
        "turnover_rate",   # 换手率
        "turnover_rate_f", # 自由流通股换手率
        "volume_ratio",    # 量比
        "pe",              # 市盈率
        "pe_ttm",          # 市盈率TTM
        "pb",              # 市净率
        "ps",              # 市销率
        "ps_ttm",          # 市销率TTM
        "dv_ratio",        # 股息率
        "dv_ttm",          # 股息率TTM
        "total_share",     # 总股本
        "float_share",     # 流通股本
        "free_share",      # 自由流通股本
        "total_mv",        # 总市值
        "circ_mv",         # 流通市值
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "close": ColumnDef("DOUBLE", nullable=True, comment="当日收盘价"),
            "turnover_rate": ColumnDef("DOUBLE", nullable=True, comment="换手率"),
            "turnover_rate_f": ColumnDef("DOUBLE", nullable=True, comment="自由流通股换手率"),
            "volume_ratio": ColumnDef("DOUBLE", nullable=True, comment="量比"),
            "pe": ColumnDef("DOUBLE", nullable=True, comment="市盈率"),
            "pe_ttm": ColumnDef("DOUBLE", nullable=True, comment="市盈率TTM"),
            "pb": ColumnDef("DOUBLE", nullable=True, comment="市净率"),
            "ps": ColumnDef("DOUBLE", nullable=True, comment="市销率"),
            "ps_ttm": ColumnDef("DOUBLE", nullable=True, comment="市销率TTM"),
            "dv_ratio": ColumnDef("DOUBLE", nullable=True, comment="股息率"),
            "dv_ttm": ColumnDef("DOUBLE", nullable=True, comment="股息率TTM"),
            "total_share": ColumnDef("DOUBLE", nullable=True, comment="总股本"),
            "float_share": ColumnDef("DOUBLE", nullable=True, comment="流通股本"),
            "free_share": ColumnDef("DOUBLE", nullable=True, comment="自由流通股本"),
            "total_mv": ColumnDef("DOUBLE", nullable=True, comment="总市值"),
            "circ_mv": ColumnDef("DOUBLE", nullable=True, comment="流通市值"),
        },
        composite_indexes=[
            ('trade_date',),
            ('trade_date', 'ts_code'),
            ('ts_code',),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call("daily_basic", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
