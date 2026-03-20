from __future__ import annotations

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class NewShareFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=123
    IPO新股上市, 120积分
        获取新股上市列表数据，单次最大 2000 条。
    API params:
        start_date: 上网发行开始日期 YYYYMMDD
        end_date: 上网发行结束日期 YYYYMMDD
    """
    fields = [
        "ts_code",       # TS股票代码
        "sub_code",      # 申购代码
        "name",          # 股票名称
        "ipo_date",      # 上网发行日期
        "issue_date",    # 上市日期
        "amount",        # 发行总量
        "market_amount", # 上网发行总量
        "price",         # 发行价格
        "pe",            # 市盈率
        "limit_amount",  # 个人申购上限
        "funds",         # 募集资金
        "ballot",        # 中签率
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "sub_code": ColumnDef("VARCHAR(16)", nullable=True, comment="申购代码"),
            "name": ColumnDef("VARCHAR(32)", nullable=True, comment="股票名称"),
            "ipo_date": ColumnDef("CHAR(8)", nullable=True, comment="上网发行日期"),
            "issue_date": ColumnDef("CHAR(8)", nullable=True, comment="上市日期"),
            "amount": ColumnDef("DOUBLE", nullable=True, comment="发行总量"),
            "market_amount": ColumnDef("DOUBLE", nullable=True, comment="上网发行总量"),
            "price": ColumnDef("DOUBLE", nullable=True, comment="发行价格"),
            "pe": ColumnDef("DOUBLE", nullable=True, comment="市盈率"),
            "limit_amount": ColumnDef("DOUBLE", nullable=True, comment="个人申购上限"),
            "funds": ColumnDef("DOUBLE", nullable=True, comment="募集资金"),
            "ballot": ColumnDef("DOUBLE", nullable=True, comment="中签率"),
        },
        composite_indexes=[
            ('ipo_date',),
            ('ipo_date', 'ts_code'),
            ('ts_code',),
        ],
    )

    def read_data(self, **kwargs):
        frame = self.client.call("new_share", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
