"""Common metrics for signal backtesting."""

import pandas as pd
import numpy as np


def next_day_return(df: pd.DataFrame, close_col: str = "close") -> pd.Series:
    """Compute next-day return per stock, assuming df is sorted by (ts_code, trade_date)."""
    return df.groupby("ts_code")[close_col].pct_change(-1).mul(-1).shift(-1)


def signal_stats(df: pd.DataFrame, signal_col: str, return_col: str = "next_ret") -> pd.DataFrame:
    """Aggregate return stats grouped by signal value (True/False or categorical)."""
    grouped = df.groupby(signal_col)[return_col]
    stats = grouped.agg(["count", "mean", "median", "std"]).rename(
        columns={"count": "n", "mean": "avg_ret", "median": "med_ret", "std": "std_ret"}
    )
    stats["win_rate"] = df.groupby(signal_col)[return_col].apply(lambda s: (s > 0).mean())
    stats["avg_ret_pct"] = stats["avg_ret"] * 100
    return stats.round(4)


def holding_period_returns(
    df: pd.DataFrame, entry_dates: pd.DataFrame, periods: list[int] = [1, 2, 3, 5]
) -> pd.DataFrame:
    """
    Compute forward returns for multiple holding periods.
    entry_dates: DataFrame with columns [ts_code, trade_date] marking signal dates.
    df: full price data with columns [ts_code, trade_date, close_qfq].
    """
    df = df.sort_values(["ts_code", "trade_date"]).copy()
    results = []
    for _, row in entry_dates.iterrows():
        code, date = row["ts_code"], row["trade_date"]
        future = df[(df["ts_code"] == code) & (df["trade_date"] > date)].head(max(periods))
        if future.empty:
            continue
        entry_close = df[(df["ts_code"] == code) & (df["trade_date"] == date)]["close_qfq"]
        if entry_close.empty:
            continue
        entry_price = entry_close.iloc[0]
        rec = {"ts_code": code, "trade_date": date}
        for p in periods:
            if len(future) >= p:
                rec[f"ret_{p}d"] = (future.iloc[p - 1]["close_qfq"] / entry_price) - 1
            else:
                rec[f"ret_{p}d"] = np.nan
        results.append(rec)
    return pd.DataFrame(results)


def print_report(title: str, stats_df: pd.DataFrame):
    """Pretty-print a signal stats table."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    print(stats_df.to_string())
    print()
