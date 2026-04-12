from __future__ import annotations

import time
from dataclasses import replace
from typing import Any

from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema
from apps.data_hub.data_pipeline_ts.fetchers.client import ClientConfig, TuShareClient
from shared.stock_core.config import get_env, get_int


CYQ_CHIPS_FETCH_ATTEMPTS = 2                 # 控的是“重试次数”
CYQ_CHIPS_MIN_INTERVAL_SECONDS = 0.32        # 控的是“单次请求之间的最小间隔”
CYQ_CHIPS_MAX_CALLS_PER_MINUTE = 190         # 控的是“每分钟最多访问该接口的次数”
CYQ_CHIPS_RATE_LIMIT_BACKOFF_SECONDS = 60.0  # 控的是“如果达到限制，等待多久后重试”
CYQ_CHIPS_NO_DATA_MESSAGE = "指定数据不存在"
CYQ_CHIPS_RATE_LIMIT_MESSAGE = "每分钟最多访问该接口200次"
CYQ_CHIPS_MIN_INTERVAL_ENV = "TS_CYQ_CHIPS_MIN_INTERVAL_SECONDS"
CYQ_CHIPS_MAX_CALLS_ENV = "TS_CYQ_CHIPS_MAX_CALLS_PER_MINUTE"


def _resolve_cyq_chips_min_interval_seconds() -> float:
    raw_value = get_env(CYQ_CHIPS_MIN_INTERVAL_ENV)
    if not raw_value:
        return CYQ_CHIPS_MIN_INTERVAL_SECONDS
    try:
        return float(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"Environment variable {CYQ_CHIPS_MIN_INTERVAL_ENV} must be a float, got {raw_value!r}"
        ) from exc


def _resolve_cyq_chips_max_calls_per_minute() -> int:
    return get_int(CYQ_CHIPS_MAX_CALLS_ENV, CYQ_CHIPS_MAX_CALLS_PER_MINUTE)


class CyqChipsFetch(BaseFetcher):
    """
    API: https://tushare.pro/document/2?doc_id=294
    每日筹码分布, 5000积分
        trade_date 调度时内部遍历全市场股票代码，因为接口要求 ts_code。
    API params:
        ts_code: 股票代码
        trade_date: 交易日期(YYYYMMDD)
        start_date: 开始日期
        end_date: 结束日期
    """

    fields = [
        "ts_code",
        "trade_date",
        "price",
        "percent",
    ]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=True, comment="股票代码"),
            "trade_date": ColumnDef("CHAR(8)", nullable=True, comment="交易日期"),
            "price": ColumnDef("DOUBLE", nullable=True, comment="成本价格"),
            "percent": ColumnDef("DOUBLE", nullable=True, comment="价格占比"),
        },
        composite_indexes=[
            ("trade_date",),
            ("trade_date", "ts_code"),
            ("ts_code",),
        ],
    )

    def __init__(self, client: Any | None = None):
        if client is None:
            client = TuShareClient(
                config=replace(
                    ClientConfig(),
                    min_interval_seconds=_resolve_cyq_chips_min_interval_seconds(),
                    max_calls_per_minute=_resolve_cyq_chips_max_calls_per_minute(),
                )
            )
        super().__init__(client=client)

    @staticmethod
    def _error_contains_message(error: BaseException, message: str) -> bool:
        current: BaseException | None = error
        while current is not None:
            if message in str(current):
                return True
            current = current.__cause__ or current.__context__
        return False

    @staticmethod
    def _is_no_data_error(error: BaseException) -> bool:
        return CyqChipsFetch._error_contains_message(error, CYQ_CHIPS_NO_DATA_MESSAGE)

    @staticmethod
    def _is_rate_limit_error(error: BaseException) -> bool:
        return CyqChipsFetch._error_contains_message(error, CYQ_CHIPS_RATE_LIMIT_MESSAGE)

    def _fetch_one_stock_code(
        self,
        stock_code: str,
        *,
        start_date: str,
        end_date: str,
    ) -> Any:
        last_error: Exception | None = None
        for attempt in range(CYQ_CHIPS_FETCH_ATTEMPTS):
            try:
                return self.client.call(
                    "cyq_chips",
                    ts_code=stock_code,
                    fields=",".join(self.fields),
                    start_date=start_date,
                    end_date=end_date,
                )
            except RuntimeError as exc:
                if self._is_no_data_error(exc):
                    return None
                last_error = exc
                if self._is_rate_limit_error(exc) and attempt + 1 < CYQ_CHIPS_FETCH_ATTEMPTS:
                    time.sleep(CYQ_CHIPS_RATE_LIMIT_BACKOFF_SECONDS)

        if last_error is not None:
            raise last_error
        return None

    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        if "ts_code" in kwargs:
            raise ValueError("cyq_chips fetches require stock_codes")

        stock_codes = kwargs.pop("stock_codes", None)
        trade_date = kwargs.pop("trade_date", None)
        start_date = kwargs.pop("start_date", None) or trade_date
        end_date = kwargs.pop("end_date", None) or trade_date

        if not start_date and end_date:
            start_date = end_date
        if not end_date and start_date:
            end_date = start_date
        if not start_date or not end_date:
            raise ValueError("cyq_chips fetches require trade_date or start_date/end_date")

        return self.fanout_by_stock_codes(
            stock_codes=stock_codes,
            stock_basic_statuses=("L",), # 上市状态 L上市 D退市 G过会未交易 P暂停上市
            columns=self.fields,
            fetch_one=lambda stock_code: self._fetch_one_stock_code(
                stock_code,
                start_date=start_date,
                end_date=end_date,
            ),
        )
