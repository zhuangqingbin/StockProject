from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class TopInstFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=107
    龙虎榜机构成交明细
        按交易日提取每日机构席位上榜明细。
        单次请求最大返回10000行数据, 可根据参数循环获取全部历史
    API params:
        trade_date: 交易日期(YYYYMMDD)
        ts_code: 股票代码
    """
    fields = [
        "trade_date",  # 交易日期
        "ts_code",  # TS代码
        "exalter",  # 营业部名称
        "side",  # 买卖类型0：买入金额最大的前5名,  1：卖出金额最大的前5名
        "buy",  # 买入额（元）
        "buy_rate",  # 买入占总成交比例
        "sell",  # 卖出额（元）
        "sell_rate",  # 卖出占总成交比例
        "net_buy",  # 净成交额（元）
        "reason",  # 上榜理由
    ]
    table_schema = TableSchema(
        columns={
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS代码"),
            "exalter": ColumnDef("VARCHAR(64)", nullable=True, comment="营业部名称"),
            "side": ColumnDef("TINYINT", nullable=True, comment="买卖类型0:买入金额最大的前5名, 1L卖出金额最大的前5名"),
            "buy": ColumnDef("DOUBLE", nullable=True, comment="买入额(元)"),
            "buy_rate": ColumnDef("DOUBLE", nullable=True, comment="买入占总成交比例"),
            "sell": ColumnDef("DOUBLE", nullable=True, comment="卖出额(元)"),
            "sell_rate": ColumnDef("DOUBLE", nullable=True, comment="卖出占总成交比例"),
            "net_buy": ColumnDef("DOUBLE", nullable=True, comment="净成交额(元)"),
            "reason": ColumnDef("TEXT", nullable=True, comment="上榜理由"),
        },
        composite_indexes=[
            ('trade_date',),
            ('trade_date', 'ts_code'),
            ('ts_code',),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call("top_inst", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
