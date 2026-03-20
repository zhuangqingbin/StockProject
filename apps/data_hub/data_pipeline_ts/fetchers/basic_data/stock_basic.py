from __future__ import annotations

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

class StockBasicFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=25
    公司基础信息, 2000积分
        获取基础信息数据，包括股票代码、名称、上市日期、退市日期等
    API params:
        ts_code: 股票代码
        name: 股票名称
        market: 市场类别 （主板/创业板/科创板/CDR/北交所）
        list_status: 上市状态 L上市 D退市 P暂停上市 G过会未交易, 默认是L
        exchange: 交易所 SSE上交所 SZSE深交所 BSE北交所
        is_hs: 是否沪深港通标的, N否 H沪股通 S深股通
    """
    fields = [
        "ts_code",  # TS代码
        "symbol",  # 股票代码
        "name",  # 股票名称
        "area",  # 地域
        "industry",  # 所属行业
        "fullname",  # 股票全称
        "enname",  # 英文全称
        "cnspell",  # 拼音缩写
        "market",  # 市场类型（主板/创业板/科创板/CDR）
        "exchange",  # 交易所代码
        "curr_type",  # 交易货币
        "list_status",  # 上市状态 L上市 D退市 G过会未交易 P暂停上市
        "list_date",  # 上市日期
        "delist_date",  # 退市日期
        "is_hs",  # 是否沪深港通标的，N否 H沪股通 S深股通
        "act_name",  # 实控人名称
        "act_ent_type",  # 实控人企业性质
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS代码"),
            "symbol": ColumnDef("VARCHAR(255)", nullable=True, comment="股票代码"),
            "name": ColumnDef("VARCHAR(255)", nullable=True, comment="股票名称"),
            "area": ColumnDef("VARCHAR(255)", nullable=True, comment="地域"),
            "industry": ColumnDef("VARCHAR(255)", nullable=True, comment="所属行业"),
            "fullname": ColumnDef("VARCHAR(128)", nullable=True, comment="股票全称"),
            "enname": ColumnDef("VARCHAR(128)", nullable=True, comment="英文全称"),
            "cnspell": ColumnDef("VARCHAR(128)", nullable=True, comment="拼音缩写"),
            "market": ColumnDef("VARCHAR(32)", nullable=True, comment="市场类型（主板/创业板/科创板/CDR）"),
            "exchange": ColumnDef("VARCHAR(32)", nullable=True, comment="交易所代码"),
            "curr_type": ColumnDef("VARCHAR(128)", nullable=True, comment="交易货币"),
            "list_status": ColumnDef("VARCHAR(128)", nullable=True, comment="上市状态 L上市 D退市 G过会未交易 P暂停上市"),
            "list_date": ColumnDef("CHAR(8)", nullable=True, comment="上市日期"),
            "delist_date": ColumnDef("CHAR(8)", nullable=True, comment="退市日期"),
            "is_hs": ColumnDef("VARCHAR(8)", nullable=True, comment="是否沪深港通标的，N否 H沪股通 S深股通"),
            "act_name": ColumnDef("VARCHAR(128)", nullable=True, comment="实控人名称"),
            "act_ent_type": ColumnDef("VARCHAR(128)", nullable=True, comment="实控人企业性质"),
        },
        composite_indexes=[
            ('ts_code',),
        ],
    )

    def read_data(self, **kwargs):
        frame = self.client.call("stock_basic", 
            exchange="",
            list_status="L",
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
