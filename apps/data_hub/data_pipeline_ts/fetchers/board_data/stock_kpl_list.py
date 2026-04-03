from __future__ import annotations

import time
from dataclasses import replace
from typing import Any, ClassVar

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema
from apps.data_hub.data_pipeline_ts.fetchers.client import ClientConfig, TuShareClient

KPL_LIST_TAGS = ("涨停", "炸板", "跌停", "自然涨停", "竞价")
KPL_LIST_FETCH_ATTEMPTS = 2
KPL_LIST_MIN_INTERVAL_SECONDS = 0.35
KPL_LIST_MAX_CALLS_PER_MINUTE = 190
KPL_LIST_RATE_LIMIT_BACKOFF_SECONDS = 60.0
KPL_LIST_RATE_LIMIT_MESSAGE = "每分钟最多访问该接口200次"

class KPLListFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=347
    榜单数据(开盘啦)
        按交易日提取涨停、炸板、跌停等榜单数据。
        fetcher 运行时仅接受 trade_date，并在内部按默认 tag 集合循环拉取后合并。
        5000积分每分钟可以请求200次每天总量1万次，8000积分以上每分钟500次每天总量不限制
    Fetcher params:
        trade_date: 交易日期(YYYYMMDD)
    """
    fields = [
        "ts_code",  # 代码
        "name",  # 名称
        "trade_date",  # 交易时间
        "lu_time",  # 涨停时间
        "ld_time",  # 跌停时间
        "open_time",  # 开板时间
        "last_time",  # 最后涨停时间
        "lu_desc",  # 涨停原因
        "tag",  # 标签
        "theme",  # 板块
        "net_change",  # 主力净额(元)
        "bid_amount",  # 竞价成交额(元)
        "status",  # 状态（N连板）
        "bid_change",  # 竞价净额
        "bid_turnover",  # 竞价换手%
        "lu_bid_vol",  # 涨停委买额
        "pct_chg",  # 涨跌幅%
        "bid_pct_chg",  # 竞价涨幅%
        "rt_pct_chg",  # 实时涨幅%
        "limit_order",  # 封单
        "amount",  # 成交额
        "turnover_rate",  # 换手率%
        "free_float",  # 实际流通
        "lu_limit_order",  # 最大封单
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="代码"),
            "name": ColumnDef("VARCHAR(32)", nullable=True, comment="名称"),
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易时间"),
            "lu_time": ColumnDef("VARCHAR(16)", nullable=True, comment="涨停时间"),
            "ld_time": ColumnDef("VARCHAR(16)", nullable=True, comment="跌停时间"),
            "open_time": ColumnDef("VARCHAR(16)", nullable=True, comment="开板时间"),
            "last_time": ColumnDef("VARCHAR(16)", nullable=True, comment="最后涨停时间"),
            "lu_desc": ColumnDef("TEXT", nullable=True, comment="涨停原因"),
            "tag": ColumnDef("VARCHAR(32)", nullable=True, comment="标签"),
            "theme": ColumnDef("VARCHAR(128)", nullable=True, comment="板块"),
            "net_change": ColumnDef("DOUBLE", nullable=True, comment="主力净额(元)"),
            "bid_amount": ColumnDef("DOUBLE", nullable=True, comment="竞价成交额(元)"),
            "status": ColumnDef("VARCHAR(16)", nullable=True, comment="状态（N连板）"),
            "bid_change": ColumnDef("DOUBLE", nullable=True, comment="竞价净额"),
            "bid_turnover": ColumnDef("DOUBLE", nullable=True, comment="竞价换手%"),
            "lu_bid_vol": ColumnDef("DOUBLE", nullable=True, comment="涨停委买额"),
            "pct_chg": ColumnDef("DOUBLE", nullable=True, comment="涨跌幅%"),
            "bid_pct_chg": ColumnDef("DOUBLE", nullable=True, comment="竞价涨幅%"),
            "rt_pct_chg": ColumnDef("DOUBLE", nullable=True, comment="实时涨幅%"),
            "limit_order": ColumnDef("DOUBLE", nullable=True, comment="封单"),
            "amount": ColumnDef("DOUBLE", nullable=True, comment="成交额"),
            "turnover_rate": ColumnDef("DOUBLE", nullable=True, comment="换手率%"),
            "free_float": ColumnDef("DOUBLE", nullable=True, comment="实际流通"),
            "lu_limit_order": ColumnDef("DOUBLE", nullable=True, comment="最大封单"),
        },
        composite_indexes=[
            ('trade_date',),
            ('trade_date', 'ts_code'),
            ('ts_code',),
            ('trade_date', 'tag'),
        ],
    )
    _shared_client: ClassVar[TuShareClient | None] = None

    @classmethod
    def _default_client(cls) -> TuShareClient:
        if cls._shared_client is None:
            cls._shared_client = TuShareClient(
                config=replace(
                    ClientConfig(),
                    min_interval_seconds=KPL_LIST_MIN_INTERVAL_SECONDS,
                    max_calls_per_minute=KPL_LIST_MAX_CALLS_PER_MINUTE,
                )
            )
        return cls._shared_client

    def __init__(self, client: Any | None = None):
        if client is None:
            client = self._default_client()
        super().__init__(client=client)

    @staticmethod
    def _error_contains_message(error: BaseException, message: str) -> bool:
        current: BaseException | None = error
        while current is not None:
            if message in str(current):
                return True
            current = current.__cause__ or current.__context__
        return False

    @classmethod
    def _is_rate_limit_error(cls, error: BaseException) -> bool:
        return cls._error_contains_message(error, KPL_LIST_RATE_LIMIT_MESSAGE)

    def _read_once(
        self,
        *,
        tag: str,
        trade_date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        params: dict[str, str] = {
            "fields": ",".join(self.fields),
            "tag": tag,
        }
        if trade_date:
            params["trade_date"] = trade_date
        else:
            params["start_date"] = start_date or ""
            params["end_date"] = end_date or ""

        last_error: RuntimeError | None = None
        for attempt in range(KPL_LIST_FETCH_ATTEMPTS):
            try:
                frame = self.client.call("kpl_list", **params)
                if frame is None or frame.empty:
                    return pd.DataFrame(columns=self.fields)
                return pd.DataFrame(frame).reindex(columns=self.fields)
            except RuntimeError as exc:
                last_error = exc
                if self._is_rate_limit_error(exc) and attempt + 1 < KPL_LIST_FETCH_ATTEMPTS:
                    time.sleep(KPL_LIST_RATE_LIMIT_BACKOFF_SECONDS)
                    continue
                raise

        if last_error is not None:
            raise last_error
        return pd.DataFrame(columns=self.fields)

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        trade_date = str(kwargs.get("trade_date", "")).strip()
        start_date = str(kwargs.get("start_date", "")).strip()
        end_date = str(kwargs.get("end_date", "")).strip()
        if not trade_date and not (start_date and end_date):
            raise ValueError("kpl_list fetches require trade_date or start_date/end_date")

        frames: list[pd.DataFrame] = []
        for tag in KPL_LIST_TAGS:
            frame = self._read_once(
                tag=tag,
                trade_date=trade_date or None,
                start_date=start_date or None,
                end_date=end_date or None,
            )
            if frame.empty:
                continue
            frames.append(frame.dropna(axis=1, how="all"))

        if not frames:
            return pd.DataFrame(columns=self.fields)
        return pd.concat(frames, ignore_index=True).reindex(columns=self.fields)
