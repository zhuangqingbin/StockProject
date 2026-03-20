from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

STOCK_HSGT_TYPES = ("HK_SZ", "SZ_HK", "HK_SH", "SH_HK")

class StockHsgtFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=398
    沪深港通股票列表, 3000积分
        type 为必填字段, 单次请求最大返回 2000 行, 运行时按 type 循环拉取并合并。
    API params:
        ts_code: 股票代码
        trade_date: 交易日期(YYYYMMDD)
        type: 类型(HK_SZ / SZ_HK / HK_SH / SH_HK)
        start_date: 开始日期(YYYYMMDD)
        end_date: 结束日期(YYYYMMDD)
    """
    fields = [
        "ts_code",    # TS股票代码
        "trade_date", # 交易日期
        "type",       # 类型
        "name",       # 股票名称
        "type_name",  # 类型名称
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "type": ColumnDef("VARCHAR(8)", nullable=True, comment="类型"),
            "name": ColumnDef("VARCHAR(64)", nullable=True, comment="股票名称"),
            "type_name": ColumnDef("VARCHAR(16)", nullable=True, comment="类型名称"),
        },
        composite_indexes=[
            ('trade_date',),
            ('trade_date', 'ts_code'),
            ('ts_code',),
            ('trade_date', 'type'),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        trade_date = str(kwargs.get("trade_date", "")).strip()
        if not trade_date:
            raise ValueError("stock_hsgt fetches require trade_date")

        frames: list[pd.DataFrame] = []
        for type_value in STOCK_HSGT_TYPES:
            frame = self.client.call("stock_hsgt", 
                type=type_value,
                fields=",".join(self.fields),
                **kwargs,
            )
            if frame is None or frame.empty:
                continue
            frames.append(pd.DataFrame(frame).reindex(columns=self.fields))

        if not frames:
            return pd.DataFrame(columns=self.fields)

        return pd.concat(frames, ignore_index=True).reindex(columns=self.fields)
