from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class StkHolderNumberFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=166
    股东人数, 600积分
        按公告日期提取股东户数数据。
    API params:
        ts_code: 股票代码
        ann_date: 公告日期(YYYYMMDD)
        enddate: 截止日期(YYYYMMDD)
        start_date: 开始日期(YYYYMMDD)
        end_date: 结束日期(YYYYMMDD)
    """
    fields = [
        "ts_code",     # TS股票代码
        "ann_date",    # 公告日期
        "end_date",    # 截止日期
        "holder_num",  # 股东户数
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "ann_date": ColumnDef("CHAR(8)", nullable=True, comment="公告日期"),
            "end_date": ColumnDef("CHAR(8)", nullable=True, comment="截止日期"),
            "holder_num": ColumnDef("DOUBLE", nullable=True, comment="股东户数"),
        },
        composite_indexes=[
            ('ann_date',),
            ('ann_date', 'ts_code'),
            ('end_date',),
            ('end_date', 'ts_code'),
            ('ts_code',),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call("stk_holdernumber", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
