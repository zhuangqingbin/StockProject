from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema


class StkSurvFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=275
    机构调研数据, 5000积分
        获取上市公司机构调研记录数据。
    API params:
        ts_code: 股票代码
        trade_date: 调研日期(YYYYMMDD)
        start_date: 调研开始日期
        end_date: 调研结束日期
    """

    fields = [
        "ts_code",
        "name",
        "surv_date",
        "fund_visitors",
        "rece_place",
        "rece_mode",
        "rece_org",
        "org_type",
        "comp_rece",
        "content",
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="股票代码"),
            "name": ColumnDef("VARCHAR(32)", nullable=True, comment="股票名称"),
            "surv_date": ColumnDef("CHAR(8)", nullable=True, comment="调研日期"),
            "fund_visitors": ColumnDef("TEXT", nullable=True, comment="机构参与人员"),
            "rece_place": ColumnDef("VARCHAR(128)", nullable=True, comment="接待地点"),
            "rece_mode": ColumnDef("VARCHAR(64)", nullable=True, comment="接待方式"),
            "rece_org": ColumnDef("TEXT", nullable=True, comment="接待的公司"),
            "org_type": ColumnDef("VARCHAR(64)", nullable=True, comment="接待公司类型"),
            "comp_rece": ColumnDef("TEXT", nullable=True, comment="上市公司接待人员"),
            "content": ColumnDef("TEXT", nullable=True, comment="调研内容"),
        },
        composite_indexes=[
            ("surv_date",),
            ("surv_date", "ts_code"),
            ("ts_code",),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call(
            "stk_surv",
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or pd.DataFrame(frame).empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
