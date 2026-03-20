from __future__ import annotations

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class TradeCalFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=26
    交易日历, 2000积分
        获取各大交易所交易日历数据,默认提取的是上交所
    API params:
        exchange: 交易所 SSE上交所,SZSE深交所,CFFEX 中金所,SHFE 上期所,CZCE 郑商所,DCE 大商所,INE 上能源
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
        is_open: 是否交易 '0'休市 '1'交易
    """
    fields = [
        "exchange",  # 交易所 同参数部分描述
        "cal_date",  # 日历日期
        "is_open",  # 是否交易 0休市 1交易
        "pretrade_date",  # 上一个交易日
    ]
    table_schema = TableSchema(
        columns={
            "exchange": ColumnDef("VARCHAR(32)", nullable=True, comment="交易所 同参数部分描述"),
            "cal_date": ColumnDef("CHAR(8)", nullable=True, comment="日历日期"),
            "is_open": ColumnDef("TINYINT", nullable=True, comment="是否交易 0休市 1交易"),
            "pretrade_date": ColumnDef("CHAR(8)", nullable=True, comment="上一个交易日"),
        },
        composite_indexes=[
            ('cal_date',),
        ],
    )

    def read_data(self, start_date, end_date, **kwargs):
        frame = self.client.call("trade_cal", 
            exchange="",
            start_date=start_date,
            end_date=end_date,
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
