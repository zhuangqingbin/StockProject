from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, ClassVar

import pandas as pd

from apps.data_hub.data_pipeline_ts.fetchers.client import TuShareClient

"""
数据权限 https://tushare.pro/document/1?doc_id=108
"""

@dataclass(frozen=True)
class ColumnDef:
    dtype: str
    nullable: bool = True
    comment: str = ""


@dataclass(frozen=True)
class TableSchema:
    columns: dict[str, ColumnDef]
    composite_indexes: list[tuple[str, ...]] = field(default_factory=list)


class BaseFetcher(ABC):
    fields: ClassVar[list[str]] = []
    table_schema: ClassVar[TableSchema]
    data: Any

    def __init__(self, client: Any | None = None):
        self.client = client or TuShareClient()
        self.pro = getattr(self.client, "pro", None)
        self.data = None

    @abstractmethod
    def read_data(self, **kwargs: Any) -> pd.DataFrame:
        raise NotImplementedError

    def fanout_by_stock_codes(
        self,
        *,
        stock_codes: Sequence[str] | None = None,
        stock_basic_statuses: Sequence[str] = ("L",),
        fetch_one: Callable[[str], Any],
        columns: Sequence[str],
    ) -> pd.DataFrame:
        resolved_stock_codes: list[str] = []
        seen: set[str] = set()

        def append_code(raw_value: Any) -> None:
            code = str(raw_value).strip()
            if not code or code in seen:
                return
            seen.add(code)
            resolved_stock_codes.append(code)

        if stock_codes is not None:
            for value in stock_codes:
                append_code(value)
        else:
            for list_status in stock_basic_statuses:
                frame = self.client.call("stock_basic", exchange="", list_status=list_status, fields="ts_code")
                if frame is None or pd.DataFrame(frame).empty:
                    continue

                series = pd.DataFrame(frame).get("ts_code")
                if series is None:
                    continue

                for value in series.dropna().astype(str).tolist():
                    append_code(value)

        if not resolved_stock_codes:
            return pd.DataFrame(columns=columns)

        frames: list[pd.DataFrame] = []
        for stock_code in resolved_stock_codes:
            frame = fetch_one(stock_code)
            normalized_frame = pd.DataFrame(frame)
            if frame is None or normalized_frame.empty:
                continue
            frames.append(normalized_frame.dropna(axis=1, how="all"))

        if not frames:
            return pd.DataFrame(columns=columns)
        return pd.concat(frames, ignore_index=True).reindex(columns=columns)

    def fetch(self, **kwargs: Any) -> pd.DataFrame:
        result = self.read_data(**kwargs)
        if result is not None:
            self.data = result
        return pd.DataFrame(self.data if self.data is not None else [], columns=self.fields or None)
