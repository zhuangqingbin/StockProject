from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class TopListFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=106
    龙虎榜每日明细
        按交易日提取每日上榜个股明细。
        单次请求返回最大10000行数据，可通过参数循环获取全部历史
    API params:
        trade_date: 交易日期(YYYYMMDD)
        ts_code: 股票代码
    """
    fields = [
        "trade_date",    # 交易日期
        "ts_code",       # TS股票代码
        "name",          # 股票名称
        "close",         # 收盘价
        "pct_change",    # 涨跌幅
        "turnover_rate", # 换手率
        "amount",        # 成交额
        "l_sell",        # 龙虎榜卖出额
        "l_buy",         # 龙虎榜买入额
        "l_amount",      # 龙虎榜成交额
        "net_amount",    # 净买入额
        "net_rate",      # 净买入占比
        "amount_rate",   # 龙虎榜成交额占比
        "float_values",  # 当日流通市值
        "reason",        # 上榜原因
    ]
    table_schema = TableSchema(
        columns={
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "name": ColumnDef("VARCHAR(32)", nullable=True, comment="股票名称"),
            "close": ColumnDef("DOUBLE", nullable=True, comment="收盘价"),
            "pct_change": ColumnDef("DOUBLE", nullable=True, comment="涨跌幅"),
            "turnover_rate": ColumnDef("DOUBLE", nullable=True, comment="换手率"),
            "amount": ColumnDef("DOUBLE", nullable=True, comment="成交额"),
            "l_sell": ColumnDef("DOUBLE", nullable=True, comment="龙虎榜卖出额"),
            "l_buy": ColumnDef("DOUBLE", nullable=True, comment="龙虎榜买入额"),
            "l_amount": ColumnDef("DOUBLE", nullable=True, comment="龙虎榜成交额"),
            "net_amount": ColumnDef("DOUBLE", nullable=True, comment="净买入额"),
            "net_rate": ColumnDef("DOUBLE", nullable=True, comment="净买入占比"),
            "amount_rate": ColumnDef("DOUBLE", nullable=True, comment="龙虎榜成交额占比"),
            "float_values": ColumnDef("DOUBLE", nullable=True, comment="当日流通市值"),
            "reason": ColumnDef("TEXT", nullable=True, comment="上榜原因"),
        },
        composite_indexes=[
            ('trade_date',),
            ('trade_date', 'ts_code'),
            ('ts_code',),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call("top_list", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        result = pd.DataFrame(frame).reindex(columns=self.fields)
        return result.drop_duplicates(subset=["trade_date", "ts_code", "reason"], keep="first").reset_index(drop=True)
