from __future__ import annotations

import numpy as np
import pandas as pd

from .base import merge_on_panel_keys


class MoneyFlowFactorBuilder:
    def build(
        self,
        panel: pd.DataFrame,
        money_flow: pd.DataFrame | None = None,
        money_flow_dc: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        factors = merge_on_panel_keys(panel, money_flow)
        factors = merge_on_panel_keys(factors, money_flow_dc)
        amount = factors["amount"].replace(0, np.nan)

        factors["net_mf_rate"] = factors.get("net_mf_amount", 0.0) / amount
        factors["elg_net_ratio"] = (factors.get("buy_elg_amount", 0.0) - factors.get("sell_elg_amount", 0.0)) / amount
        factors["lg_net_ratio"] = (factors.get("buy_lg_amount", 0.0) - factors.get("sell_lg_amount", 0.0)) / amount
        factors["retail_contra"] = (
            (
                factors.get("buy_sm_amount", 0.0)
                - factors.get("sell_sm_amount", 0.0)
                - (factors.get("buy_lg_amount", 0.0) - factors.get("sell_lg_amount", 0.0))
            )
            / amount
        )
        factors["dc_main_strength"] = factors.get("net_amount_rate")
        factors["dc_order_split"] = factors.get("buy_elg_amount_rate", 0.0) - factors.get("buy_sm_amount_rate", 0.0)
        factors["flow_consensus"] = (
            np.sign(factors.get("net_mf_amount", 0.0)) == np.sign(factors.get("net_amount", 0.0))
        ).astype(float)
        return factors
