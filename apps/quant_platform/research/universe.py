from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


def _to_datetime(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values, errors="coerce")


@dataclass(frozen=True)
class UniverseFilterConfig:
    exclude_st: bool = True
    exclude_suspended: bool = True
    min_list_days: int = 60


class UniverseFilter:
    def __init__(self, config: UniverseFilterConfig | None = None):
        self.config = config or UniverseFilterConfig()

    def apply(
        self,
        panel: pd.DataFrame,
        stock_basic: pd.DataFrame,
        st_flags: pd.DataFrame | None = None,
        suspensions: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        filtered = panel.copy()
        filtered["trade_date"] = _to_datetime(filtered["trade_date"])

        if self.config.min_list_days > 0 and not stock_basic.empty:
            listed = stock_basic.loc[:, ["ts_code", "list_date"]].copy()
            listed["list_date"] = _to_datetime(listed["list_date"])
            filtered = filtered.merge(listed, on="ts_code", how="left")
            listed_days = (filtered["trade_date"] - filtered["list_date"]).dt.days
            eligible = filtered["list_date"].isna() | (listed_days >= self.config.min_list_days)
            filtered = filtered.loc[eligible].copy()
            filtered = filtered.drop(columns=["list_date"])

        if self.config.exclude_st and st_flags is not None and not st_flags.empty:
            st_daily = st_flags.loc[:, ["ts_code", "trade_date"]].copy()
            st_daily["trade_date"] = _to_datetime(st_daily["trade_date"])
            st_daily["_is_st"] = True
            filtered = filtered.merge(st_daily.drop_duplicates(), on=["ts_code", "trade_date"], how="left")
            filtered = filtered.loc[filtered["_is_st"] != True].drop(columns=["_is_st"])

        if self.config.exclude_suspended and suspensions is not None and not suspensions.empty:
            suspended = suspensions.loc[:, ["ts_code", "trade_date", "suspend_type"]].copy()
            suspended["trade_date"] = _to_datetime(suspended["trade_date"])
            suspended = suspended.loc[suspended["suspend_type"].fillna("S").ne("R")].copy()
            suspended["_is_suspended"] = True
            filtered = filtered.merge(
                suspended.loc[:, ["ts_code", "trade_date", "_is_suspended"]].drop_duplicates(),
                on=["ts_code", "trade_date"],
                how="left",
            )
            filtered = filtered.loc[filtered["_is_suspended"] != True].drop(columns=["_is_suspended"])

        filtered["trade_date"] = filtered["trade_date"].dt.strftime("%Y-%m-%d")
        return filtered.reset_index(drop=True)
