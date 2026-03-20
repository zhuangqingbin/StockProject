from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class ShareFloatFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=160
    限售股解禁, 120积分
        按公告日期提取限售股解禁数据。
    API params:
        ts_code: 股票代码
        ann_date: 公告日期(YYYYMMDD)
        float_date: 解禁日期(YYYYMMDD)
        start_date: 开始日期(YYYYMMDD)
        end_date: 结束日期(YYYYMMDD)
    """
    fields = [
        "ts_code",      # TS股票代码
        "ann_date",     # 公告日期
        "float_date",   # 解禁日期
        "float_share",  # 解禁数量
        "float_ratio",  # 解禁比例
        "holder_name",  # 股东名称
        "share_type",   # 股份类型
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "ann_date": ColumnDef("CHAR(8)", nullable=True, comment="公告日期"),
            "float_date": ColumnDef("CHAR(8)", nullable=True, comment="解禁日期"),
            "float_share": ColumnDef("DOUBLE", nullable=True, comment="解禁数量"),
            "float_ratio": ColumnDef("DOUBLE", nullable=True, comment="解禁比例"),
            "holder_name": ColumnDef("VARCHAR(64)", nullable=True, comment="股东名称"),
            "share_type": ColumnDef("VARCHAR(64)", nullable=True, comment="股份类型"),
        },
        composite_indexes=[
            ('ann_date',),
            ('ann_date', 'ts_code'),
            ('ts_code',),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call("share_float", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
