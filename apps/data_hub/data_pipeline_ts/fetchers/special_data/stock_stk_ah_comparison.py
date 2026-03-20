from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema


class StkAHComparisonFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=399
    AH股比价, 5000积分
        获取 A/H 两地上市股票的比价与溢价数据。
    API params:
        hk_code: 港股股票代码
        ts_code: A股股票代码
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
    """

    fields = [
        "hk_code",
        "ts_code",
        "trade_date",
        "hk_name",
        "hk_pct_chg",
        "hk_close",
        "name",
        "close",
        "pct_chg",
        "ah_comparison",
        "ah_premium",
    ]
    table_schema = TableSchema(
        columns={
            "hk_code": ColumnDef("VARCHAR(16)", nullable=True, comment="港股代码"),
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="A股代码"),
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "hk_name": ColumnDef("VARCHAR(32)", nullable=True, comment="港股名称"),
            "hk_pct_chg": ColumnDef("DOUBLE", nullable=True, comment="港股涨跌幅"),
            "hk_close": ColumnDef("DOUBLE", nullable=True, comment="港股收盘价"),
            "name": ColumnDef("VARCHAR(32)", nullable=True, comment="A股名称"),
            "close": ColumnDef("DOUBLE", nullable=True, comment="A股收盘价"),
            "pct_chg": ColumnDef("DOUBLE", nullable=True, comment="A股涨跌幅"),
            "ah_comparison": ColumnDef("DOUBLE", nullable=True, comment="A/H比价"),
            "ah_premium": ColumnDef("DOUBLE", nullable=True, comment="A/H溢价"),
        },
        composite_indexes=[
            ("trade_date",),
            ("trade_date", "ts_code"),
            ("ts_code",),
            ("hk_code",),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call(
            "stk_ah_comparison",
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or pd.DataFrame(frame).empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
