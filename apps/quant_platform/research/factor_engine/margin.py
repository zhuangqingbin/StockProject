from __future__ import annotations

import pandas as pd

from .base import merge_on_panel_keys, sort_panel


class MarginFactorBuilder:
    def build(self, panel: pd.DataFrame, margin_detail: pd.DataFrame | None = None) -> pd.DataFrame:
        if margin_detail is None or margin_detail.empty:
            return panel.copy()

        factors = panel.copy()
        detail = sort_panel(margin_detail)
        detail["margin_balance"] = detail["rzye"] - detail.get("rqye", 0.0)
        detail["margin_balance_chg"] = detail.groupby("ts_code", sort=False)["margin_balance"].diff()
        factors = merge_on_panel_keys(factors, detail)
        mv = factors.get("circ_mv", factors.get("float_mv", pd.Series(index=factors.index))).replace(0, pd.NA)
        factors["rzye_ratio"] = factors.get("rzye", 0.0) / mv
        factors["rzmre_intensity"] = factors.get("rzmre", 0.0) / factors["amount"].replace(0, pd.NA)
        factors["rqye_ratio"] = factors.get("rqye", 0.0) / mv
        return factors.drop(columns=["margin_balance"], errors="ignore")
