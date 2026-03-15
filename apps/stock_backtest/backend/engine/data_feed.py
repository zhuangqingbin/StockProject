from __future__ import annotations

from datetime import date

import backtrader as bt
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.stock_backtest.backend.models.db_models import (
    MarketDailyBasicModel,
    MarketDailyKlineModel,
    MarketMoneyflowModel,
)


PRIMARY_COLUMNS = ("open", "high", "low", "close", "volume", "openinterest")
EXTRA_MODEL_MAPPING = {
    "daily_basic": (MarketDailyBasicModel, ("turnover_rate", "pe_ttm")),
    "moneyflow": (MarketMoneyflowModel, ("net_mf_amount",)),
}


def _rows_to_frame(rows: list[object], column_names: tuple[str, ...]) -> pd.DataFrame:
    records = []
    for row in rows:
        record = {"trade_date": row.trade_date}
        for column_name in column_names:
            record[column_name] = getattr(row, column_name, None)
        records.append(record)
    return pd.DataFrame.from_records(records)


def load_symbol_frame(
    session: Session,
    symbol: str,
    start_date: date,
    end_date: date,
    feed_ids: list[str],
) -> pd.DataFrame:
    base_rows = (
        session.execute(
            select(MarketDailyKlineModel)
            .where(MarketDailyKlineModel.ts_code == symbol)
            .where(MarketDailyKlineModel.trade_date >= start_date)
            .where(MarketDailyKlineModel.trade_date <= end_date)
            .order_by(MarketDailyKlineModel.trade_date.asc())
        )
        .scalars()
        .all()
    )
    if not base_rows:
        raise ValueError(f"No daily_kline data found for {symbol} in the requested range")

    base_frame = pd.DataFrame.from_records(
        [
            {
                "trade_date": row.trade_date,
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "close": row.close,
                "volume": row.vol,
                "amount": row.amount or 0,
            }
            for row in base_rows
        ]
    )

    merged_frame = base_frame
    for feed_id in feed_ids:
        if feed_id == "daily_kline":
            continue
        model_and_columns = EXTRA_MODEL_MAPPING.get(feed_id)
        if model_and_columns is None:
            continue

        model, column_names = model_and_columns
        extra_rows = (
            session.execute(
                select(model)
                .where(model.ts_code == symbol)
                .where(model.trade_date >= start_date)
                .where(model.trade_date <= end_date)
            )
            .scalars()
            .all()
        )
        if not extra_rows:
            continue

        extra_frame = _rows_to_frame(extra_rows, column_names)
        merged_frame = merged_frame.merge(extra_frame, on="trade_date", how="left")

    merged_frame["trade_date"] = pd.to_datetime(merged_frame["trade_date"])
    merged_frame = merged_frame.sort_values("trade_date").drop_duplicates("trade_date")
    merged_frame["openinterest"] = 0.0
    merged_frame = merged_frame.set_index("trade_date")
    merged_frame = merged_frame.fillna(0.0)
    return merged_frame


def build_backtrader_feed(frame: pd.DataFrame, symbol: str):
    extra_columns = tuple(column for column in frame.columns if column not in PRIMARY_COLUMNS)
    feed_class_name = f"StockBacktestFeed_{'_'.join(extra_columns) or 'base'}"
    feed_class = type(
        feed_class_name,
        (bt.feeds.PandasData,),
        {
            "lines": extra_columns,
            "params": (
                ("datetime", None),
                ("open", -1),
                ("high", -1),
                ("low", -1),
                ("close", -1),
                ("volume", -1),
                ("openinterest", -1),
            )
            + tuple((column_name, -1) for column_name in extra_columns),
        },
    )
    return feed_class(dataname=frame, name=symbol)
