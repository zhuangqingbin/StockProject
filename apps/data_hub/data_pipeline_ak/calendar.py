from __future__ import annotations

from typing import Any

import pandas as pd


def get_prev_trade_days(
    date: str,
    n: int,
    *,
    akshare_client: Any = None,
) -> list[str]:
    if akshare_client is None:
        from apps.data_hub.data_pipeline_ak.provider.client import AkShareClient

        akshare_client = AkShareClient().module

    trade_dates_df = akshare_client.tool_trade_date_hist_sina()
    trade_dates_df = pd.DataFrame(trade_dates_df).copy()
    trade_dates_df["trade_date"] = pd.to_datetime(trade_dates_df["trade_date"])
    target_date = pd.to_datetime(date)
    before_target = trade_dates_df[trade_dates_df["trade_date"] < target_date]
    return before_target["trade_date"].tail(n).dt.strftime("%Y-%m-%d").tolist()
