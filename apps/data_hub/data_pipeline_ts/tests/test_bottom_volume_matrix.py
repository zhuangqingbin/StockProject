from __future__ import annotations

from datetime import datetime as real_datetime
from pathlib import Path

import pandas as pd

from apps.data_hub.data_pipeline_ts.analysis.bottom_val_strategies import bottom_volume_matrix as module
from apps.data_hub.data_pipeline_ts.analysis.bottom_val_strategies.bottom_volume_matrix import (
    build_bottom_rule_defs,
    build_features,
    build_latest_hits,
    build_strategy_ranking,
    build_volume_rule_defs,
    summarize_signal_matrix,
    write_outputs,
)


def _fixed_datetime_class():
    class FixedDateTime(real_datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 4, 18, 16, 30)

        @classmethod
        def strptime(cls, date_string, fmt):
            return real_datetime.strptime(date_string, fmt)

    return FixedDateTime


def test_build_features_adds_expected_forward_returns_and_rolling_fields():
    frame = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240101",
                "open_qfq": 10.0,
                "high_qfq": 11.0,
                "low_qfq": 9.0,
                "close_qfq": 10.0,
                "pct_chg": 0.0,
                "vol": 100.0,
                "amount": 1000.0,
                "turnover_rate": 1.0,
                "turnover_rate_f": 1.0,
                "volume_ratio": 0.8,
                "boll_lower_qfq": 9.5,
                "boll_mid_qfq": 10.2,
                "boll_upper_qfq": 10.8,
                "rsi_qfq_6": 45.0,
                "rsi_qfq_12": 48.0,
                "ma_qfq_20": 10.4,
                "ma_qfq_60": 10.8,
                "downdays": 0,
                "updays": 0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240102",
                "open_qfq": 10.0,
                "high_qfq": 10.5,
                "low_qfq": 9.2,
                "close_qfq": 9.5,
                "pct_chg": -5.0,
                "vol": 120.0,
                "amount": 1200.0,
                "turnover_rate": 1.2,
                "turnover_rate_f": 1.2,
                "volume_ratio": 0.9,
                "boll_lower_qfq": 9.2,
                "boll_mid_qfq": 10.0,
                "boll_upper_qfq": 10.6,
                "rsi_qfq_6": 35.0,
                "rsi_qfq_12": 40.0,
                "ma_qfq_20": 10.2,
                "ma_qfq_60": 10.7,
                "downdays": 1,
                "updays": 0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240103",
                "open_qfq": 9.6,
                "high_qfq": 10.0,
                "low_qfq": 9.0,
                "close_qfq": 9.8,
                "pct_chg": 3.0,
                "vol": 180.0,
                "amount": 2200.0,
                "turnover_rate": 1.8,
                "turnover_rate_f": 1.8,
                "volume_ratio": 1.6,
                "boll_lower_qfq": 9.1,
                "boll_mid_qfq": 9.9,
                "boll_upper_qfq": 10.4,
                "rsi_qfq_6": 32.0,
                "rsi_qfq_12": 38.0,
                "ma_qfq_20": 10.0,
                "ma_qfq_60": 10.5,
                "downdays": 2,
                "updays": 0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240104",
                "open_qfq": 9.9,
                "high_qfq": 10.4,
                "low_qfq": 9.7,
                "close_qfq": 10.2,
                "pct_chg": 4.0,
                "vol": 260.0,
                "amount": 3000.0,
                "turnover_rate": 2.4,
                "turnover_rate_f": 2.4,
                "volume_ratio": 2.0,
                "boll_lower_qfq": 9.2,
                "boll_mid_qfq": 9.8,
                "boll_upper_qfq": 10.5,
                "rsi_qfq_6": 42.0,
                "rsi_qfq_12": 44.0,
                "ma_qfq_20": 9.9,
                "ma_qfq_60": 10.3,
                "downdays": 0,
                "updays": 1,
            },
        ]
    )

    result = build_features(frame)

    first_row = result.iloc[0]
    assert round(first_row["ret_1d"], 6) == round((9.5 / 10.0) - 1, 6)
    assert round(first_row["ret_3d"], 6) == round((10.2 / 10.0) - 1, 6)
    assert round(result.iloc[2]["vol_ma_3_prev"], 6) == round((100.0 + 120.0) / 2, 6)
    assert round(result.iloc[2]["volume_ratio_ma_3_prev"], 6) == round((0.8 + 0.9) / 2, 6)
    assert round(result.iloc[2]["close_to_low_120"], 6) == round(9.8 / 9.0, 6)
    assert result.iloc[3]["prev_volume_ratio"] == 1.6


def test_rule_builders_generate_expected_counts_and_family_labels():
    bottom_rules = build_bottom_rule_defs()
    volume_rules = build_volume_rule_defs()

    assert len(bottom_rules) == 18
    assert len(volume_rules) == 18
    assert {rule.family for rule in bottom_rules} == {
        "pos120",
        "near_120_low",
        "boll_rsi_oversold",
        "below_ma_zone",
        "exhaustion",
    }
    assert {rule.family for rule in volume_rules} == {
        "volume_ratio",
        "shrink_to_expand",
        "vol_spike_5",
        "turnover_jump",
        "amount_spike_5",
        "consecutive_expand",
    }


def test_summarize_signal_matrix_returns_combo_and_family_aggregates():
    frame = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240101",
                "ret_1d": 0.02,
                "ret_3d": 0.05,
                "pos120": 0.10,
                "close_to_low_120": 1.04,
                "close_qfq": 10.0,
                "boll_lower_qfq": 10.0,
                "rsi_qfq_6": 28.0,
                "rsi_qfq_12": 40.0,
                "ma_qfq_20": 11.0,
                "ma_qfq_60": 12.0,
                "downdays": 4,
                "volume_ratio": 1.8,
                "volume_ratio_ma_3_prev": 0.9,
                "prev_volume_ratio": 1.1,
                "vol_spike_5": 1.6,
                "turnover_rate_f": 2.5,
                "turnover_jump_3": 1.6,
                "amount_spike_5": 1.7,
                "pct_chg": 3.0,
            },
            {
                "ts_code": "000002.SZ",
                "trade_date": "20240101",
                "ret_1d": -0.01,
                "ret_3d": 0.03,
                "pos120": 0.18,
                "close_to_low_120": 1.06,
                "close_qfq": 8.0,
                "boll_lower_qfq": 7.9,
                "rsi_qfq_6": 33.0,
                "rsi_qfq_12": 42.0,
                "ma_qfq_20": 8.5,
                "ma_qfq_60": 8.8,
                "downdays": 3,
                "volume_ratio": 1.6,
                "volume_ratio_ma_3_prev": 0.8,
                "prev_volume_ratio": 1.0,
                "vol_spike_5": 1.7,
                "turnover_rate_f": 2.2,
                "turnover_jump_3": 1.5,
                "amount_spike_5": 1.4,
                "pct_chg": 1.0,
            },
            {
                "ts_code": "000003.SZ",
                "trade_date": "20240101",
                "ret_1d": 0.04,
                "ret_3d": 0.08,
                "pos120": 0.35,
                "close_to_low_120": 1.15,
                "close_qfq": 12.0,
                "boll_lower_qfq": 10.5,
                "rsi_qfq_6": 55.0,
                "rsi_qfq_12": 52.0,
                "ma_qfq_20": 11.5,
                "ma_qfq_60": 11.0,
                "downdays": 0,
                "volume_ratio": 0.9,
                "volume_ratio_ma_3_prev": 0.9,
                "prev_volume_ratio": 0.8,
                "vol_spike_5": 1.0,
                "turnover_rate_f": 0.9,
                "turnover_jump_3": 1.0,
                "amount_spike_5": 1.0,
                "pct_chg": 0.5,
            },
        ]
    )

    summary_df, trigger_df, bottom_family_df, volume_family_df = summarize_signal_matrix(frame, min_sample=1)

    assert {"bottom_family", "bottom_code", "volume_family", "volume_code", "signal_code"}.issubset(summary_df.columns)
    assert {"bottom_family", "best_signal_code", "best_avg_ret_3d"}.issubset(bottom_family_df.columns)
    assert {"volume_family", "best_signal_code", "best_avg_ret_3d"}.issubset(volume_family_df.columns)
    assert trigger_df["signal_code"].nunique() > 0
    assert summary_df["sample_count"].max() >= 1


def test_strategy_ranking_and_latest_hits_use_1d_priority():
    summary_df = pd.DataFrame(
        [
            {
                "bottom_family": "pos120",
                "bottom_code": "B_a",
                "volume_family": "volume_ratio",
                "volume_code": "V_a",
                "signal_code": "A",
                "sample_count": 20,
                "avg_ret_1d": 0.08,
                "median_ret_1d": 0.04,
                "win_rate_1d": 0.7,
                "avg_ret_3d": 0.03,
                "median_ret_3d": 0.02,
                "win_rate_3d": 0.6,
                "is_low_sample": False,
            },
            {
                "bottom_family": "near_120_low",
                "bottom_code": "B_b",
                "volume_family": "vol_spike_5",
                "volume_code": "V_b",
                "signal_code": "B",
                "sample_count": 20,
                "avg_ret_1d": 0.03,
                "median_ret_1d": 0.02,
                "win_rate_1d": 0.6,
                "avg_ret_3d": 0.09,
                "median_ret_3d": 0.08,
                "win_rate_3d": 0.7,
                "is_low_sample": False,
            },
        ]
    )
    trigger_df = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240110",
                "bottom_family": "pos120",
                "bottom_code": "B_a",
                "volume_family": "volume_ratio",
                "volume_code": "V_a",
                "signal_code": "A",
                "close_qfq": 10.0,
                "pct_chg": 2.0,
                "volume_ratio": 1.8,
                "turnover_rate_f": 2.4,
                "ret_1d": 0.01,
                "ret_3d": 0.02,
            },
            {
                "ts_code": "000002.SZ",
                "trade_date": "20240110",
                "bottom_family": "near_120_low",
                "bottom_code": "B_b",
                "volume_family": "vol_spike_5",
                "volume_code": "V_b",
                "signal_code": "B",
                "close_qfq": 11.0,
                "pct_chg": 3.0,
                "volume_ratio": 1.9,
                "turnover_rate_f": 2.2,
                "ret_1d": 0.02,
                "ret_3d": 0.03,
            },
        ]
    )

    ranking_df = build_strategy_ranking(summary_df)
    latest_hits_df = build_latest_hits(trigger_df, ranking_df)

    assert ranking_df.iloc[0]["signal_code"] == "A"
    assert ranking_df.iloc[0]["strategy_rank_1d"] == 1
    assert set(["avg_ret_1d", "win_rate_1d", "avg_ret_3d", "win_rate_3d"]).issubset(ranking_df.columns)
    assert latest_hits_df.iloc[0]["signal_code"] == "A"
    assert latest_hits_df.iloc[0]["strategy_avg_ret_1d"] >= latest_hits_df.iloc[-1]["strategy_avg_ret_1d"]


def test_write_outputs_creates_summary_and_trigger_files(tmp_path: Path, monkeypatch):
    summary_df = pd.DataFrame(
        [
            {
                "bottom_family": "pos120",
                "bottom_code": "B_pos120_le_20",
                "volume_family": "volume_ratio",
                "volume_code": "V_vr_gt_15",
                "signal_code": "B_pos120_le_20__V_vr_gt_15",
                "sample_count": 2,
                "avg_ret_1d": 0.01,
                "median_ret_1d": 0.01,
                "win_rate_1d": 0.5,
                "avg_ret_3d": 0.03,
                "median_ret_3d": 0.03,
                "win_rate_3d": 1.0,
                "is_low_sample": True,
            }
        ]
    )
    trigger_df = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240101",
                "signal_code": "B_pos120_le_20__V_vr_gt_15",
                "ret_1d": 0.02,
                "ret_3d": 0.05,
            }
        ]
    )
    bottom_family_df = pd.DataFrame(
        [{"bottom_family": "pos120", "best_signal_code": "B_pos120_le_20__V_vr_gt_15", "best_avg_ret_3d": 0.03}]
    )
    volume_family_df = pd.DataFrame(
        [{"volume_family": "volume_ratio", "best_signal_code": "B_pos120_le_20__V_vr_gt_15", "best_avg_ret_3d": 0.03}]
    )
    strategy_ranking_df = pd.DataFrame(
        [
            {
                "strategy_rank_1d": 1,
                "strategy_rank_3d": 1,
                "signal_code": "B_pos120_le_20__V_vr_gt_15",
                "avg_ret_1d": 0.01,
                "win_rate_1d": 0.5,
                "avg_ret_3d": 0.03,
                "win_rate_3d": 1.0,
            }
        ]
    )
    latest_hits_df = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240101",
                "signal_code": "B_pos120_le_20__V_vr_gt_15",
                "strategy_avg_ret_1d": 0.01,
            }
        ]
    )

    monkeypatch.setattr(module, "datetime", _fixed_datetime_class())

    output_paths = write_outputs(
        summary_df=summary_df,
        trigger_df=trigger_df,
        bottom_family_df=bottom_family_df,
        volume_family_df=volume_family_df,
        strategy_ranking_df=strategy_ranking_df,
        latest_hits_df=latest_hits_df,
        output_dir=tmp_path,
        top_n=10,
    )

    assert (tmp_path / "0418_1630.csv").exists()
    assert (tmp_path / "0418_1630.md").exists()
    assert (tmp_path / "0418_1630_bottom_family.csv").exists()
    assert (tmp_path / "0418_1630_volume_family.csv").exists()
    assert (tmp_path / "0418_1630_triggers.csv").exists()
    assert (tmp_path / "0418_1630_strategy_ranking.csv").exists()
    assert (tmp_path / "0418_1630_latest_hits.csv").exists()
    assert output_paths["summary_md"].name == "0418_1630.md"


def test_run_analysis_uses_query_df_and_returns_non_empty_summary(monkeypatch, tmp_path: Path):
    source = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240101",
                "open_qfq": 10.0,
                "high_qfq": 10.2,
                "low_qfq": 9.8,
                "close_qfq": 10.0,
                "pct_chg": 0.0,
                "vol": 100.0,
                "amount": 1000.0,
                "turnover_rate": 1.0,
                "turnover_rate_f": 1.0,
                "volume_ratio": 0.8,
                "boll_lower_qfq": 9.9,
                "boll_mid_qfq": 10.2,
                "boll_upper_qfq": 10.5,
                "rsi_qfq_6": 45.0,
                "rsi_qfq_12": 45.0,
                "ma_qfq_20": 10.4,
                "ma_qfq_60": 10.6,
                "downdays": 0,
                "updays": 0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240102",
                "open_qfq": 9.8,
                "high_qfq": 9.9,
                "low_qfq": 9.3,
                "close_qfq": 9.4,
                "pct_chg": -6.0,
                "vol": 90.0,
                "amount": 900.0,
                "turnover_rate": 0.9,
                "turnover_rate_f": 0.9,
                "volume_ratio": 0.7,
                "boll_lower_qfq": 9.4,
                "boll_mid_qfq": 9.9,
                "boll_upper_qfq": 10.3,
                "rsi_qfq_6": 29.0,
                "rsi_qfq_12": 38.0,
                "ma_qfq_20": 10.0,
                "ma_qfq_60": 10.4,
                "downdays": 3,
                "updays": 0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240103",
                "open_qfq": 9.5,
                "high_qfq": 9.8,
                "low_qfq": 9.2,
                "close_qfq": 9.7,
                "pct_chg": 3.2,
                "vol": 160.0,
                "amount": 1700.0,
                "turnover_rate": 1.8,
                "turnover_rate_f": 1.8,
                "volume_ratio": 1.7,
                "boll_lower_qfq": 9.3,
                "boll_mid_qfq": 9.8,
                "boll_upper_qfq": 10.1,
                "rsi_qfq_6": 31.0,
                "rsi_qfq_12": 39.0,
                "ma_qfq_20": 9.9,
                "ma_qfq_60": 10.3,
                "downdays": 4,
                "updays": 0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240104",
                "open_qfq": 9.8,
                "high_qfq": 10.3,
                "low_qfq": 9.7,
                "close_qfq": 10.1,
                "pct_chg": 4.1,
                "vol": 240.0,
                "amount": 2600.0,
                "turnover_rate": 2.4,
                "turnover_rate_f": 2.4,
                "volume_ratio": 2.0,
                "boll_lower_qfq": 9.4,
                "boll_mid_qfq": 9.7,
                "boll_upper_qfq": 10.2,
                "rsi_qfq_6": 38.0,
                "rsi_qfq_12": 41.0,
                "ma_qfq_20": 9.8,
                "ma_qfq_60": 10.1,
                "downdays": 0,
                "updays": 1,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240105",
                "open_qfq": 10.0,
                "high_qfq": 10.5,
                "low_qfq": 9.9,
                "close_qfq": 10.4,
                "pct_chg": 3.0,
                "vol": 260.0,
                "amount": 2900.0,
                "turnover_rate": 2.8,
                "turnover_rate_f": 2.8,
                "volume_ratio": 2.1,
                "boll_lower_qfq": 9.6,
                "boll_mid_qfq": 9.9,
                "boll_upper_qfq": 10.4,
                "rsi_qfq_6": 44.0,
                "rsi_qfq_12": 43.0,
                "ma_qfq_20": 9.9,
                "ma_qfq_60": 10.0,
                "downdays": 0,
                "updays": 2,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240108",
                "open_qfq": 9.5,
                "high_qfq": 9.8,
                "low_qfq": 9.2,
                "close_qfq": 9.6,
                "pct_chg": 2.9,
                "vol": 280.0,
                "amount": 3200.0,
                "turnover_rate": 3.0,
                "turnover_rate_f": 3.0,
                "volume_ratio": 2.0,
                "boll_lower_qfq": 9.4,
                "boll_mid_qfq": 9.8,
                "boll_upper_qfq": 10.1,
                "rsi_qfq_6": 28.0,
                "rsi_qfq_12": 35.0,
                "ma_qfq_20": 10.0,
                "ma_qfq_60": 10.2,
                "downdays": 5,
                "updays": 0,
            },
        ]
    )

    monkeypatch.setattr(module, "query_df", lambda sql, params=None: source)
    monkeypatch.setattr(module, "datetime", _fixed_datetime_class())

    result = module.run_analysis(
        start_date="20240101",
        end_date="20240108",
        min_sample=1,
        top_n=5,
        output_dir=tmp_path,
    )

    assert not result["summary_df"].empty
    assert not result["strategy_ranking_df"].empty
    assert not result["latest_hits_df"].empty
    assert (tmp_path / "0418_1630.csv").exists()
    assert (tmp_path / "0418_1630_strategy_ranking.csv").exists()
    assert (tmp_path / "0418_1630_latest_hits.csv").exists()
    assert result["latest_hits_df"].iloc[0]["strategy_avg_ret_1d"] >= result["latest_hits_df"].iloc[-1]["strategy_avg_ret_1d"]


def test_main_accepts_cli_arguments(monkeypatch, tmp_path: Path, capsys):
    monkeypatch.setattr(
        module,
        "run_analysis",
        lambda start_date, end_date, min_sample, top_n, output_dir: {
            "summary_df": pd.DataFrame(
                [{"signal_code": "demo", "sample_count": 1, "avg_ret_3d": 0.02, "win_rate_3d": 1.0}]
            ),
            "strategy_ranking_df": pd.DataFrame(
                [{"signal_code": "demo", "strategy_rank_1d": 1, "avg_ret_1d": 0.03, "win_rate_1d": 1.0}]
            ),
            "output_paths": {"summary_csv": tmp_path / "0418_1630.csv"},
        },
    )

    exit_code = module.main(
        [
            "--start-date",
            "20240101",
            "--end-date",
            "20240131",
            "--min-sample",
            "5",
            "--top-n",
            "3",
            "--output-dir",
            str(tmp_path),
        ]
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert "0418_1630.csv" in stdout
    assert "demo" in stdout
