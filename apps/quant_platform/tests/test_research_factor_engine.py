import pandas as pd

from apps.quant_platform.research.factor_engine.base import (
    fill_factor_missing_values,
    winsorize_mad_by_date,
    zscore_by_date,
)
from apps.quant_platform.research.factor_engine.technical import TechnicalFactorBuilder


def test_winsorize_mad_by_date_clips_outliers_per_trade_date():
    panel = pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "alpha": 1.0},
            {"trade_date": "2026-01-02", "alpha": 2.0},
            {"trade_date": "2026-01-02", "alpha": 3.0},
            {"trade_date": "2026-01-02", "alpha": 100.0},
        ]
    )

    clipped = winsorize_mad_by_date(panel, ["alpha"])

    assert clipped["alpha"].max() < 100.0


def test_zscore_by_date_standardizes_each_cross_section():
    panel = pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "alpha": 1.0},
            {"trade_date": "2026-01-02", "alpha": 2.0},
            {"trade_date": "2026-01-02", "alpha": 3.0},
        ]
    )

    normalized = zscore_by_date(panel, ["alpha"])

    assert round(normalized["alpha"].mean(), 10) == 0.0
    assert round(normalized["alpha"].std(ddof=0), 10) == 1.0


def test_fill_factor_missing_values_prefers_industry_median_then_market():
    panel = pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "industry": "Bank", "alpha": 1.0},
            {"trade_date": "2026-01-02", "industry": "Bank", "alpha": None},
            {"trade_date": "2026-01-02", "industry": None, "alpha": None},
            {"trade_date": "2026-01-02", "industry": "Tech", "alpha": 5.0},
        ]
    )

    filled = fill_factor_missing_values(panel, ["alpha"])

    assert filled.loc[1, "alpha"] == 1.0
    assert filled.loc[2, "alpha"] == 3.0


def test_technical_factor_builder_derives_first_batch_of_technical_factors():
    panel = pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "ts_code": "000001.SZ",
                "pct_chg": 2.5,
                "ma_qfq_5": 10.5,
                "ma_qfq_20": 10.0,
                "ema_qfq_10": 10.2,
                "ema_qfq_60": 9.7,
                "atr_qfq": 0.8,
                "close_qfq": 10.4,
            }
        ]
    )

    factors = TechnicalFactorBuilder().build(panel)

    assert factors.loc[0, "pct_chg"] == 2.5
    assert round(factors.loc[0, "ma_spread_5_20"], 6) == 0.05
    assert round(factors.loc[0, "ema_spread_10_60"], 6) == round((10.2 / 9.7) - 1, 6)
    assert round(factors.loc[0, "atr_pct"], 6) == round(0.8 / 10.4, 6)
    assert round(factors.loc[0, "close_to_ma_qfq_20"], 6) == 0.04
