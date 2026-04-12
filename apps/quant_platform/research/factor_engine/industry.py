from __future__ import annotations

import numpy as np
import pandas as pd


class IndustryFactorBuilder:
    def build(self, panel: pd.DataFrame, base_factor_cols: list[str] | None = None) -> pd.DataFrame:
        factors = panel.copy()
        if "industry" not in factors.columns:
            return factors

        factor_cols = base_factor_cols or [
            "pct_chg",
            "turnover_rate_f",
            "net_mf_rate",
            "winner_rate",
            "hk_hold_chg",
            "inst_net_buy",
            "forecast_surprise_mid",
            "analyst_target_return",
            "repurchase_amount_to_mv",
        ]

        for column in factor_cols:
            if column not in factors.columns:
                continue
            industry_mean = factors.groupby(["trade_date", "industry"], dropna=False)[column].transform("mean")
            factors[f"ind_rel_{column}"] = factors[column] - industry_mean
            factors[f"ind_rank_{column}"] = factors.groupby(
                ["trade_date", "industry"], dropna=False
            )[column].rank(method="average", pct=True)

        summary = (
            factors.groupby(["trade_date", "industry"], dropna=False)
            .agg(
                ind_momentum_daily=("pct_chg", "mean"),
                ind_breadth=("pct_chg", lambda values: float((values > 0).mean())),
                ind_money_flow=("net_mf_rate", "sum"),
                ind_limit_heat=("limit_up_days", "sum"),
                ind_event_heat=("turnaround_flag", "mean"),
                ind_revision_breadth=("analyst_target_return", lambda values: float((values > 0).mean())),
                ind_turnover=("turnover_rate_f", "mean"),
            )
            .reset_index()
        )
        summary = summary.sort_values(["industry", "trade_date"]).reset_index(drop=True)
        for window in [5, 20]:
            summary[f"ind_momentum_{window}d"] = summary.groupby("industry", sort=False)["ind_momentum_daily"].transform(
                lambda values: values.rolling(window, min_periods=1).mean()
            )
        summary["ind_rotation_score"] = summary["ind_momentum_5d"] - summary["ind_momentum_20d"]
        market_turnover = summary.groupby("trade_date", dropna=False)["ind_turnover"].transform("mean")
        market_return = summary.groupby("trade_date", dropna=False)["ind_momentum_daily"].transform("mean")
        summary["ind_crowding"] = summary["ind_turnover"] / market_turnover.replace(0, np.nan)
        summary["ind_relative_strength"] = summary["ind_momentum_daily"] / market_return.replace(0, np.nan)
        summary["ind_flow_rotation"] = summary.groupby("trade_date", dropna=False)["ind_money_flow"].rank(pct=True) - summary.groupby(
            "industry", sort=False
        )["ind_money_flow"].shift(1).fillna(0.0)
        summary["ind_event_rotation"] = summary.groupby("trade_date", dropna=False)["ind_event_heat"].rank(pct=True) - summary.groupby(
            "industry", sort=False
        )["ind_event_heat"].shift(1).fillna(0.0)

        return factors.merge(summary, on=["trade_date", "industry"], how="left")
