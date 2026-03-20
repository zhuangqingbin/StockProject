from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class MoneyFlowDCFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=170
    个股资金流向(DC), 5000积分
        获取东方财富口径的每日个股资金流向数据。
    API params:
        ts_code: 股票代码
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
    """
    fields = [
        "trade_date",  # 交易日期
        "ts_code",  # 股票代码
        "name",  # 股票名称
        "pct_change",  # 涨跌幅
        "close",  # 最新价
        "net_amount",  # 今日主力净流入额（万元）
        "net_amount_rate",  # 今日主力净流入净占比（%）
        "buy_elg_amount",  # 今日超大单净流入额（万元）
        "buy_elg_amount_rate",  # 今日超大单净流入占比（%）
        "buy_lg_amount",  # 今日大单净流入额（万元）
        "buy_lg_amount_rate",  # 今日大单净流入占比（%）
        "buy_md_amount",  # 今日中单净流入额（万元）
        "buy_md_amount_rate",  # 今日中单净流入占比（%）
        "buy_sm_amount",  # 今日小单净流入额（万元）
        "buy_sm_amount_rate",  # 今日小单净流入占比（%）
    ]
    table_schema = TableSchema(
        columns={
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="股票代码"),
            "name": ColumnDef("VARCHAR(32)", nullable=True, comment="股票名称"),
            "pct_change": ColumnDef("DOUBLE", nullable=True, comment="涨跌幅"),
            "close": ColumnDef("DOUBLE", nullable=True, comment="最新价"),
            "net_amount": ColumnDef("DOUBLE", nullable=True, comment="今日主力净流入额(万元)"),
            "net_amount_rate": ColumnDef("DOUBLE", nullable=True, comment="今日主力净流入净占比(%)"),
            "buy_elg_amount": ColumnDef("DOUBLE", nullable=True, comment="今日超大单净流入额(万元)"),
            "buy_elg_amount_rate": ColumnDef("DOUBLE", nullable=True, comment="今日超大单净流入占比(%)"),
            "buy_lg_amount": ColumnDef("DOUBLE", nullable=True, comment="今日大单净流入额(万元)"),
            "buy_lg_amount_rate": ColumnDef("DOUBLE", nullable=True, comment="今日大单净流入占比(%)"),
            "buy_md_amount": ColumnDef("DOUBLE", nullable=True, comment="今日中单净流入额(万元)"),
            "buy_md_amount_rate": ColumnDef("DOUBLE", nullable=True, comment="今日中单净流入占比(%)"),
            "buy_sm_amount": ColumnDef("DOUBLE", nullable=True, comment="今日小单净流入额(万元)"),
            "buy_sm_amount_rate": ColumnDef("DOUBLE", nullable=True, comment="今日小单净流入占比(%)"),
        },
        composite_indexes=[
            ('trade_date',),
            ('trade_date', 'ts_code'),
            ('ts_code',),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call("moneyflow_dc", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
