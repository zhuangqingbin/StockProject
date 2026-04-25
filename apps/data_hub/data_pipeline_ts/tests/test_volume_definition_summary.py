from __future__ import annotations

import pandas as pd

from apps.data_hub.data_pipeline_ts.analysis.volume_definition.segmentation import (
    add_boll_pos_context,
    add_candle_color,
    add_ma60_side,
    add_pos120_context,
)
from apps.data_hub.data_pipeline_ts.analysis.volume_definition.summary import (
    label_stability,
    summarize_masks,
)


def test_context_bucket_helpers_assign_expected_labels():
    frame = pd.DataFrame(
        [
            {
                "close_qfq": 10.0,
                "rolling_low_120": 0.0,
                "rolling_high_120": 20.0,
                "close": 9.0,
                "boll_lower_bfq": 0.0,
                "boll_upper_bfq": 15.0,
                "pct_chg": 1.2,
                "ma_bfq_60": 8.0,
            },
            {
                "close_qfq": 15.0,
                "rolling_low_120": 0.0,
                "rolling_high_120": 20.0,
                "close": 7.0,
                "boll_lower_bfq": 5.0,
                "boll_upper_bfq": 20.0,
                "pct_chg": -0.5,
                "ma_bfq_60": 8.0,
            },
            {
                "close_qfq": 18.0,
                "rolling_low_120": 0.0,
                "rolling_high_120": 20.0,
                "close": 8.0,
                "boll_lower_bfq": 0.0,
                "boll_upper_bfq": 12.0,
                "pct_chg": 0.0,
                "ma_bfq_60": 8.0,
            },
        ]
    )

    result = add_ma60_side(add_candle_color(add_boll_pos_context(add_pos120_context(frame))))

    assert result["pos120_bucket"].tolist() == ["中位", "高位", "高位"]
    assert result["boll_pos_bucket"].tolist() == ["中位", "低位", "中位"]
    assert result["candle_color"].tolist() == ["红盘", "绿盘", "绿盘"]
    assert result["ma60_side"].tolist() == ["MA60上", "MA60下", "MA60上"]


def test_context_bucket_helpers_return_nan_for_zero_width_ranges():
    frame = pd.DataFrame(
        [
            {
                "close_qfq": 10.0,
                "rolling_low_120": 10.0,
                "rolling_high_120": 10.0,
                "close": 10.0,
                "boll_lower_bfq": 10.0,
                "boll_upper_bfq": 10.0,
                "pct_chg": 0.0,
                "ma_bfq_60": 10.0,
            }
        ]
    )

    result = add_ma60_side(add_candle_color(add_boll_pos_context(add_pos120_context(frame))))

    assert pd.isna(result.loc[0, "pos120"])
    assert pd.isna(result.loc[0, "pos120_bucket"])
    assert pd.isna(result.loc[0, "boll_pos"])
    assert pd.isna(result.loc[0, "boll_pos_bucket"])


def test_summarize_masks_aggregates_return_statistics_by_group():
    frame = pd.DataFrame(
        [
            {"strategy_code": "A", "bucket": "x", "ret_next": 0.10},
            {"strategy_code": "A", "bucket": "x", "ret_next": -0.20},
            {"strategy_code": "A", "bucket": "x", "ret_next": 0.30},
            {"strategy_code": "B", "bucket": "x", "ret_next": 0.00},
            {"strategy_code": "B", "bucket": "x", "ret_next": 0.20},
            {"strategy_code": "B", "bucket": "y", "ret_next": -0.10},
        ]
    )

    result = summarize_masks(frame, ["strategy_code", "bucket"]).set_index(["strategy_code", "bucket"])

    a = result.loc[("A", "x")]
    assert a["sample_count"] == 3
    assert round(a["avg_ret_next"], 6) == round((0.10 - 0.20 + 0.30) / 3, 6)
    assert round(a["median_ret_next"], 6) == 0.10
    assert round(a["std_ret_next"], 6) == round(pd.Series([0.10, -0.20, 0.30]).std(), 6)
    assert round(a["win_rate_next"], 6) == round(2 / 3, 6)

    b = result.loc[("B", "x")]
    assert b["sample_count"] == 2
    assert round(b["avg_ret_next"], 6) == round((0.00 + 0.20) / 2, 6)
    assert round(b["win_rate_next"], 6) == 0.5


def test_label_stability_applies_period_threshold_and_label_rules():
    frame = pd.DataFrame(
        [
            {"strategy_code": "stable", "sample_count": 120, "excess_ret_next": 0.10},
            {"strategy_code": "stable", "sample_count": 130, "excess_ret_next": 0.04},
            {"strategy_code": "stable", "sample_count": 140, "excess_ret_next": -0.02},
            {"strategy_code": "volatile", "sample_count": 150, "excess_ret_next": 0.08},
            {"strategy_code": "volatile", "sample_count": 160, "excess_ret_next": -0.01},
            {"strategy_code": "volatile", "sample_count": 170, "excess_ret_next": -0.03},
            {"strategy_code": "failed", "sample_count": 110, "excess_ret_next": -0.02},
            {"strategy_code": "failed", "sample_count": 130, "excess_ret_next": 0.00},
            {"strategy_code": "failed", "sample_count": 140, "excess_ret_next": -0.04},
            {"strategy_code": "insufficient", "sample_count": 90, "excess_ret_next": 0.20},
            {"strategy_code": "insufficient", "sample_count": 80, "excess_ret_next": -0.05},
        ]
    )

    result = label_stability(frame).set_index("strategy_code")

    stable = result.loc["stable"]
    assert stable["qualified_period_count"] == 3
    assert stable["positive_period_count"] == 2
    assert stable["stability_label"] == "稳定"

    volatile = result.loc["volatile"]
    assert volatile["qualified_period_count"] == 3
    assert volatile["positive_period_count"] == 1
    assert volatile["stability_label"] == "高波动"

    failed = result.loc["failed"]
    assert failed["qualified_period_count"] == 3
    assert failed["positive_period_count"] == 0
    assert failed["stability_label"] == "失效"

    insufficient = result.loc["insufficient"]
    assert insufficient["qualified_period_count"] == 0
    assert insufficient["qualified_sample_count"] == 0
    assert insufficient["stability_label"] == "样本不足"
