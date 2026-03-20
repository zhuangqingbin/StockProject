from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class DisclosureDateFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=162
    财报披露日期表, 500积分
        按公告日期提取财报披露计划和实际披露日期。
    API params:
        ts_code: 股票代码
        end_date: 报告期(YYYYMMDD)
        pre_date: 预计披露日期(YYYYMMDD)
        ann_date: 公告日期(YYYYMMDD)
        actual_date: 实际披露日期(YYYYMMDD)
    """
    fields = [
        "ts_code",     # TS股票代码
        "ann_date",    # 公告日期
        "end_date",    # 报告期
        "pre_date",    # 预计披露日期
        "actual_date", # 实际披露日期
        "modify_date", # 披露日期修正记录
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "ann_date": ColumnDef("CHAR(8)", nullable=True, comment="公告日期"),
            "end_date": ColumnDef("CHAR(8)", nullable=True, comment="报告期"),
            "pre_date": ColumnDef("CHAR(8)", nullable=True, comment="预计披露日期"),
            "actual_date": ColumnDef("CHAR(8)", nullable=True, comment="实际披露日期"),
            "modify_date": ColumnDef("CHAR(8)", nullable=True, comment="披露日期修正记录"),
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
        frame = self.client.call("disclosure_date", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
