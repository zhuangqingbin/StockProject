from __future__ import annotations

from pathlib import Path

import pandas as pd

from apps.data_hub.data_pipeline_ts.analysis.flow_chip_northbound_strategies import (
    flow_chip_northbound_matrix as module,
)


def test_main_prints_context_and_result_paths(monkeypatch, tmp_path: Path, capsys):
    captured = {}

    def fake_run_analysis(**kwargs):
        captured["kwargs"] = kwargs
        return {
            "compact_df": pd.DataFrame([{"signal_code": "demo"}]),
            "output_paths": {
                "summary_csv": tmp_path / "0421_1200.csv",
                "summary_md": tmp_path / "0421_1200.md",
            },
        }

    monkeypatch.setattr(
        module,
        "run_analysis",
        fake_run_analysis,
    )

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
    assert "strategy = flow_chip_northbound_matrix" in stdout
    assert "source_tables = stock_stk_factor_pro, stock_money_flow, stock_cyq_perf, stock_hk_hold" in stdout
    assert "requested_date_range = 20240101 -> 20240131" in stdout
    assert f"output_dir = {tmp_path}" in stdout
    assert "==> summary_csv = " in stdout
    assert "==> summary_md = " in stdout
    assert "==> rows = 1" in stdout


def test_run_analysis_returns_compact_and_output_contract_and_writes_timestamped_files(monkeypatch, tmp_path: Path, capsys):
    class FixedDatetime:
        @staticmethod
        def now():
            return pd.Timestamp("2026-04-21 12:00:00").to_pydatetime()

    base_frame = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240129",
                "pct_chg": 1.0,
                "open_qfq": 9.8,
                "high_qfq": 10.2,
                "low_qfq": 9.6,
                "close_qfq": 10.0,
                "boll_lower_qfq": 9.5,
                "rsi_qfq_6": 45.0,
                "rsi_qfq_12": 48.0,
                "ma_qfq_20": 10.4,
                "ma_qfq_60": 10.8,
                "vol": 100.0,
                "amount": 1000.0,
                "turnover_rate": 1.0,
                "turnover_rate_f": 1.2,
                "volume_ratio": 0.8,
                "downdays": 0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240130",
                "pct_chg": 2.0,
                "open_qfq": 10.0,
                "high_qfq": 10.5,
                "low_qfq": 9.7,
                "close_qfq": 10.5,
                "boll_lower_qfq": 9.2,
                "rsi_qfq_6": 35.0,
                "rsi_qfq_12": 40.0,
                "ma_qfq_20": 10.2,
                "ma_qfq_60": 10.7,
                "vol": 120.0,
                "amount": 1200.0,
                "turnover_rate": 1.1,
                "turnover_rate_f": 1.3,
                "volume_ratio": 1.0,
                "downdays": 0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240131",
                "pct_chg": 3.0,
                "open_qfq": 10.4,
                "high_qfq": 11.0,
                "low_qfq": 10.2,
                "close_qfq": 11.0,
                "boll_lower_qfq": 9.1,
                "rsi_qfq_6": 32.0,
                "rsi_qfq_12": 37.0,
                "ma_qfq_20": 10.0,
                "ma_qfq_60": 10.5,
                "vol": 140.0,
                "amount": 1400.0,
                "turnover_rate": 1.4,
                "turnover_rate_f": 1.6,
                "volume_ratio": 1.4,
                "downdays": 0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240201",
                "pct_chg": 4.0,
                "open_qfq": 10.8,
                "high_qfq": 11.6,
                "low_qfq": 10.6,
                "close_qfq": 11.5,
                "boll_lower_qfq": 9.2,
                "rsi_qfq_6": 42.0,
                "rsi_qfq_12": 44.0,
                "ma_qfq_20": 9.9,
                "ma_qfq_60": 10.3,
                "vol": 160.0,
                "amount": 1600.0,
                "turnover_rate": 1.6,
                "turnover_rate_f": 1.8,
                "volume_ratio": 1.7,
                "downdays": 0,
            },
        ]
    )
    money_flow_frame = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240129",
                "buy_elg_amount": 100.0,
                "sell_elg_amount": 20.0,
                "buy_lg_amount": 50.0,
                "sell_lg_amount": 10.0,
                "buy_sm_amount": 20.0,
                "sell_sm_amount": 30.0,
                "buy_md_amount": 40.0,
                "sell_md_amount": 35.0,
                "net_mf_amount": 135.0,
                "main_net": 120.0,
                "elg_net": 80.0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240130",
                "buy_elg_amount": 120.0,
                "sell_elg_amount": 40.0,
                "buy_lg_amount": 70.0,
                "sell_lg_amount": 30.0,
                "buy_sm_amount": 25.0,
                "sell_sm_amount": 20.0,
                "buy_md_amount": 45.0,
                "sell_md_amount": 44.0,
                "net_mf_amount": 141.0,
                "main_net": 160.0,
                "elg_net": 80.0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240131",
                "buy_elg_amount": 130.0,
                "sell_elg_amount": 50.0,
                "buy_lg_amount": 80.0,
                "sell_lg_amount": 40.0,
                "buy_sm_amount": 30.0,
                "sell_sm_amount": 25.0,
                "buy_md_amount": 55.0,
                "sell_md_amount": 50.0,
                "net_mf_amount": 150.0,
                "main_net": 170.0,
                "elg_net": 80.0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240201",
                "buy_elg_amount": 140.0,
                "sell_elg_amount": 60.0,
                "buy_lg_amount": 90.0,
                "sell_lg_amount": 50.0,
                "buy_sm_amount": 35.0,
                "sell_sm_amount": 30.0,
                "buy_md_amount": 60.0,
                "sell_md_amount": 58.0,
                "net_mf_amount": 155.0,
                "main_net": 180.0,
                "elg_net": 80.0,
            },
        ]
    )
    cyq_perf_frame = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240129",
                "winner_rate": 40.0,
                "cost_5pct": 8.0,
                "cost_95pct": 8.2,
                "weight_avg": 4.0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240130",
                "winner_rate": 41.0,
                "cost_5pct": 8.2,
                "cost_95pct": 8.4,
                "weight_avg": 4.0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240131",
                "winner_rate": 42.0,
                "cost_5pct": 8.4,
                "cost_95pct": 8.6,
                "weight_avg": 4.0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240201",
                "winner_rate": 43.0,
                "cost_5pct": 8.6,
                "cost_95pct": 8.8,
                "weight_avg": 4.0,
            },
        ]
    )
    hk_hold_frame = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240129",
                "hk_vol": 1000.0,
                "hk_ratio": 2.0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240130",
                "hk_vol": 1200.0,
                "hk_ratio": 2.4,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240131",
                "hk_vol": 1300.0,
                "hk_ratio": 2.9,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240201",
                "hk_vol": 1400.0,
                "hk_ratio": 3.2,
            },
        ]
    )

    monkeypatch.setattr(module, "datetime", FixedDatetime)
    monkeypatch.setattr(module, "load_base_frame", lambda start_date, end_date=None: base_frame)
    monkeypatch.setattr(module, "load_money_flow_frame", lambda start_date, end_date=None: money_flow_frame)
    monkeypatch.setattr(module, "load_cyq_perf_frame", lambda start_date, end_date=None: cyq_perf_frame)
    monkeypatch.setattr(module, "load_hk_hold_frame", lambda start_date, end_date=None: hk_hold_frame)
    monkeypatch.setattr(
        module,
        "build_signal_rule_defs",
        lambda: [
            module.SignalRuleDef(
                family="test_family",
                code="test_rule",
                description="main_net_ratio > 0.02",
                predicate=lambda df: df["main_net_ratio"] > 0.02,
            )
        ],
    )

    result = module.run_analysis(
        start_date="20240101",
        end_date="20240131",
        min_sample=5,
        top_n=3,
        output_dir=tmp_path,
        show_progress=False,
    )

    stdout = capsys.readouterr().out
    assert "==> load_base_frame" in stdout
    assert "==> load_money_flow_frame" in stdout
    assert "==> load_cyq_perf_frame" in stdout
    assert "==> load_hk_hold_frame" in stdout
    assert "==> load_base_frame done | loaded_rows = 4 | loaded_stocks = 1 | date_range = 20240101 -> 20240201" in stdout
    assert "==> merge_side_frames" in stdout
    assert "==> build_features" in stdout
    assert "==> summarize_signal_matrix" in stdout
    assert "==> build_compact_summary" in stdout
    assert "==> build_signal_code_markdown" in stdout
    assert "==> write_outputs" in stdout

    assert set(result) >= {
        "base_df",
        "merged_df",
        "featured_df",
        "summary_df",
        "trigger_df",
        "compact_df",
        "output_paths",
    }
    assert result["base_df"].equals(base_frame)
    assert len(result["merged_df"]) == 4
    assert len(result["featured_df"]) == 4
    assert result["summary_df"].shape[0] == 1
    assert result["trigger_df"]["trade_date"].max() == "20240131"
    assert result["compact_df"].iloc[0]["latest_trade_date"] == "20240131"

    output_paths = result["output_paths"]
    assert output_paths["summary_csv"].name == "0421_1200.csv"
    assert output_paths["summary_md"].name == "0421_1200.md"
    assert output_paths["summary_csv"].exists()
    assert output_paths["summary_md"].exists()
    assert output_paths["summary_csv"].read_text(encoding="utf-8").startswith("strategy_family,signal_code")
    assert "| strategy_family | signal_code | description |" in output_paths["summary_md"].read_text(encoding="utf-8")


def test_summarize_signal_matrix_uses_tqdm_when_progress_enabled(monkeypatch):
    calls = []

    class FakeTqdm:
        def __init__(self, **kwargs):
            calls.append(kwargs)
            self.updates = 0
            self.closed = False

        def update(self, count):
            self.updates += count

        def close(self):
            self.closed = True

    frame = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240101",
                "main_net_ratio": 0.05,
                "ret_1d": 0.01,
                "ret_3d": 0.03,
                "close_qfq": 10.0,
                "pct_chg": 1.0,
                "volume_ratio": 1.2,
                "turnover_rate_f": 1.0,
            }
        ]
    )
    rule_defs = [
        module.SignalRuleDef(
            family="test_family",
            code="rule_one",
            description="main_net_ratio > 0.02",
            predicate=lambda df: df["main_net_ratio"] > 0.02,
        ),
        module.SignalRuleDef(
            family="test_family",
            code="rule_two",
            description="main_net_ratio > 0.10",
            predicate=lambda df: df["main_net_ratio"] > 0.10,
        ),
    ]

    monkeypatch.setattr(module, "tqdm", FakeTqdm)

    summary_df, trigger_df = module.summarize_signal_matrix(frame, rule_defs=rule_defs, min_sample=1, show_progress=True)

    assert calls == [{"total": 2, "desc": "Scanning strategies", "unit": "combo"}]
    assert summary_df["signal_code"].tolist() == ["rule_one"]
    assert trigger_df["signal_code"].tolist() == ["rule_one"]
    assert len(summary_df) == 1


def test_analysis_readme_mentions_flow_chip_northbound_strategies():
    readme_path = Path(__file__).resolve().parents[1] / "analysis" / "README.md"
    assert "flow_chip_northbound_strategies" in readme_path.read_text(encoding="utf-8")


def test_feature_engineering_loaders_merge_and_build_features(monkeypatch):
    base_frame = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240129",
                "pct_chg": 1.0,
                "open_qfq": 9.8,
                "high_qfq": 10.2,
                "low_qfq": 9.6,
                "close_qfq": 10.0,
                "boll_lower_qfq": 9.5,
                "rsi_qfq_6": 45.0,
                "rsi_qfq_12": 48.0,
                "ma_qfq_20": 10.4,
                "ma_qfq_60": 10.8,
                "vol": 100.0,
                "amount": 1000.0,
                "turnover_rate": 1.0,
                "turnover_rate_f": 1.2,
                "volume_ratio": 0.8,
                "downdays": 0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240130",
                "pct_chg": 2.0,
                "open_qfq": 10.0,
                "high_qfq": 10.5,
                "low_qfq": 9.7,
                "close_qfq": 10.5,
                "boll_lower_qfq": 9.2,
                "rsi_qfq_6": 35.0,
                "rsi_qfq_12": 40.0,
                "ma_qfq_20": 10.2,
                "ma_qfq_60": 10.7,
                "vol": 120.0,
                "amount": 1200.0,
                "turnover_rate": 1.1,
                "turnover_rate_f": 1.3,
                "volume_ratio": 1.0,
                "downdays": 0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240131",
                "pct_chg": 3.0,
                "open_qfq": 10.4,
                "high_qfq": 11.0,
                "low_qfq": 10.2,
                "close_qfq": 11.0,
                "boll_lower_qfq": 9.1,
                "rsi_qfq_6": 32.0,
                "rsi_qfq_12": 37.0,
                "ma_qfq_20": 10.0,
                "ma_qfq_60": 10.5,
                "vol": 140.0,
                "amount": 1400.0,
                "turnover_rate": 1.4,
                "turnover_rate_f": 1.6,
                "volume_ratio": 1.4,
                "downdays": 0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240201",
                "pct_chg": 4.0,
                "open_qfq": 10.8,
                "high_qfq": 11.6,
                "low_qfq": 10.6,
                "close_qfq": 11.5,
                "boll_lower_qfq": 9.2,
                "rsi_qfq_6": 42.0,
                "rsi_qfq_12": 44.0,
                "ma_qfq_20": 9.9,
                "ma_qfq_60": 10.3,
                "vol": 160.0,
                "amount": 1600.0,
                "turnover_rate": 1.6,
                "turnover_rate_f": 1.8,
                "volume_ratio": 1.7,
                "downdays": 0,
            },
        ]
    )
    money_flow_frame = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240129",
                "buy_elg_amount": 100.0,
                "sell_elg_amount": 20.0,
                "buy_lg_amount": 50.0,
                "sell_lg_amount": 10.0,
                "buy_sm_amount": 20.0,
                "sell_sm_amount": 30.0,
                "buy_md_amount": 40.0,
                "sell_md_amount": 35.0,
                "net_mf_amount": 135.0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240130",
                "buy_elg_amount": 120.0,
                "sell_elg_amount": 40.0,
                "buy_lg_amount": 70.0,
                "sell_lg_amount": 30.0,
                "buy_sm_amount": 25.0,
                "sell_sm_amount": 20.0,
                "buy_md_amount": 45.0,
                "sell_md_amount": 44.0,
                "net_mf_amount": 141.0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240131",
                "buy_elg_amount": 130.0,
                "sell_elg_amount": 50.0,
                "buy_lg_amount": 80.0,
                "sell_lg_amount": 40.0,
                "buy_sm_amount": 30.0,
                "sell_sm_amount": 25.0,
                "buy_md_amount": 55.0,
                "sell_md_amount": 50.0,
                "net_mf_amount": 150.0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240201",
                "buy_elg_amount": 140.0,
                "sell_elg_amount": 60.0,
                "buy_lg_amount": 90.0,
                "sell_lg_amount": 50.0,
                "buy_sm_amount": 35.0,
                "sell_sm_amount": 30.0,
                "buy_md_amount": 60.0,
                "sell_md_amount": 58.0,
                "net_mf_amount": 155.0,
            },
        ]
    )
    cyq_perf_frame = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240129",
                "winner_rate": 40.0,
                "cost_5pct": 8.0,
                "cost_95pct": 8.2,
                "weight_avg": 4.0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240130",
                "winner_rate": 41.0,
                "cost_5pct": 8.2,
                "cost_95pct": 8.4,
                "weight_avg": 4.0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240131",
                "winner_rate": 42.0,
                "cost_5pct": 8.4,
                "cost_95pct": 8.6,
                "weight_avg": 4.0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240201",
                "winner_rate": 43.0,
                "cost_5pct": 8.6,
                "cost_95pct": 8.8,
                "weight_avg": 4.0,
            },
        ]
    )
    hk_hold_frame = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240129",
                "hk_vol": 1000.0,
                "hk_ratio": 2.0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240130",
                "hk_vol": 1200.0,
                "hk_ratio": 2.4,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240131",
                "hk_vol": 1300.0,
                "hk_ratio": 2.9,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240201",
                "hk_vol": 1400.0,
                "hk_ratio": 3.2,
            },
        ]
    )
    seen_queries: list[tuple[str, dict | None]] = []

    def fake_query_df(sql: str, params=None):
        seen_queries.append((sql, params))
        if "FROM stock_stk_factor_pro" in sql:
            return base_frame
        if "FROM stock_money_flow" in sql:
            return money_flow_frame
        if "FROM stock_cyq_perf" in sql:
            return cyq_perf_frame
        if "FROM stock_hk_hold" in sql:
            return hk_hold_frame
        raise AssertionError(sql)

    monkeypatch.setattr(module, "query_df", fake_query_df)

    loaded_base = module.load_base_frame("20240101", "20240131")
    loaded_money_flow = module.load_money_flow_frame("20240101", "20240131")
    loaded_cyq_perf = module.load_cyq_perf_frame("20240101", "20240131")
    loaded_hk_hold = module.load_hk_hold_frame("20240101", "20240131")
    merged = module.merge_side_frames(loaded_base, loaded_money_flow, loaded_cyq_perf, loaded_hk_hold)
    featured = module.build_features(merged)

    assert seen_queries[0][1] == {"start_date": "20240101", "load_end_date": "20240210"}
    assert {
        "pct_chg",
        "boll_lower_qfq",
        "rsi_qfq_6",
        "rsi_qfq_12",
        "ma_qfq_20",
        "ma_qfq_60",
    }.issubset(set(loaded_base.columns))
    assert loaded_money_flow.loc[0, "main_net"] == 120.0
    assert loaded_money_flow.loc[0, "elg_net"] == 80.0
    assert round(loaded_cyq_perf.loc[0, "chip_spread"], 6) == round((8.2 - 8.0) / 4.0, 6)
    assert list(loaded_hk_hold.columns) == ["ts_code", "trade_date", "hk_vol", "hk_ratio"]
    assert len(merged) == len(base_frame)

    required_feature_columns = {
        "rolling_low_120",
        "rolling_high_120",
        "pos120",
        "close_to_low_120",
        "main_net",
        "elg_net",
        "main_net_ratio",
        "elg_net_ratio",
        "mf_net_ratio",
        "main_net_change_2d",
        "main_net_change_3d",
        "elg_net_change_2d",
        "chip_spread",
        "chip_spread_change_3d",
        "winner_rate_change_3d",
        "close_vs_weight_avg",
        "hk_ratio_change_3d",
        "hk_vol_change_3d",
        "is_bottom_zone",
        "ret_1d",
        "ret_3d",
    }
    assert required_feature_columns.issubset(set(featured.columns))

    row_20240130 = featured.loc[featured["trade_date"] == "20240130"].iloc[0]
    row_20240131 = featured.loc[featured["trade_date"] == "20240131"].iloc[0]
    row_20240201 = featured.loc[featured["trade_date"] == "20240201"].iloc[0]
    row_20240129 = featured.loc[featured["trade_date"] == "20240129"].iloc[0]

    assert row_20240130["main_net"] > 0
    assert row_20240130["chip_spread"] < 0.1
    assert row_20240130["close_vs_weight_avg"] > 1.0
    assert round(row_20240130["close_to_low_120"], 6) == round(10.5 / 9.6, 6)
    assert round(row_20240130["main_net_ratio"], 6) == round(120.0 / (120.0 + 40.0 + 70.0 + 30.0), 6)
    assert round(row_20240130["elg_net_ratio"], 6) == round((120.0 - 40.0) / (120.0 + 40.0 + 70.0 + 30.0), 6)
    assert round(row_20240201["main_net_change_2d"], 6) == 0.0
    assert round(row_20240201["main_net_change_3d"], 6) == 0.0
    assert round(row_20240201["elg_net_change_2d"], 6) == 0.0
    assert round(row_20240201["hk_ratio_change_3d"], 6) == round(3.2 - 2.0, 6)
    assert round(row_20240201["hk_vol_change_3d"], 6) == round(1400.0 - 1000.0, 6)
    assert bool(row_20240129["is_bottom_zone"]) is True
    assert round(row_20240131["ret_1d"], 6) == round(11.5 / 11.0 - 1.0, 6)
    assert round(row_20240129["ret_3d"], 6) == round(11.5 / 10.0 - 1.0, 6)


def test_build_signal_rule_defs_expands_many_unique_rules():
    rule_defs = module.build_signal_rule_defs()

    assert len(rule_defs) >= 200
    assert len({rule.code for rule in rule_defs}) == len(rule_defs)
    assert {
        "plain_main_flow",
        "bottom_main_flow",
        "plain_chip_repair",
        "bottom_chip_repair",
        "plain_northbound_support",
        "bottom_northbound_support",
        "plain_resonance",
        "bottom_resonance",
    }.issubset({rule.family for rule in rule_defs})
    assert module.SignalRuleDef.__dataclass_params__.frozen is True


def test_write_outputs_uses_fixed_timestamp_stem(monkeypatch, tmp_path: Path):
    class FixedDatetime:
        @staticmethod
        def now():
            return pd.Timestamp("2026-04-21 12:00:00").to_pydatetime()

    monkeypatch.setattr(module, "datetime", FixedDatetime)

    compact_df = pd.DataFrame([{"strategy_family": "demo", "signal_code": "demo__001"}])
    output_paths = module.write_outputs(compact_df, "## Signal Codes\n", tmp_path)

    assert output_paths["summary_csv"].name == "0421_1200.csv"
    assert output_paths["summary_md"].name == "0421_1200.md"
    assert output_paths["summary_csv"].exists()
    assert output_paths["summary_md"].exists()
    assert output_paths["summary_csv"].read_text(encoding="utf-8").strip().startswith("strategy_family")
    assert output_paths["summary_md"].read_text(encoding="utf-8") == "## Signal Codes\n"


def test_summarize_signal_matrix_and_compact_summary_build_expected_columns():
    rule_defs = [
        rule
        for rule in module.build_signal_rule_defs()
        if rule.code
        in {
            "plain_main_flow__main_net_ratio_gt_0p02",
            "bottom_main_flow__plain_main_flow__main_net_ratio_gt_0p02",
        }
    ]
    frame = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240101",
                "main_net_ratio": 0.03,
                "is_bottom_zone": False,
                "close_qfq": 10.0,
                "pct_chg": 1.0,
                "volume_ratio": 0.9,
                "turnover_rate_f": 1.1,
                "ret_1d": 0.05,
                "ret_3d": 0.10,
            },
            {
                "ts_code": "000002.SZ",
                "trade_date": "20240102",
                "main_net_ratio": 0.05,
                "is_bottom_zone": True,
                "close_qfq": 10.5,
                "pct_chg": -0.5,
                "volume_ratio": 1.2,
                "turnover_rate_f": 1.3,
                "ret_1d": -0.02,
                "ret_3d": 0.03,
            },
            {
                "ts_code": "000003.SZ",
                "trade_date": "20240102",
                "main_net_ratio": 0.07,
                "is_bottom_zone": True,
                "close_qfq": 10.8,
                "pct_chg": 0.4,
                "volume_ratio": 1.5,
                "turnover_rate_f": 1.4,
                "ret_1d": 0.01,
                "ret_3d": 0.02,
            },
        ]
    )

    summary_df, trigger_df = module.summarize_signal_matrix(frame, rule_defs=rule_defs, min_sample=1, show_progress=False)
    compact_df = module.build_compact_summary(summary_df, trigger_df)

    assert list(compact_df.columns) == [
        "strategy_family",
        "signal_code",
        "sample_count",
        "win_rate_1d",
        "avg_ret_1d",
        "var_ret_1d",
        "win_rate_3d",
        "avg_ret_3d",
        "var_ret_3d",
        "latest_trade_date",
        "latest_hit_stocks",
    ]
    assert {"strategy_family", "signal_code"}.issubset(set(summary_df.columns))
    assert set(trigger_df.columns) >= {
        "ts_code",
        "trade_date",
        "strategy_family",
        "signal_code",
        "close_qfq",
        "pct_chg",
        "volume_ratio",
        "turnover_rate_f",
        "ret_1d",
        "ret_3d",
    }

    plain_row = compact_df.loc[compact_df["signal_code"] == "plain_main_flow__main_net_ratio_gt_0p02"].iloc[0]
    bottom_row = compact_df.loc[
        compact_df["signal_code"] == "bottom_main_flow__plain_main_flow__main_net_ratio_gt_0p02"
    ].iloc[0]
    assert plain_row["strategy_family"] == "plain_main_flow"
    assert bottom_row["strategy_family"] == "bottom_main_flow"
    assert plain_row["latest_trade_date"] == "20240102"
    assert plain_row["latest_hit_stocks"] == "000002.SZ,000003.SZ"
    assert bottom_row["latest_hit_stocks"] == "000002.SZ,000003.SZ"
