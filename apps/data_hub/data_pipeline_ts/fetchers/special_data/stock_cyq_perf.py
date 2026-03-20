from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema


class CyqPerfFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=293
    每日筹码及胜率, 5000积分
        支持直接按 trade_date 提取全市场筹码平均成本和胜率数据。
    API params:
        trade_date: 交易日期(YYYYMMDD)
        ts_code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
    """

    fields = [
        "ts_code",
        "trade_date",
        "his_low",
        "his_high",
        "cost_5pct",
        "cost_15pct",
        "cost_50pct",
        "cost_85pct",
        "cost_95pct",
        "weight_avg",
        "winner_rate",
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="股票代码"),
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "his_low": ColumnDef("DOUBLE", nullable=True, comment="历史最低价"),
            "his_high": ColumnDef("DOUBLE", nullable=True, comment="历史最高价"),
            "cost_5pct": ColumnDef("DOUBLE", nullable=True, comment="5分位成本"),
            "cost_15pct": ColumnDef("DOUBLE", nullable=True, comment="15分位成本"),
            "cost_50pct": ColumnDef("DOUBLE", nullable=True, comment="50分位成本"),
            "cost_85pct": ColumnDef("DOUBLE", nullable=True, comment="85分位成本"),
            "cost_95pct": ColumnDef("DOUBLE", nullable=True, comment="95分位成本"),
            "weight_avg": ColumnDef("DOUBLE", nullable=True, comment="加权平均成本"),
            "winner_rate": ColumnDef("DOUBLE", nullable=True, comment="胜率"),
        },
        composite_indexes=[
            ("trade_date",),
            ("trade_date", "ts_code"),
            ("ts_code",),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call(
            "cyq_perf",
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or pd.DataFrame(frame).empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
