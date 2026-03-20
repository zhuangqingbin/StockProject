from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

LIMIT_LIST_D_EXCHANGES = ("SH", "SZ", "BJ")
LIMIT_LIST_D_SINGLE_CALL_ROW_CAP = 2500

class LimitListDFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=298
    涨跌停和炸板数据
        按交易日提取每日涨停、跌停、炸板明细。
        数据从2020年开始(不提供ST股票的统计)单次最大可以获取2500条数据, 可通过日期或者股票循环提取
    API params:
        trade_date: 交易日期(YYYYMMDD)
        ts_code: 股票代码
        limit_type: 涨跌停类型
        exchange: 交易所
        start_date: 开始日期(YYYYMMDD)
        end_date: 结束日期(YYYYMMDD)
    """
    fields = [
        "trade_date",  # 交易日期
        "ts_code",  # 股票代码
        "industry",  # 所属行业
        "name",  # 股票名称
        "close",  # 收盘价
        "pct_chg",  # 涨跌幅
        "amount",  # 成交额
        "limit_amount",  # 板上成交金额(成交价格为该股票跌停价的所有成交额的总和, 涨停无此数据)
        "float_mv",  # 流通市值
        "total_mv",  # 总市值
        "turnover_ratio",  # 换手率
        "fd_amount",  # 封单金额（以涨停价买入挂单的资金总量）
        "first_time",  # 首次封板时间（跌停无此数据）
        "last_time",  # 最后封板时间
        "open_times",  # 炸板次数(跌停为开板次数)
        "up_stat",  # 涨停统计（N/T T天有N次涨停）
        "limit_times",  # 连板数（个股连续封板数量）
        "limit",  # D跌停U涨停Z炸板
    ]
    table_schema = TableSchema(
        columns={
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="股票代码"),
            "industry": ColumnDef("VARCHAR(16)", nullable=True, comment="所属行业"),
            "name": ColumnDef("VARCHAR(32)", nullable=True, comment="股票名称"),
            "close": ColumnDef("DOUBLE", nullable=True, comment="收盘价"),
            "pct_chg": ColumnDef("DOUBLE", nullable=True, comment="涨跌幅"),
            "amount": ColumnDef("DOUBLE", nullable=True, comment="成交额"),
            "limit_amount": ColumnDef("DOUBLE", nullable=True, comment="板上成交金额(成交价格为该股票跌停价的所有成交额的总和, 涨停无此数据)"),
            "float_mv": ColumnDef("DOUBLE", nullable=True, comment="流通市值"),
            "total_mv": ColumnDef("DOUBLE", nullable=True, comment="总市值"),
            "turnover_ratio": ColumnDef("DOUBLE", nullable=True, comment="换手率"),
            "fd_amount": ColumnDef("DOUBLE", nullable=True, comment="封单金额（以涨停价买入挂单的资金总量）"),
            "first_time": ColumnDef("VARCHAR(32)", nullable=True, comment="首次封板时间(跌停无此数据)"),
            "last_time": ColumnDef("VARCHAR(32)", nullable=True, comment="最后封板时间"),
            "open_times": ColumnDef("INT", nullable=True, comment="炸板次数(跌停为开板次数)"),
            "up_stat": ColumnDef("VARCHAR(32)", nullable=True, comment="涨停统计(N/T T天有N次涨停)"),
            "limit_times": ColumnDef("INT", nullable=True, comment="连板数(个股连续封板数量)"),
            "limit": ColumnDef("VARCHAR(16)", nullable=True, comment="D跌停U涨停Z炸板"),
        },
        composite_indexes=[
            ('trade_date',),
            ('trade_date', 'ts_code'),
            ('ts_code',),
        ],
    )

    def _read_once(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call("limit_list_d", 
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        direct_frame = self._read_once(**kwargs)
        if len(direct_frame.index) < LIMIT_LIST_D_SINGLE_CALL_ROW_CAP:
            return direct_frame

        frames: list[pd.DataFrame] = []
        for exchange in LIMIT_LIST_D_EXCHANGES:
            frame = self._read_once(exchange=exchange, **kwargs)
            if frame.empty:
                continue
            frames.append(frame)

        if not frames:
            return direct_frame
        return pd.concat(frames, ignore_index=True).reindex(columns=self.fields)
