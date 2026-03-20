from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class MarginDetailFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=59
    融资融券交易明细, 2000积分
        获取每日个股融资融券明细。
    API params:
        trade_date: 交易日期(YYYYMMDD)
        ts_code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
    """
    fields = [
        "trade_date",  # 交易日期
        "ts_code",     # TS股票代码
        "name",        # 股票名称
        "rzye",        # 融资余额
        "rqye",        # 融券余量
        "rzmre",       # 融资买入额
        "rqyl",        # 融券余量金额
        "rzche",       # 融资偿还额
        "rqchl",       # 融券偿还量
        "rqmcl",       # 融券卖出量
        "rzrqye",      # 融资融券余额
    ]
    table_schema = TableSchema(
        columns={
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "name": ColumnDef("VARCHAR(32)", nullable=True, comment="股票名称"),
            "rzye": ColumnDef("DOUBLE", nullable=True, comment="融资余额"),
            "rqye": ColumnDef("DOUBLE", nullable=True, comment="融券余量"),
            "rzmre": ColumnDef("DOUBLE", nullable=True, comment="融资买入额"),
            "rqyl": ColumnDef("DOUBLE", nullable=True, comment="融券余量金额"),
            "rzche": ColumnDef("DOUBLE", nullable=True, comment="融资偿还额"),
            "rqchl": ColumnDef("DOUBLE", nullable=True, comment="融券偿还量"),
            "rqmcl": ColumnDef("DOUBLE", nullable=True, comment="融券卖出量"),
            "rzrqye": ColumnDef("DOUBLE", nullable=True, comment="融资融券余额"),
        },
        composite_indexes=[
            ('trade_date',),
            ('trade_date', 'ts_code'),
            ('ts_code',),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call("margin_detail", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
