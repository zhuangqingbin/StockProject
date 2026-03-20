from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema


class StockSuspendDFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=214
    每日停复牌信息
        按日期获取股票停复牌信息。
    API params:
        ts_code: 股票代码
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期(YYYYMMDD)
        end_date: 结束日期(YYYYMMDD)
        suspend_type: 停复牌类型 S停牌 R复牌
    """

    fields = [
        "ts_code",         # TS代码
        "trade_date",      # 停复牌日期
        "suspend_timing",  # 日内停牌时间段
        "suspend_type",    # 停复牌类型
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS代码"),
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="停复牌日期"),
            "suspend_timing": ColumnDef("VARCHAR(16)", nullable=True, comment="日内停牌时间段"),
            "suspend_type": ColumnDef("VARCHAR(8)", nullable=True, comment="停复牌类型"),
        },
        composite_indexes=[
            ("trade_date",),
            ("trade_date", "ts_code"),
            ("ts_code",),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call(
            "suspend_d",
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
