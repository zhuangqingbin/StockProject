from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema


class CcassHoldFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=295
    中央结算系统持股统计, 120积分试用 / 5000积分正式
        获取中央结算系统持股汇总数据，覆盖全部历史数据。
    API params:
        ts_code: 股票代码
        hk_code: 港交所代码
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
    """

    fields = [
        "trade_date",
        "ts_code",
        "name",
        "shareholding",
        "hold_nums",
        "hold_ratio",
    ]
    table_schema = TableSchema(
        columns={
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="股票代码"),
            "name": ColumnDef("VARCHAR(32)", nullable=True, comment="股票名称"),
            "shareholding": ColumnDef("BIGINT", nullable=True, comment="持股量"),
            "hold_nums": ColumnDef("INT", nullable=True, comment="参与者数目"),
            "hold_ratio": ColumnDef("DOUBLE", nullable=True, comment="持股占比"),
        },
        composite_indexes=[
            ("trade_date",),
            ("trade_date", "ts_code"),
            ("ts_code",),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call(
            "ccass_hold",
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or pd.DataFrame(frame).empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
