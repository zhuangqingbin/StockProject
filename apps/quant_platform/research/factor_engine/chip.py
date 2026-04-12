from __future__ import annotations

import numpy as np
import pandas as pd

from .base import merge_on_panel_keys


class ChipFactorBuilder:
    def build(
        self,
        panel: pd.DataFrame,
        chip_perf: pd.DataFrame | None = None,
        chip_distribution: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        factors = merge_on_panel_keys(panel, chip_perf)
        close = factors["close_qfq"].replace(0, np.nan)
        weight_avg = factors.get("weight_avg", pd.Series(np.nan, index=factors.index, dtype=float))
        cost_5pct = factors.get("cost_5pct", pd.Series(np.nan, index=factors.index, dtype=float))
        cost_15pct = factors.get("cost_15pct", pd.Series(np.nan, index=factors.index, dtype=float))
        cost_50pct = factors.get("cost_50pct", pd.Series(np.nan, index=factors.index, dtype=float))
        cost_85pct = factors.get("cost_85pct", pd.Series(np.nan, index=factors.index, dtype=float))
        cost_95pct = factors.get("cost_95pct", pd.Series(np.nan, index=factors.index, dtype=float))

        factors["avg_cost_gap"] = factors["close_qfq"] / weight_avg.replace(0, np.nan) - 1
        factors["chip_width"] = (cost_95pct - cost_5pct) / weight_avg
        factors["chip_skew"] = (
            (
                (cost_85pct - cost_50pct)
                - (cost_50pct - cost_15pct)
            )
            / weight_avg
        )

        if chip_distribution is None or chip_distribution.empty:
            factors["upper_overhang"] = np.nan
            factors["support_density"] = np.nan
            factors["dominant_peak_gap"] = np.nan
            return factors

        chips = chip_distribution.merge(
            factors.loc[:, ["ts_code", "trade_date", "close_qfq"]],
            on=["ts_code", "trade_date"],
            how="left",
        )
        aggregated_records: list[dict[str, object]] = []
        for (ts_code, trade_date), group in chips.groupby(["ts_code", "trade_date"], dropna=False):
            close_value = group["close_qfq"].iloc[0]
            aggregated_records.append(
                {
                    "ts_code": ts_code,
                    "trade_date": trade_date,
                    "upper_overhang": group.loc[group["price"] > close_value, "percent"].sum(),
                    "support_density": group.loc[
                        (close_value != 0) & ((group["price"] / close_value - 1).abs() <= 0.03),
                        "percent",
                    ].sum(),
                    "dominant_peak_price": group.loc[group["percent"].idxmax(), "price"] if not group.empty else np.nan,
                }
            )
        aggregated = pd.DataFrame(aggregated_records)
        factors = merge_on_panel_keys(factors, aggregated)
        factors["dominant_peak_gap"] = factors["dominant_peak_price"] / close - 1
        return factors.drop(columns=["dominant_peak_price"], errors="ignore")
