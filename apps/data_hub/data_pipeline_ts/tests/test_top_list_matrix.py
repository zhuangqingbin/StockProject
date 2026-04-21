from __future__ import annotations

from pathlib import Path

import pandas as pd

from apps.data_hub.data_pipeline_ts.analysis.top_list_strategies import (
    top_list_matrix as module,
)


def test_main_prints_context_and_result_paths(monkeypatch, tmp_path: Path, capsys):
    captured = {}

    def fake_run_analysis(**kwargs):
        captured["kwargs"] = kwargs
        return {
            "compact_df": pd.DataFrame([{"signal_code": "demo"}]),
            "output_paths": {
                "summary_csv": tmp_path / "0422_1200.csv",
                "summary_md": tmp_path / "0422_1200.md",
            },
        }

    monkeypatch.setattr(module, "run_analysis", fake_run_analysis)

    exit_code = module.main(
        [
            "--start-date",
            "20240101",
            "--end-date",
            "20240131",
            "--output-dir",
            str(tmp_path),
        ]
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert captured["kwargs"] == {
        "start_date": "20240101",
        "end_date": "20240131",
        "min_sample": 30,
        "top_n": 20,
        "output_dir": tmp_path,
        "show_progress": True,
    }
    assert "strategy = top_list_matrix" in stdout
    assert "description = 龙虎榜策略矩阵" in stdout
    assert "source_tables = stock_stk_factor_pro, stock_top_inst, stock_top_list" in stdout
    assert "requested_date_range = 20240101 -> 20240131" in stdout
    assert f"output_dir = {tmp_path}" in stdout
    assert "==> summary_csv = " in stdout
    assert "==> summary_md = " in stdout
    assert "==> rows = 1" in stdout


def test_loaders_merge_and_build_core_top_list_features(monkeypatch):
    base_df = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240129",
                "close_qfq": 10.0,
                "open_qfq": 9.8,
                "high_qfq": 10.2,
                "low_qfq": 9.7,
                "pct_chg": 1.0,
                "amount": 1000.0,
                "vol": 100.0,
                "volume_ratio": 0.9,
                "turnover_rate_f": 1.5,
                "boll_lower_qfq": 9.5,
                "rsi_qfq_6": 43.0,
                "ma_qfq_5": 9.9,
                "ma_qfq_20": 10.4,
                "ma_qfq_60": 10.7,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240130",
                "close_qfq": 10.7,
                "open_qfq": 10.1,
                "high_qfq": 10.9,
                "low_qfq": 10.0,
                "pct_chg": 7.0,
                "amount": 1800.0,
                "vol": 180.0,
                "volume_ratio": 1.8,
                "turnover_rate_f": 4.2,
                "boll_lower_qfq": 9.6,
                "rsi_qfq_6": 59.0,
                "ma_qfq_5": 10.1,
                "ma_qfq_20": 10.3,
                "ma_qfq_60": 10.6,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240131",
                "close_qfq": 11.0,
                "open_qfq": 10.8,
                "high_qfq": 11.1,
                "low_qfq": 10.7,
                "pct_chg": 2.8,
                "amount": 1500.0,
                "vol": 150.0,
                "volume_ratio": 1.2,
                "turnover_rate_f": 3.4,
                "boll_lower_qfq": 9.7,
                "rsi_qfq_6": 61.0,
                "ma_qfq_5": 10.4,
                "ma_qfq_20": 10.4,
                "ma_qfq_60": 10.6,
            },
        ]
    )
    top_inst_df = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240130",
                "buy": 30000000.0,
                "buy_rate": 6.0,
                "sell": 5000000.0,
                "sell_rate": 1.0,
                "net_buy": 25000000.0,
                "reason": "日涨幅偏离值达到7%的前五只证券",
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240131",
                "buy": 8000000.0,
                "buy_rate": 1.5,
                "sell": 18000000.0,
                "sell_rate": 3.0,
                "net_buy": -10000000.0,
                "reason": "日振幅值达到15%的前五只证券",
            },
        ]
    )
    top_list_df = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240130",
                "net_amount": 30000000.0,
                "net_rate": 8.5,
                "amount_rate": 23.0,
                "l_buy": 50000000.0,
                "l_sell": 20000000.0,
                "l_amount": 70000000.0,
                "reason": "日涨幅偏离值达到7%的前五只证券",
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240131",
                "net_amount": -9000000.0,
                "net_rate": -3.5,
                "amount_rate": 11.0,
                "l_buy": 15000000.0,
                "l_sell": 24000000.0,
                "l_amount": 39000000.0,
                "reason": "连续三个交易日内，涨幅偏离值累计达到20%的证券",
            },
        ]
    )

    monkeypatch.setattr(module, "load_base_frame", lambda start_date, end_date: base_df.copy())
    monkeypatch.setattr(module, "load_top_inst_frame", lambda start_date, end_date: top_inst_df.copy())
    monkeypatch.setattr(module, "load_top_list_frame", lambda start_date, end_date: top_list_df.copy())

    merged = module.load_analysis_frame("20240101", "20240131")
    features = module.build_features(merged)

    day1 = features.loc[features["trade_date"] == "20240130"].iloc[0]
    day2 = features.loc[features["trade_date"] == "20240131"].iloc[0]
    assert round(day1["inst_net_buy"], 2) == 25000000.0
    assert round(day1["top_list_net_rate"], 2) == 8.5
    assert day1["reason_up_deviation"] == 1
    assert round(day2["top_list_count_3d"], 2) == 2.0
    assert day2["top_list_streak_2d"] == 1
    assert round(day1["ret_1d"], 6) == round(11.0 / 10.7 - 1.0, 6)
