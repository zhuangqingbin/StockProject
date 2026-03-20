from __future__ import annotations

import pandas as pd
import pytest

from apps.data_hub.data_pipeline_ts.fetchers.base import ColumnDef, TableSchema
from apps.data_hub.data_pipeline_ts.execution.persistence import validate_frame_columns


def test_validate_frame_columns_accepts_matching_columns():
    schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=False),
            "trade_date": ColumnDef("CHAR(8)", nullable=False),
        }
    )
    frame = pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "20260317"}])

    validated = validate_frame_columns("stock_daily", frame, schema)

    assert list(validated.columns) == ["ts_code", "trade_date"]


def test_validate_frame_columns_rejects_mismatched_columns():
    schema = TableSchema(
        columns={
            "ts_code": ColumnDef("VARCHAR(16)", nullable=False),
            "trade_date": ColumnDef("CHAR(8)", nullable=False),
        }
    )
    frame = pd.DataFrame([{"ts_code": "000001.SZ", "close": 12.3}])

    with pytest.raises(ValueError, match="Schema mismatch"):
        validate_frame_columns("stock_daily", frame, schema)
