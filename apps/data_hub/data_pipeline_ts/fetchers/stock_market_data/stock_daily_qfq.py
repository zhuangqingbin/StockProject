from __future__ import annotations

from typing import Any

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema



class StockDailyQfqFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=109
    A股日线前复权行情
        使用 pro_bar 固定 asset='E'、adj='qfq'、freq='D' 获取前复权日线。
    API params:
        ts_code: 股票代码
        start_date: 开始日期(YYYYMMDD)
        end_date: 结束日期(YYYYMMDD)
    """

    fields = [
        "ts_code",    # TS股票代码
        "trade_date", # 交易日期
        "open",       # 开盘价
        "high",       # 最高价
        "low",        # 最低价
        "close",      # 收盘价
        "pre_close",  # 昨收价
        "change",     # 涨跌额
        "pct_chg",    # 涨跌幅
        "vol",        # 成交量
        "amount",     # 成交额
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "open": ColumnDef("DOUBLE", nullable=True, comment="开盘价"),
            "high": ColumnDef("DOUBLE", nullable=True, comment="最高价"),
            "low": ColumnDef("DOUBLE", nullable=True, comment="最低价"),
            "close": ColumnDef("DOUBLE", nullable=True, comment="收盘价"),
            "pre_close": ColumnDef("DOUBLE", nullable=True, comment="昨收价"),
            "change": ColumnDef("DOUBLE", nullable=True, comment="涨跌额"),
            "pct_chg": ColumnDef("DOUBLE", nullable=True, comment="涨跌幅"),
            "vol": ColumnDef("DOUBLE", nullable=True, comment="成交量"),
            "amount": ColumnDef("DOUBLE", nullable=True, comment="成交额"),
        },
        composite_indexes=[
            ("trade_date",),
            ("trade_date", "ts_code"),
            ("ts_code",),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        if "ts_code" in kwargs:
            raise ValueError("stock_daily_qfq fetches require stock_codes")

        stock_codes = kwargs.pop("stock_codes", None)
        trade_date = kwargs.pop("trade_date", None)
        start_date = kwargs.pop("start_date", None) or trade_date
        end_date = kwargs.pop("end_date", None) or trade_date

        if not start_date and end_date:
            start_date = end_date
        if not end_date and start_date:
            end_date = start_date
        if not start_date or not end_date:
            raise ValueError("stock_daily_qfq fetches require trade_date or start_date/end_date")

        return self.fanout_by_stock_codes(
            stock_codes=stock_codes,
            stock_basic_statuses=("L",), # 上市状态 L上市 D退市 G过会未交易 P暂停上市
            columns=self.fields,
            fetch_one=lambda stock_code: self.client.pro_bar(
                ts_code=stock_code,
                asset="E",  # E股票 I沪深指数 C数字货币 FT期货 FD基金 O期权 CB可转债
                adj="qfq",  # None未复权 qfq前复权 hfq后复权 
                freq="D",   # D日频 W周频 M月频
                start_date=start_date,
                end_date=end_date,
            ),
        )
