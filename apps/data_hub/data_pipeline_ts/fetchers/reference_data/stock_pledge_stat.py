from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema


class PledgeStatFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=110
    股权质押统计, 500积分
        按截止日提取全市场股权质押统计数据。
    API params:
        ts_code: 股票代码
        end_date: 截止日期(YYYYMMDD)
    """

    fields = [
        "ts_code",
        "end_date",
        "pledge_count",
        "unrest_pledge",
        "rest_pledge",
        "total_share",
        "pledge_ratio",
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS代码"),
            "end_date": ColumnDef("CHAR(8)", nullable=True, comment="截止日期"),
            "pledge_count": ColumnDef("INT", nullable=True, comment="质押次数"),
            "unrest_pledge": ColumnDef("DOUBLE", nullable=True, comment="无限售股质押数量(万)"),
            "rest_pledge": ColumnDef("DOUBLE", nullable=True, comment="限售股份质押数量(万)"),
            "total_share": ColumnDef("DOUBLE", nullable=True, comment="总股本"),
            "pledge_ratio": ColumnDef("DOUBLE", nullable=True, comment="质押比例"),
        },
        composite_indexes=[
            ("end_date",),
            ("end_date", "ts_code"),
            ("ts_code",),
        ],
    )

    def read_data(self, **kwargs: Any):
        frame = self.client.call(
            "pledge_stat",
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or pd.DataFrame(frame).empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
