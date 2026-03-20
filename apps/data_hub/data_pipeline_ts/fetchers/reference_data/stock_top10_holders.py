from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema


class Top10HoldersFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=62
    前十大股东, 2000积分
        按公告日提取前十大股东数据。
    API params:
        ann_date: 公告日期(YYYYMMDD)
        start_date: 开始日期(YYYYMMDD)
        end_date: 结束日期(YYYYMMDD)
    """

    fields = [
        "ts_code",  # TS股票代码
        "ann_date",  # 公告日期
        "end_date",  # 报告期
        "holder_name",  # 股东名称
        "hold_amount",  # 持有数量(股)
        "hold_ratio",  # 占总股本比例(%)
        "hold_float_ratio",  # 占流通股本比例(%)
        "hold_change",  # 持股变动
        "holder_type",  # 股东类型
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "ann_date": ColumnDef("CHAR(8)", nullable=True, comment="公告日期"),
            "end_date": ColumnDef("CHAR(8)", nullable=True, comment="报告期"),
            "holder_name": ColumnDef("VARCHAR(128)", nullable=True, comment="股东名称"),
            "hold_amount": ColumnDef("DOUBLE", nullable=True, comment="持有数量(股)"),
            "hold_ratio": ColumnDef("DOUBLE", nullable=True, comment="占总股本比例(%)"),
            "hold_float_ratio": ColumnDef("DOUBLE", nullable=True, comment="占流通股本比例(%)"),
            "hold_change": ColumnDef("DOUBLE", nullable=True, comment="持股变动"),
            "holder_type": ColumnDef("VARCHAR(128)", nullable=True, comment="股东类型"),
        },
        composite_indexes=[
            ('ann_date',),
            ('ann_date', 'ts_code'),
            ('end_date',),
            ('end_date', 'ts_code'),
            ('ts_code',),
        ],
    )

    def read_data(self, **kwargs: Any):
        frame = self.client.call(
            "top10_holders",
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or pd.DataFrame(frame).empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
