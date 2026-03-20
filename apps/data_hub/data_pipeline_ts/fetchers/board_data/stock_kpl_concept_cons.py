from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class KPLConceptConsFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=351
    题材成分(开盘啦)
        按交易日提取开盘啦概念题材成分股。
    API params:
        trade_date: 交易日期(YYYYMMDD)
        ts_code: 股票代码
        con_code: 题材代码
    """
    fields = [
        "ts_code",  # 题材ID
        "name",  # 题材名称
        "con_name",  # 股票名称
        "con_code",  # 股票代码
        "trade_date",  # 交易日期
        "desc",  # 描述
        "hot_num",  # 人气值
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="题材ID"),
            "name": ColumnDef("VARCHAR(32)", nullable=True, comment="题材名称"),
            "con_name": ColumnDef("VARCHAR(32)", nullable=True, comment="股票名称"),
            "con_code": ColumnDef("VARCHAR(32)", nullable=True, comment="股票代码"),
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "desc": ColumnDef("TEXT", nullable=True, comment="描述"),
            "hot_num": ColumnDef("INT", nullable=True, comment="人气值"),
        },
        composite_indexes=[
            ('trade_date',),
            ('trade_date', 'ts_code'),
            ('ts_code',),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call("kpl_concept_cons", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
