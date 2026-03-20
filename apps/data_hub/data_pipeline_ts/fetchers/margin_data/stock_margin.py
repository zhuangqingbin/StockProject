from __future__ import annotations

from typing import Any

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema

MARGIN_EXCHANGE_IDS = ("SSE", "SZSE", "BSE")
MARGIN_SINGLE_CALL_ROW_CAP = 4000

class MarginFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=58
    融资融券交易汇总, 2000积分
        获取交易所级别的每日融资融券交易汇总。
    API params:
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
        exchange_id: 交易所标识
    """
    fields = [
        "trade_date",   # 交易日期
        "exchange_id",  # 交易所标识
        "rzye",         # 融资余额
        "rzmre",        # 融资买入额
        "rzche",        # 融资偿还额
        "rqye",         # 融券余量
        "rqmcl",        # 融券卖出量
        "rzrqye",       # 融资融券余额
        "rqyl",         # 融券余量金额
    ]
    table_schema = TableSchema(
        columns={
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "exchange_id": ColumnDef("VARCHAR(32)", nullable=True, comment="交易所标识"),
            "rzye": ColumnDef("DOUBLE", nullable=True, comment="融资余额"),
            "rzmre": ColumnDef("DOUBLE", nullable=True, comment="融资买入额"),
            "rzche": ColumnDef("DOUBLE", nullable=True, comment="融资偿还额"),
            "rqye": ColumnDef("DOUBLE", nullable=True, comment="融券余量"),
            "rqmcl": ColumnDef("DOUBLE", nullable=True, comment="融券卖出量"),
            "rzrqye": ColumnDef("DOUBLE", nullable=True, comment="融资融券余额"),
            "rqyl": ColumnDef("DOUBLE", nullable=True, comment="融券余量金额"),
        },
        composite_indexes=[
            ('trade_date',),
            ('trade_date', 'exchange_id'),
        ],
    )

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        direct_frame = self._read_once(**kwargs)
        if len(direct_frame.index) < MARGIN_SINGLE_CALL_ROW_CAP:
            return direct_frame

        frames: list[pd.DataFrame] = []
        for exchange_id in MARGIN_EXCHANGE_IDS:
            frame = self._read_once(exchange_id=exchange_id, **kwargs)
            if frame.empty:
                continue
            frames.append(frame)

        if not frames:
            return direct_frame
        return pd.concat(frames, ignore_index=True).reindex(columns=self.fields)

    def _read_once(self, **kwargs: Any) -> pd.DataFrame:
        frame = self.client.call(
            "margin",
            fields=",".join(self.fields),
            **kwargs,
        )
        if frame is None or frame.empty:
            return pd.DataFrame(columns=self.fields)
        return pd.DataFrame(frame).reindex(columns=self.fields)
