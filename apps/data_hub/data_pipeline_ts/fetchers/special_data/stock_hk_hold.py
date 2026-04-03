from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema


class HKHoldFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=188
    沪深港股通持股明细, 120积分试用 / 2000积分正式
        获取沪深港股通持股明细，数据来源港交所。
    API params:
        code: 交易所原始代码
        ts_code: TS股票代码
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
        exchange: 类型，SH/SZ/HK
    """

    fields = [
        "code",
        "trade_date",
        "ts_code",
        "name",
        "vol",
        "ratio",
        "exchange",
    ]
    table_schema = TableSchema(
        columns={
            "code": ColumnDef("VARCHAR(16)", nullable=True, comment="原始代码"),
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS代码"),
            "name": ColumnDef("TEXT", nullable=True, comment="股票名称"),
            "vol": ColumnDef("BIGINT", nullable=True, comment="持股数量"),
            "ratio": ColumnDef("DOUBLE", nullable=True, comment="持股占比"),
            "exchange": ColumnDef("VARCHAR(8)", nullable=True, comment="交易所类型"),
        },
        composite_indexes=[
            ("trade_date",),
            ("trade_date", "ts_code"),
            ("exchange", "trade_date"),
            ("ts_code",),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call(
            "hk_hold",
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or pd.DataFrame(frame).empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
