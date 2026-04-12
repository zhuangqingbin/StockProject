from __future__ import annotations

import numpy as np
import pandas as pd

from .base import merge_on_panel_keys, sort_panel


class LimitFactorBuilder:
    def __init__(self, window: int = 5):
        self.window = window

    def build(
        self,
        panel: pd.DataFrame,
        limit_list: pd.DataFrame | None = None,
        limit_price: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        factors = panel.copy()

        if limit_list is not None and not limit_list.empty:
            limits = sort_panel(limit_list)
            limit_type = limits["limit"].fillna("")
            limits["is_limit_up"] = limit_type.isin(["U", "涨停"]).astype(float)
            limits["is_limit_down"] = limit_type.isin(["D", "跌停"]).astype(float)
            limits["limit_up_days"] = limits.groupby("ts_code", sort=False)["is_limit_up"].transform(
                lambda values: values.rolling(self.window, min_periods=1).sum()
            )
            limits["limit_down_days"] = limits.groupby("ts_code", sort=False)["is_limit_down"].transform(
                lambda values: values.rolling(self.window, min_periods=1).sum()
            )
            factors = merge_on_panel_keys(factors, limits)
            factors["seal_amount_ratio"] = factors.get("fd_amount", 0.0) / factors["float_mv"].replace(0, pd.NA)
            factors["open_board_pressure"] = (
                factors.get("open_times", 0.0) / factors.get("limit_times", 1.0).replace(0, 1.0)
            )

        if limit_price is not None and not limit_price.empty:
            renamed = limit_price.rename(
                columns={
                    "pre_close": "limit_pre_close",
                    "up_limit": "limit_up_price",
                    "down_limit": "limit_down_price",
                }
            )
            factors = merge_on_panel_keys(
                factors,
                renamed,
                value_columns=["limit_pre_close", "limit_up_price", "limit_down_price"],
            )
            close = factors.get("close", pd.Series(np.nan, index=factors.index, dtype=float))
            open_price = factors.get("open", pd.Series(np.nan, index=factors.index, dtype=float))
            limit_up = factors.get("limit_up_price", pd.Series(np.nan, index=factors.index, dtype=float))
            limit_down = factors.get("limit_down_price", pd.Series(np.nan, index=factors.index, dtype=float))
            factors["close_limit_up_flag"] = np.isclose(close, limit_up, equal_nan=False).astype(float)
            factors["close_limit_down_flag"] = np.isclose(close, limit_down, equal_nan=False).astype(float)
            factors["one_word_limit_up_flag"] = np.isclose(open_price, limit_up, equal_nan=False).astype(float)

        return factors
