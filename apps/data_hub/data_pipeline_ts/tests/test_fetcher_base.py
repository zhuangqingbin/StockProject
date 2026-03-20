from __future__ import annotations

from dataclasses import FrozenInstanceError

import pandas as pd
import pytest

from apps.data_hub.data_pipeline_ts.fetchers import base as base_module
from apps.data_hub.data_pipeline_ts.fetchers.base import BaseFetcher, ColumnDef, TableSchema


class DemoFetcher(BaseFetcher):
    fields = ["ts_code", "trade_date"]
    table_schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=False, comment="股票代码"),
            "trade_date": ColumnDef("CHAR(8)", nullable=False, comment="交易日"),
        },
        composite_indexes=[("trade_date",), ("trade_date", "ts_code")],
    )

    def read_data(self, **kwargs):
        return pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": kwargs["trade_date"]}])


def test_column_def_and_table_schema_are_frozen() -> None:
    column = ColumnDef("VARCHAR(16)", nullable=False)

    with pytest.raises(FrozenInstanceError):
        column.dtype = "TEXT"  # type: ignore[misc]


def test_base_fetcher_subclass_exposes_table_schema_and_fetch() -> None:
    fetcher = DemoFetcher(client=object())

    result = fetcher.fetch(trade_date="20260317")

    assert fetcher.table_schema.composite_indexes == [("trade_date",), ("trade_date", "ts_code")]
    assert list(result.columns) == ["ts_code", "trade_date"]
    assert result.iloc[0].to_dict() == {"ts_code": "000001.SZ", "trade_date": "20260317"}


def test_fetcher_package_no_longer_exposes_schema_inference_helpers() -> None:
    assert not hasattr(base_module, "build_table_schema")
    assert not hasattr(base_module, "infer_column_def")
    assert not hasattr(base_module, "infer_composite_indexes")
