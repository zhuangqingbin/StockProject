from __future__ import annotations

import numpy as np
import pandas as pd


class MarketFactorBuilder:
    def build(
        self,
        panel: pd.DataFrame,
        market_money_flow: pd.DataFrame | None = None,
        market_hsgt: pd.DataFrame | None = None,
        market_margin: pd.DataFrame | None = None,
        ah_comparison: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        factors = panel.copy()

        market_stats = (
            factors.groupby("trade_date", dropna=False)
            .agg(
                mkt_advance_ratio=("pct_chg", lambda values: float((values > 0).mean())),
                mkt_limit_up_count=("limit_up_days", lambda values: float((values.fillna(0) > 0).sum())),
                mkt_limit_down_count=("limit_down_days", lambda values: float((values.fillna(0) > 0).sum())),
                mkt_avg_turnover=("turnover_rate_f", "mean"),
                mkt_return=("pct_chg", "mean"),
                mkt_event_heat=("turnaround_flag", lambda values: float(values.fillna(0).sum())),
            )
            .reset_index()
        )
        if market_money_flow is not None and not market_money_flow.empty:
            market_stats = market_stats.merge(
                market_money_flow.loc[
                    :,
                    [
                        column
                        for column in [
                            "trade_date",
                            "net_mf_amount",
                            "net_amount_rate",
                            "buy_elg_amount_rate",
                            "buy_sm_amount_rate",
                        ]
                        if column in market_money_flow.columns
                    ],
                ].rename(columns={"net_mf_amount": "mkt_money_flow", "net_amount_rate": "mkt_dc_main_strength"}),
                on="trade_date",
                how="left",
            )
            if {"buy_elg_amount_rate", "buy_sm_amount_rate"}.issubset(market_stats.columns):
                market_stats["mkt_big_small_split"] = (
                    market_stats["buy_elg_amount_rate"] - market_stats["buy_sm_amount_rate"]
                )
                market_stats = market_stats.drop(columns=["buy_elg_amount_rate", "buy_sm_amount_rate"])
        else:
            market_stats["mkt_money_flow"] = factors.groupby("trade_date", dropna=False)["net_mf_amount"].transform("sum").drop_duplicates().to_numpy()
            market_stats["mkt_dc_main_strength"] = np.nan
            market_stats["mkt_big_small_split"] = np.nan

        if market_hsgt is not None and not market_hsgt.empty:
            market_stats = market_stats.merge(
                market_hsgt.loc[:, ["trade_date", "north_money"]].rename(columns={"north_money": "mkt_north_money"}),
                on="trade_date",
                how="left",
            )

        if market_margin is not None and not market_margin.empty:
            margin = market_margin.sort_values("trade_date").copy()
            margin["mkt_margin_pulse"] = margin["rzrqye"].diff()
            market_stats = market_stats.merge(
                margin.loc[:, ["trade_date", "mkt_margin_pulse"]],
                on="trade_date",
                how="left",
            )

        factors = factors.merge(market_stats, on="trade_date", how="left")
        factors = factors.sort_values(["ts_code", "trade_date"]).reset_index(drop=True)
        corr_records: list[pd.Series] = []
        sensitivity_records: list[pd.Series] = []
        beta_residual_records: list[pd.Series] = []
        flow_beta_residual_records: list[pd.Series] = []
        for _, group in factors.groupby("ts_code", sort=False):
            market_var = group["mkt_return"].rolling(20, min_periods=5).var().replace(0, np.nan)
            beta = group["pct_chg"].rolling(20, min_periods=5).cov(group["mkt_return"]) / market_var
            beta_residual_records.append(group["pct_chg"] - beta.fillna(0.0) * group["mkt_return"])

            flow_base = group.get("mkt_dc_main_strength", pd.Series(0.0, index=group.index)).fillna(0.0)
            flow_var = flow_base.rolling(20, min_periods=5).var().replace(0, np.nan)
            flow_beta = group.get("net_mf_rate", pd.Series(0.0, index=group.index)).fillna(0.0).rolling(
                20, min_periods=5
            ).cov(flow_base) / flow_var
            flow_beta_residual_records.append(
                group.get("net_mf_rate", pd.Series(0.0, index=group.index)).fillna(0.0)
                - flow_beta.fillna(0.0) * flow_base
            )
            corr_records.append(group["pct_chg"].rolling(20, min_periods=2).corr(group["mkt_return"]))
            sensitivity_records.append(
                group["pct_chg"].where(group["mkt_return"] < 0).rolling(20, min_periods=2).mean()
                / group["mkt_return"].where(group["mkt_return"] < 0).rolling(20, min_periods=2).mean().replace(0, np.nan)
            )
        factors["beta_residual"] = pd.concat(beta_residual_records).sort_index()
        factors["relative_strength_mkt"] = factors.get("pct_chg", 0.0) - factors.get("mkt_return", 0.0)
        factors["flow_beta_residual"] = pd.concat(flow_beta_residual_records).sort_index()
        factors["corr_with_market_20d"] = pd.concat(corr_records).sort_index()
        factors["mkt_sensitivity"] = pd.concat(sensitivity_records).sort_index()

        if ah_comparison is not None and not ah_comparison.empty:
            ah = ah_comparison.sort_values(["ts_code", "trade_date"]).copy()
            ah["ah_premium_chg"] = ah.groupby("ts_code", sort=False)["ah_premium"].pct_change()
            factors = factors.merge(
                ah.loc[:, ["ts_code", "trade_date", "ah_comparison", "ah_premium", "ah_premium_chg"]],
                on=["ts_code", "trade_date"],
                how="left",
            )

        if "industry" in factors.columns:
            industry_sum = factors.groupby(["trade_date", "industry"], dropna=False).agg(
                industry_count=("ts_code", "count"),
                peer_return_sum=("pct_chg", "sum"),
                peer_flow_sum=("net_mf_rate", "sum"),
                peer_limit_heat_sum=("limit_up_days", "sum"),
                peer_event_heat_sum=("turnaround_flag", "sum"),
                peer_revision_sum=("analyst_target_return", lambda values: float((values > 0).sum())),
            )
            factors = factors.merge(industry_sum, on=["trade_date", "industry"], how="left")
            peer_count = (factors["industry_count"] - 1).replace(0, np.nan)
            factors["peer_momentum"] = (factors["peer_return_sum"] - factors["pct_chg"]) / peer_count
            factors["peer_money_flow"] = (factors["peer_flow_sum"] - factors.get("net_mf_rate", 0.0).fillna(0.0)) / peer_count
            factors["peer_limit_heat"] = (factors["peer_limit_heat_sum"] - factors.get("limit_up_days", 0.0).fillna(0.0)) / peer_count
            factors["peer_event_heat"] = (factors["peer_event_heat_sum"] - factors.get("turnaround_flag", 0.0).fillna(0.0)) / peer_count
            factors["peer_revision_breadth"] = (
                factors["peer_revision_sum"] - (factors.get("analyst_target_return", 0.0).fillna(0.0) > 0).astype(float)
            ) / peer_count
            factors = factors.drop(
                columns=[
                    "industry_count",
                    "peer_return_sum",
                    "peer_flow_sum",
                    "peer_limit_heat_sum",
                    "peer_event_heat_sum",
                    "peer_revision_sum",
                ],
                errors="ignore",
            )

        return factors
