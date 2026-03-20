from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class RepurchaseFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=124
    股票回购, 600积分
        按公告日期提取回购数据。
    API params:
        ann_date: 公告日期(YYYYMMDD)
        start_date: 开始日期(YYYYMMDD)
        end_date: 结束日期(YYYYMMDD)
    """
    fields = [
        "ts_code",     # TS股票代码
        "ann_date",    # 公告日期
        "end_date",    # 回购截止日期
        "proc",        # 回购进度
        "exp_date",    # 过期日期
        "vol",         # 回购数量
        "amount",      # 回购金额
        "high_limit",  # 回购价格上限
        "low_limit",   # 回购价格下限
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "ann_date": ColumnDef("CHAR(8)", nullable=True, comment="公告日期"),
            "end_date": ColumnDef("CHAR(8)", nullable=True, comment="回购截止日期"),
            "proc": ColumnDef("VARCHAR(64)", nullable=True, comment="回购进度"),
            "exp_date": ColumnDef("CHAR(8)", nullable=True, comment="过期日期"),
            "vol": ColumnDef("DOUBLE", nullable=True, comment="回购数量"),
            "amount": ColumnDef("DOUBLE", nullable=True, comment="回购金额"),
            "high_limit": ColumnDef("DOUBLE", nullable=True, comment="回购价格上限"),
            "low_limit": ColumnDef("DOUBLE", nullable=True, comment="回购价格下限"),
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
        frame = self.client.call("repurchase", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
