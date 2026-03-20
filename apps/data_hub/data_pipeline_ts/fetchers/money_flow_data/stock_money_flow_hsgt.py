from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class MoneyFlowHSGTFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=47
    沪深港通资金流向, 2000积分
        获取沪股通、深股通、港股通每日资金流向数据。
    API params:
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
    """
    fields = [
        "trade_date",  # 交易日期
        "ggt_ss",      # 港股通(沪)净流入
        "ggt_sz",      # 港股通(深)净流入
        "hgt",         # 沪股通净流入
        "sgt",         # 深股通净流入
        "north_money", # 北向资金净流入
        "south_money", # 南向资金净流入
    ]
    table_schema = TableSchema(
        columns={
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "ggt_ss": ColumnDef("DOUBLE", nullable=True, comment="港股通(沪)净流入"),
            "ggt_sz": ColumnDef("DOUBLE", nullable=True, comment="港股通(深)净流入"),
            "hgt": ColumnDef("DOUBLE", nullable=True, comment="沪股通净流入"),
            "sgt": ColumnDef("DOUBLE", nullable=True, comment="深股通净流入"),
            "north_money": ColumnDef("DOUBLE", nullable=True, comment="北向资金净流入"),
            "south_money": ColumnDef("DOUBLE", nullable=True, comment="南向资金净流入"),
        },
        composite_indexes=[
            ('trade_date',),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call("moneyflow_hsgt", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
