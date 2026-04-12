from __future__ import annotations

import numpy as np
import pandas as pd


def _series(frame: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column in frame.columns:
        return frame[column].fillna(default)
    return pd.Series(default, index=frame.index, dtype=float)


class CrossFeatureBuilder:
    def build(self, panel: pd.DataFrame) -> pd.DataFrame:
        factors = panel.copy()
        factors["chip_breakout_strength"] = _series(factors, "avg_cost_gap") * _series(factors, "volume_ratio")
        factors["upper_overhang_reversal"] = _series(factors, "upper_overhang") * (-_series(factors, "pct_chg"))
        factors["support_rebound"] = _series(factors, "support_density") * (50 - _series(factors, "rsi_qfq_6", 50.0))
        factors["turnover_chip_shift"] = _series(factors, "turnover_rate_f") * (-_series(factors, "avg_cost_gap"))

        factors["north_main_consensus"] = (
            _series(factors, "hk_hold_chg")
            + _series(factors, "net_mf_rate")
            + _series(factors, "dc_main_strength")
        )
        factors["north_attention_breakout"] = (
            _series(factors, "hsgt_top10_flag")
            * _series(factors, "hk_hold_chg")
            * np.sign(_series(factors, "macd_dif_qfq"))
        )
        factors["ccass_north_mismatch"] = _series(factors, "ccass_participant_chg") - _series(factors, "hk_hold_chg")
        factors["margin_flow_resonance"] = _series(factors, "rzmre_intensity") * _series(factors, "dc_main_strength")

        factors["repurchase_discount_absorb"] = (
            _series(factors, "repurchase_price_premium")
            * (-_series(factors, "pct_chg"))
            * _series(factors, "net_mf_rate")
        )
        factors["insider_followthrough"] = _series(factors, "insider_net_increase") * _series(factors, "volume_ratio")
        factors["block_trade_followthrough"] = (-_series(factors, "block_discount")) * _series(factors, "inst_net_buy")
        factors["survey_breakout"] = _series(factors, "survey_heat") * (
            _series(factors, "close_qfq") > _series(factors, "ma_qfq_20", np.inf)
        ).astype(float)

        factors["forecast_trend_confirm"] = _series(factors, "forecast_surprise_mid") * np.sign(_series(factors, "macd_dif_qfq"))
        factors["analyst_gap_oversold"] = _series(factors, "analyst_target_return") * (30 - _series(factors, "rsi_qfq_6", 30.0))
        factors["earnings_quality_breakout"] = _series(factors, "express_profit_yoy") * _series(factors, "boll_bandwidth", 1.0)
        factors["revision_flow_sync"] = _series(factors, "analyst_attention_20d") * _series(factors, "dc_main_strength")

        factors["high_margin_high_unlock"] = _series(factors, "rzye_ratio") * _series(factors, "unlock_ratio")
        factors["pledge_fragile_momentum"] = _series(factors, "pledge_ratio") * _series(factors, "pct_chg_momentum_20")
        factors["crowded_reversal"] = (
            _series(factors, "hk_hold_ratio")
            * _series(factors, "winner_rate")
            * (-_series(factors, "pct_chg"))
        )
        factors["quality_under_short_pressure"] = _series(factors, "q_roe") * _series(factors, "rqye_ratio")
        return factors
