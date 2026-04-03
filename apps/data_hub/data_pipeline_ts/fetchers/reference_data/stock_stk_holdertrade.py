from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class StkHolderTradeFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=175
    股东增减持, 2000积分
        按公告日期提取增减持数据。
    API params:
        ts_code: 股票代码
        ann_date: 公告日期(YYYYMMDD)
        start_date: 开始日期(YYYYMMDD)
        end_date: 结束日期(YYYYMMDD)
        trade_type: 交易类型
        holder_type: 股东类型
    """
    fields = [
        "ts_code",  # TS代码
        "ann_date",  # 公告日期
        "holder_name",  # 股东名称
        "holder_type",  # 股东类型G高管P个人C公司
        "in_de",  # 类型IN增持DE减持
        "change_vol",  # 变动数量
        "change_ratio",  # 占流通比例(%）
        "after_share",  # 变动后持股
        "after_ratio",  # 变动后占流通比例(%）
        "avg_price",  # 平均价格
        "total_share",  # 持股总数
        "begin_date",  # 增减持开始日期
        "close_date",  # 增减持结束日期
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS代码"),
            "ann_date": ColumnDef("CHAR(8)", nullable=True, comment="公告日期"),
            "holder_name": ColumnDef("TEXT", nullable=True, comment="股东名称"),
            "holder_type": ColumnDef("VARCHAR(8)", nullable=True, comment="股东类型G高管P个人C公司"),
            "in_de": ColumnDef("VARCHAR(8)", nullable=True, comment="类型IN增持DE减持"),
            "change_vol": ColumnDef("DOUBLE", nullable=True, comment="变动数量"),
            "change_ratio": ColumnDef("DOUBLE", nullable=True, comment="占流通比例(%)"),
            "after_share": ColumnDef("DOUBLE", nullable=True, comment="变动后持股"),
            "after_ratio": ColumnDef("DOUBLE", nullable=True, comment="变动后占流通比例(%)"),
            "avg_price": ColumnDef("DOUBLE", nullable=True, comment="平均价格"),
            "total_share": ColumnDef("DOUBLE", nullable=True, comment="持股总数"),
            "begin_date": ColumnDef("CHAR(8)", nullable=True, comment="增减持开始日期"),
            "close_date": ColumnDef("CHAR(8)", nullable=True, comment="增减持结束日期"),
        },
        composite_indexes=[
            ('ann_date',),
            ('ann_date', 'ts_code'),
            ('ts_code',),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call("stk_holdertrade", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
