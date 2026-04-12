from __future__ import annotations

import pandas as pd

from .base import merge_on_panel_keys, sort_panel


class OwnershipFactorBuilder:
    def build(
        self,
        panel: pd.DataFrame,
        holder_number: pd.DataFrame | None = None,
        holder_trade: pd.DataFrame | None = None,
        repurchase: pd.DataFrame | None = None,
        share_float: pd.DataFrame | None = None,
        pledge_stat: pd.DataFrame | None = None,
        top10_holders: pd.DataFrame | None = None,
        top10_floatholders: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        factors = panel.copy()

        if holder_number is not None and not holder_number.empty:
            numbers = sort_panel(holder_number)
            numbers["holder_num_chg"] = numbers.groupby("ts_code", sort=False)["holder_num"].pct_change()
            factors = merge_on_panel_keys(factors, numbers, value_columns=["holder_num", "holder_num_chg"])

        if holder_trade is not None and not holder_trade.empty:
            trades = holder_trade.copy()
            trades["insider_net_increase"] = trades.apply(
                lambda row: row.get("change_ratio", 0.0) if str(row.get("in_de", "")).upper() == "IN" else 0.0,
                axis=1,
            )
            trades["insider_net_decrease"] = trades.apply(
                lambda row: row.get("change_ratio", 0.0) if str(row.get("in_de", "")).upper() == "DE" else 0.0,
                axis=1,
            )
            trades = (
                trades.groupby(["ts_code", "trade_date"], dropna=False)[["insider_net_increase", "insider_net_decrease"]]
                .sum()
                .reset_index()
            )
            factors = merge_on_panel_keys(factors, trades)

        if repurchase is not None and not repurchase.empty:
            repurchase_frame = repurchase.rename(columns={"amount": "repurchase_amount"})
            factors = merge_on_panel_keys(
                factors,
                repurchase_frame,
                value_columns=["repurchase_amount", "high_limit"],
            )
            factors["repurchase_amount_to_mv"] = factors.get("repurchase_amount", 0.0) / factors["total_mv"].replace(0, pd.NA)
            factors["repurchase_price_premium"] = factors.get("high_limit") / factors["close_qfq"].replace(0, pd.NA) - 1

        factors = merge_on_panel_keys(factors, share_float, value_columns=["float_ratio"])
        factors["unlock_ratio"] = factors.get("float_ratio")
        factors = merge_on_panel_keys(factors, pledge_stat, value_columns=["pledge_ratio"])

        if top10_holders is not None and not top10_holders.empty:
            holders = (
                top10_holders.groupby(["ts_code", "trade_date"], dropna=False)[
                    ["hold_ratio", "hold_float_ratio", "hold_change"]
                ]
                .sum(min_count=1)
                .reset_index()
                .rename(
                    columns={
                        "hold_ratio": "top10_holder_concentration",
                        "hold_float_ratio": "top10_holder_float_concentration",
                        "hold_change": "top10_holder_change",
                    }
                )
            )
            factors = merge_on_panel_keys(factors, holders)

        if top10_floatholders is not None and not top10_floatholders.empty:
            float_holders = (
                top10_floatholders.groupby(["ts_code", "trade_date"], dropna=False)[
                    ["hold_ratio", "hold_float_ratio", "hold_change"]
                ]
                .sum(min_count=1)
                .reset_index()
                .rename(
                    columns={
                        "hold_ratio": "top10_float_holder_concentration",
                        "hold_float_ratio": "top10_float_holder_float_concentration",
                        "hold_change": "top10_float_holder_change",
                    }
                )
            )
            factors = merge_on_panel_keys(factors, float_holders)

        return factors
