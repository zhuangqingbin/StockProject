from __future__ import annotations

from typing import Any, Callable

import pandas as pd


def get_trade_cal(
    start_date: str,
    end_date: str,
    *,
    fetcher_cls: Callable[[], Any] | None = None,
) -> list[str]:
    if fetcher_cls is None:
        from apps.data_hub.data_pipeline_ts.fetchers.infrastructure import TradeCalFetch

        fetcher_cls = TradeCalFetch

    fetcher = fetcher_cls()
    calendar_df = pd.DataFrame(fetcher.fetch(start_date=start_date, end_date=end_date))
    if calendar_df.empty:
        return []
    return list(calendar_df.loc[calendar_df["is_open"] == 1, "cal_date"])
