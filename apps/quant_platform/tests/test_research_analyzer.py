import pandas as pd

from apps.quant_platform.research.analyzer.ic_analysis import analyze_factor_ic
from apps.quant_platform.research.analyzer.layered_backtest import analyze_layered_returns


def test_analyze_factor_ic_returns_series_and_summary_stats():
    panel = pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "alpha": 1.0, "overnight_return": 0.01},
            {"trade_date": "2026-01-02", "alpha": 2.0, "overnight_return": 0.02},
            {"trade_date": "2026-01-02", "alpha": 3.0, "overnight_return": 0.03},
            {"trade_date": "2026-01-03", "alpha": 1.0, "overnight_return": 0.03},
            {"trade_date": "2026-01-03", "alpha": 2.0, "overnight_return": 0.02},
            {"trade_date": "2026-01-03", "alpha": 3.0, "overnight_return": 0.01},
        ]
    )

    result = analyze_factor_ic(panel, factor_col="alpha", target_col="overnight_return")

    assert result["ic_series"]["trade_date"].tolist() == ["2026-01-02", "2026-01-03"]
    assert result["mean_ic"] == 0.0
    assert result["rank_ic"] == 0.0
    assert result["positive_rate"] == 0.5
    assert result["ic_ir"] == 0.0


def test_analyze_layered_returns_builds_group_and_long_short_outputs():
    panel = pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "ts_code": "A", "alpha": 1.0, "overnight_return": 0.01},
            {"trade_date": "2026-01-02", "ts_code": "B", "alpha": 2.0, "overnight_return": 0.02},
            {"trade_date": "2026-01-02", "ts_code": "C", "alpha": 3.0, "overnight_return": 0.03},
            {"trade_date": "2026-01-02", "ts_code": "D", "alpha": 4.0, "overnight_return": 0.04},
            {"trade_date": "2026-01-02", "ts_code": "E", "alpha": 5.0, "overnight_return": 0.05},
            {"trade_date": "2026-01-03", "ts_code": "A", "alpha": 1.0, "overnight_return": 0.01},
            {"trade_date": "2026-01-03", "ts_code": "B", "alpha": 2.0, "overnight_return": 0.02},
            {"trade_date": "2026-01-03", "ts_code": "C", "alpha": 3.0, "overnight_return": 0.03},
            {"trade_date": "2026-01-03", "ts_code": "D", "alpha": 4.0, "overnight_return": 0.04},
            {"trade_date": "2026-01-03", "ts_code": "E", "alpha": 5.0, "overnight_return": 0.05},
        ]
    )

    result = analyze_layered_returns(panel, factor_col="alpha", target_col="overnight_return", n_groups=5)

    assert sorted(result["grouped_panel"]["group"].unique().tolist()) == [1, 2, 3, 4, 5]
    assert result["long_short_returns"].tolist() == [0.04, 0.04]
    assert result["group_return_means"][5] == 0.05
    assert result["group_return_means"][1] == 0.01
