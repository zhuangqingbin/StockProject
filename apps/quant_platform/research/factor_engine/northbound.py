from __future__ import annotations

import pandas as pd

from .base import merge_on_panel_keys, sort_panel


class NorthboundFactorBuilder:
    def build(
        self,
        panel: pd.DataFrame,
        hk_hold: pd.DataFrame | None = None,
        hsgt_top10: pd.DataFrame | None = None,
        ccass_hold: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        factors = panel.copy()

        if hk_hold is not None and not hk_hold.empty:
            hold = sort_panel(hk_hold)
            hold["hk_hold_chg"] = hold.groupby("ts_code", sort=False)["ratio"].diff()
            factors = merge_on_panel_keys(
                factors,
                hold.rename(columns={"ratio": "hk_hold_ratio"}),
                value_columns=["hk_hold_ratio", "hk_hold_chg", "vol"],
            )

        if hsgt_top10 is not None and not hsgt_top10.empty:
            top10 = (
                hsgt_top10.groupby(["ts_code", "trade_date"], dropna=False)["net_amount"]
                .sum()
                .reset_index()
            )
            top10["hsgt_top10_flag"] = 1.0
            factors = merge_on_panel_keys(
                factors,
                top10.rename(columns={"net_amount": "hsgt_top10_net_amount"}),
                value_columns=["hsgt_top10_net_amount", "hsgt_top10_flag"],
            )

        if ccass_hold is not None and not ccass_hold.empty:
            ccass = sort_panel(ccass_hold)
            ccass["ccass_participant_chg"] = ccass.groupby("ts_code", sort=False)["hold_nums"].diff()
            factors = merge_on_panel_keys(
                factors,
                ccass.rename(columns={"hold_ratio": "ccass_hold_ratio"}),
                value_columns=["ccass_hold_ratio", "hold_nums", "ccass_participant_chg"],
            )

        factors["hsgt_top10_net_ratio"] = factors.get("hsgt_top10_net_amount", pd.Series(0.0, index=factors.index)) / factors["amount"].replace(0, pd.NA)
        factors["north_attention_score"] = (
            factors.get("hk_hold_chg", pd.Series(0.0, index=factors.index)).fillna(0.0)
            + factors.get("hsgt_top10_flag", pd.Series(0.0, index=factors.index)).fillna(0.0)
            + factors.get("ccass_hold_ratio", pd.Series(0.0, index=factors.index)).fillna(0.0)
        )
        return factors
