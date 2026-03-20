from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class SLBLenFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=331
    转融资交易汇总, 2000积分
        获取转融通融资每日交易汇总。
    API params:
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
    """
    fields = [
        "trade_date",   # 交易日期
        "ob",           # 期初余额
        "auc_amount",   # 竞价成交金额
        "repo_amount",  # 约定申报成交金额
        "repay_amount", # 偿还金额
        "cb",           # 期末余额
    ]
    table_schema = TableSchema(
        columns={
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "ob": ColumnDef("DOUBLE", nullable=True, comment="期初余额"),
            "auc_amount": ColumnDef("DOUBLE", nullable=True, comment="竞价成交金额"),
            "repo_amount": ColumnDef("DOUBLE", nullable=True, comment="约定申报成交金额"),
            "repay_amount": ColumnDef("DOUBLE", nullable=True, comment="偿还金额"),
            "cb": ColumnDef("DOUBLE", nullable=True, comment="期末余额"),
        },
        composite_indexes=[
            ('trade_date',),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call("slb_len", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
