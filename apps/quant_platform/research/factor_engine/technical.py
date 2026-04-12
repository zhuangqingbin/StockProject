from __future__ import annotations

from collections.abc import Sequence

import pandas as pd


def _safe_divide(left: pd.Series, right: pd.Series) -> pd.Series:
    denominator = right.where(right.ne(0))
    return left / denominator


class TechnicalFactorBuilder:
    factor_columns: Sequence[str] = (
        "pct_chg",
        "roc_qfq",
        "mtm_qfq",
        "ma_spread_5_20",
        "ma_spread_20_60",
        "ema_spread_10_60",
        "macd_dif_qfq",
        "macd_dea_qfq",
        "macd_qfq",
        "dmi_pdi_qfq",
        "dmi_mdi_qfq",
        "dmi_adx_qfq",
        "dmi_adxr_qfq",
        "trix_qfq",
        "cr_qfq",
        "atr_pct",
        "boll_bandwidth",
        "close_to_ma_qfq_20",
        "topdays",
        "lowdays",
        "volume_ratio",
        "turnover_rate_f",
        "obv_qfq",
        "mfi_qfq",
        "rsi_qfq_6",
        "rsi_qfq_12",
        "rsi_qfq_24",
        "kdj_k_qfq",
        "kdj_d_qfq",
        "kdj_j_qfq",
        "wr_qfq",
        "cci_qfq",
        "psy_qfq",
        "bias1_qfq",
        "bias2_qfq",
        "bias3_qfq",
        "pe_ttm",
        "pb",
        "ps_ttm",
        "dv_ttm",
        "total_mv",
        "circ_mv",
    )
    required_columns = {
        "pct_chg",
        "ma_qfq_5",
        "ma_qfq_20",
        "ema_qfq_10",
        "ema_qfq_60",
        "atr_qfq",
        "close_qfq",
    }

    def build(self, panel: pd.DataFrame) -> pd.DataFrame:
        missing = sorted(self.required_columns.difference(panel.columns))
        if missing:
            raise ValueError(f"missing required technical columns: {', '.join(missing)}")

        factors = panel.copy()
        factors["ma_spread_5_20"] = _safe_divide(factors["ma_qfq_5"], factors["ma_qfq_20"]) - 1
        if {"ma_qfq_20", "ma_qfq_60"}.issubset(factors.columns):
            factors["ma_spread_20_60"] = _safe_divide(factors["ma_qfq_20"], factors["ma_qfq_60"]) - 1
        factors["ema_spread_10_60"] = _safe_divide(factors["ema_qfq_10"], factors["ema_qfq_60"]) - 1
        factors["atr_pct"] = _safe_divide(factors["atr_qfq"], factors["close_qfq"])
        factors["close_to_ma_qfq_20"] = _safe_divide(factors["close_qfq"], factors["ma_qfq_20"]) - 1
        if {"boll_upper_qfq", "boll_lower_qfq", "close_qfq"}.issubset(factors.columns):
            factors["boll_bandwidth"] = _safe_divide(
                factors["boll_upper_qfq"] - factors["boll_lower_qfq"],
                factors["close_qfq"],
            )
        if {"kdj_k_qfq", "kdj_d_qfq"}.issubset(factors.columns):
            factors["kdj_j_qfq"] = 3 * factors["kdj_k_qfq"] - 2 * factors["kdj_d_qfq"]
        elif "kdj_qfq" in factors.columns:
            factors["kdj_j_qfq"] = factors["kdj_qfq"]
        return factors
