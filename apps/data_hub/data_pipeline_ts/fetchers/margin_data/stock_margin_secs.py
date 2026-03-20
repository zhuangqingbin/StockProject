from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

MARGIN_SECS_EXCHANGES = ("SSE", "SZSE", "BSE")
MARGIN_SECS_SINGLE_CALL_ROW_CAP = 6000

class MarginSecsFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=326
    融资融券标的(盘前), 2000积分
        获取沪深京三大交易所盘前融资融券标的列表。
    API params:
        trade_date: 交易日期(YYYYMMDD)
        ts_code: 股票代码
        exchange: 交易所标识
        start_date: 开始日期
        end_date: 结束日期
    """
    fields = [
        "trade_date",  # 交易日期
        "ts_code",     # TS股票代码
        "name",        # 股票名称
        "exchange",    # 交易所标识
    ]
    table_schema = TableSchema(
        columns={
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="TS股票代码"),
            "name": ColumnDef("VARCHAR(32)", nullable=True, comment="股票名称"),
            "exchange": ColumnDef("VARCHAR(32)", nullable=True, comment="交易所标识"),
        },
        composite_indexes=[
            ('trade_date',),
            ('trade_date', 'ts_code'),
            ('ts_code',),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        direct_frame = self._read_once(**kwargs)
        if len(direct_frame.index) < MARGIN_SECS_SINGLE_CALL_ROW_CAP:
            return direct_frame

        frames: list[pd.DataFrame] = []
        for exchange in MARGIN_SECS_EXCHANGES:
            frame = self._read_once(exchange=exchange, **kwargs)
            if frame.empty:
                continue
            frames.append(frame)

        if not frames:
            return direct_frame
        return pd.concat(frames, ignore_index=True).reindex(columns=self.fields)

    def _read_once(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call(
            "margin_secs",
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
