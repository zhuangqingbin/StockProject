from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class ForecastVipFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=45
    业绩预告(VIP), 5000积分
        按公告日期提取全市场业绩预告数据。
    API params:
        ts_code: 股票代码
        ann_date: 公告日期(YYYYMMDD)
        start_date: 公告开始日期(YYYYMMDD)
        end_date: 公告结束日期(YYYYMMDD)
        period: 报告期(YYYYMMDD)
        type: 预告类型
    """
    fields = [
        "ts_code",  # TS股票代码
        "ann_date",  # 公告日期
        "end_date",  # 报告期
        "type",  # 业绩预告类型(预增/预减/扭亏/首亏/续亏/续盈/略增/略减)
        "p_change_min",  # 预告净利润变动幅度下限（%）
        "p_change_max",  # 预告净利润变动幅度上限（%）
        "net_profit_min",  # 预告净利润下限（万元）
        "net_profit_max",  # 预告净利润上限（万元）
        "last_parent_net",  # 上年同期归属母公司净利润
        "first_ann_date",  # 首次公告日
        "summary",  # 业绩预告摘要
        "change_reason",  # 业绩变动原因
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "ann_date": ColumnDef("CHAR(8)", nullable=True, comment="公告日期"),
            "end_date": ColumnDef("CHAR(8)", nullable=True, comment="报告期"),
            "type": ColumnDef("VARCHAR(16)", nullable=True, comment="业绩预告类型(预增/预减/扭亏/首亏/续亏/续盈/略增/略减)"),
            "p_change_min": ColumnDef("DOUBLE", nullable=True, comment="预告净利润变动幅度下限(%)"),
            "p_change_max": ColumnDef("DOUBLE", nullable=True, comment="预告净利润变动幅度上限(%)"),
            "net_profit_min": ColumnDef("DOUBLE", nullable=True, comment="预告净利润下限(万元)"),
            "net_profit_max": ColumnDef("DOUBLE", nullable=True, comment="预告净利润上限(万元)"),
            "last_parent_net": ColumnDef("DOUBLE", nullable=True, comment="上年同期归属母公司净利润"),
            "first_ann_date": ColumnDef("CHAR(8)", nullable=True, comment="首次公告日"),
            "summary": ColumnDef("TEXT", nullable=True, comment="业绩预告摘要"),
            "change_reason": ColumnDef("TEXT", nullable=True, comment="业绩变动原因"),
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
        frame = self.client.call("forecast_vip", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
