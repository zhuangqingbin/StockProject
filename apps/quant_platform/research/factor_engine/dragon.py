from __future__ import annotations

import pandas as pd

from .base import merge_on_panel_keys


class DragonFactorBuilder:
    def build(
        self,
        panel: pd.DataFrame,
        top_list: pd.DataFrame | None = None,
        top_inst: pd.DataFrame | None = None,
        block_trade: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        factors = panel.copy()

        if top_list is not None and not top_list.empty:
            toplist = top_list.copy()
            if "net_rate" not in toplist.columns and "net_amount" in toplist.columns:
                toplist["net_rate"] = toplist["net_amount"] / factors["amount"].replace(0, pd.NA).mean()
            factors = merge_on_panel_keys(factors, toplist, value_columns=["net_rate", "net_amount"])
            factors = factors.rename(columns={"net_rate": "top_list_net_rate"})

        if top_inst is not None and not top_inst.empty:
            inst = (
                top_inst.groupby(["ts_code", "trade_date"], dropna=False)[["net_buy", "buy", "sell"]]
                .sum()
                .reset_index()
            )
            factors = merge_on_panel_keys(factors, inst, value_columns=["net_buy", "buy", "sell"])
            factors["inst_net_buy"] = factors.get("net_buy")
            factors["inst_participation"] = (
                factors.get("buy", 0.0).fillna(0.0) + factors.get("sell", 0.0).fillna(0.0)
            ) / factors["amount"].replace(0, pd.NA)

        if block_trade is not None and not block_trade.empty:
            block = (
                block_trade.groupby(["ts_code", "trade_date"], dropna=False)[["price", "amount"]]
                .mean()
                .reset_index()
            )
            block = block.rename(columns={"amount": "block_trade_amount"})
            factors = merge_on_panel_keys(factors, block, value_columns=["price", "block_trade_amount"])
            factors["block_discount"] = factors.get("price") / factors["close_qfq"].replace(0, pd.NA) - 1
            factors["block_amount_ratio"] = factors.get("block_trade_amount", 0.0) / factors["amount"].replace(0, pd.NA)

        return factors
