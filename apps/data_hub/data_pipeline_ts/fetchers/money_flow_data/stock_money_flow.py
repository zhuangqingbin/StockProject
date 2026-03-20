from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class MoneyFlowFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=170
    个股资金流向, 2000积分
        获取沪深两市每日个股资金流向数据。
    API params:
        ts_code: 股票代码
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
    """
    fields = [
        "ts_code",         # TS股票代码
        "trade_date",      # 交易日期
        "buy_sm_vol",      # 小单买入成交量
        "buy_sm_amount",   # 小单买入成交额
        "sell_sm_vol",     # 小单卖出成交量
        "sell_sm_amount",  # 小单卖出成交额
        "buy_md_vol",      # 中单买入成交量
        "buy_md_amount",   # 中单买入成交额
        "sell_md_vol",     # 中单卖出成交量
        "sell_md_amount",  # 中单卖出成交额
        "buy_lg_vol",      # 大单买入成交量
        "buy_lg_amount",   # 大单买入成交额
        "sell_lg_vol",     # 大单卖出成交量
        "sell_lg_amount",  # 大单卖出成交额
        "buy_elg_vol",     # 特大单买入成交量
        "buy_elg_amount",  # 特大单买入成交额
        "sell_elg_vol",    # 特大单卖出成交量
        "sell_elg_amount", # 特大单卖出成交额
        "net_mf_vol",      # 净流入量
        "net_mf_amount",   # 净流入额
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "buy_sm_vol": ColumnDef("INT", nullable=True, comment="小单(5万以下)买入成交量"),
            "buy_sm_amount": ColumnDef("DOUBLE", nullable=True, comment="小单(5万以下)买入成交额"),
            "sell_sm_vol": ColumnDef("INT", nullable=True, comment="小单(5万以下)卖出成交量"),
            "sell_sm_amount": ColumnDef("DOUBLE", nullable=True, comment="小单(5万以下)卖出成交额"),
            "buy_md_vol": ColumnDef("INT", nullable=True, comment="中单(5万-20万)买入成交量"),
            "buy_md_amount": ColumnDef("DOUBLE", nullable=True, comment="中单(5万-20万)买入成交额"),
            "sell_md_vol": ColumnDef("INT", nullable=True, comment="中单(5万-20万)卖出成交量"),
            "sell_md_amount": ColumnDef("DOUBLE", nullable=True, comment="中单(5万-20万)卖出成交额"),
            "buy_lg_vol": ColumnDef("INT", nullable=True, comment="大单(20万-100万)买入成交量"),
            "buy_lg_amount": ColumnDef("DOUBLE", nullable=True, comment="大单(20万-100万)买入成交额"),
            "sell_lg_vol": ColumnDef("INT", nullable=True, comment="大单(20万-100万)卖出成交量"),
            "sell_lg_amount": ColumnDef("DOUBLE", nullable=True, comment="大单(20万-100万)卖出成交额"),
            "buy_elg_vol": ColumnDef("INT", nullable=True, comment="特大单(100万以上)买入成交量"),
            "buy_elg_amount": ColumnDef("DOUBLE", nullable=True, comment="特大单(100万以上)买入成交额"),
            "sell_elg_vol": ColumnDef("INT", nullable=True, comment="特大单(100万以上)卖出成交量"),
            "sell_elg_amount": ColumnDef("DOUBLE", nullable=True, comment="特大单(100万以上)卖出成交额"),
            "net_mf_vol": ColumnDef("INT", nullable=True, comment="净流入量"),
            "net_mf_amount": ColumnDef("DOUBLE", nullable=True, comment="净流入额"),
        },
        composite_indexes=[
            ('trade_date',),
            ('trade_date', 'ts_code'),
            ('ts_code',),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call("moneyflow", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
