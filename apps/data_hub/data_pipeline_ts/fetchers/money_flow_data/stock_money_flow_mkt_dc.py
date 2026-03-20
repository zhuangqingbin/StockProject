from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema


class MoneyFlowMktDCFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=345
    大盘资金流向(DC), 6000积分
        获取东方财富口径的每日大盘资金流向数据。
    API params:
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
    """

    fields = [
        "trade_date",  # 交易日期
        "close_sh",  # 上证收盘价(点)
        "pct_change_sh",  # 上证涨跌幅(%)
        "close_sz",  # 深证收盘价(点)
        "pct_change_sz",  # 深证涨跌幅(%)
        "net_amount",  # 今日主力净流入净额(元)
        "net_amount_rate",  # 今日主力净流入净占比%
        "buy_elg_amount",  # 今日超大单净流入净额(元)
        "buy_elg_amount_rate",  # 今日超大单净流入净占比%
        "buy_lg_amount",  # 今日大单净流入净额(元)
        "buy_lg_amount_rate",  # 今日大单净流入净占比%
        "buy_md_amount",  # 今日中单净流入净额(元)
        "buy_md_amount_rate",  # 今日中单净流入净占比%
        "buy_sm_amount",  # 今日小单净流入净额(元)
        "buy_sm_amount_rate",  # 今日小单净流入净占比%
    ]
    table_schema = TableSchema(
        columns={
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "close_sh": ColumnDef("DOUBLE", nullable=True, comment="上证收盘价(点)"),
            "pct_change_sh": ColumnDef("DOUBLE", nullable=True, comment="上证涨跌幅(%)"),
            "close_sz": ColumnDef("DOUBLE", nullable=True, comment="深证收盘价(点)"),
            "pct_change_sz": ColumnDef("DOUBLE", nullable=True, comment="深证涨跌幅(%)"),
            "net_amount": ColumnDef("DOUBLE", nullable=True, comment="今日主力净流入净额(元)"),
            "net_amount_rate": ColumnDef("DOUBLE", nullable=True, comment="今日主力净流入净占比%"),
            "buy_elg_amount": ColumnDef("DOUBLE", nullable=True, comment="今日超大单净流入净额(元)"),
            "buy_elg_amount_rate": ColumnDef("DOUBLE", nullable=True, comment="今日超大单净流入净占比%"),
            "buy_lg_amount": ColumnDef("DOUBLE", nullable=True, comment="今日大单净流入净额(元)"),
            "buy_lg_amount_rate": ColumnDef("DOUBLE", nullable=True, comment="今日大单净流入净占比%"),
            "buy_md_amount": ColumnDef("DOUBLE", nullable=True, comment="今日中单净流入净额(元)"),
            "buy_md_amount_rate": ColumnDef("DOUBLE", nullable=True, comment="今日中单净流入净占比%"),
            "buy_sm_amount": ColumnDef("DOUBLE", nullable=True, comment="今日小单净流入净额(元)"),
            "buy_sm_amount_rate": ColumnDef("DOUBLE", nullable=True, comment="今日小单净流入净占比%"),
        },
        composite_indexes=[
            ("trade_date",),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call(
            "moneyflow_mkt_dc",
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
