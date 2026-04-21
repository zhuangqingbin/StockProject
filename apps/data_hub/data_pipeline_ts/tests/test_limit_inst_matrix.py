from __future__ import annotations

from pathlib import Path

import pandas as pd

from apps.data_hub.data_pipeline_ts.analysis.event_price_action_strategies import (
    limit_inst_matrix as module,
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
    assert "strategy = limit_inst_matrix" in stdout
    assert "description = 涨跌停 + 龙虎榜事件矩阵" in stdout
    assert "source_tables = stock_stk_factor_pro, stock_limit_list_d, stock_top_inst" in stdout
    assert "requested_date_range = 20240101 -> 20240131" in stdout
    assert f"output_dir = {tmp_path}" in stdout
    assert "==> summary_csv = " in stdout
    assert "==> summary_md = " in stdout
    assert "==> rows = 1" in stdout


def test_event_loaders_merge_and_build_features(monkeypatch):
    base_df = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240129",
                "open_qfq": 9.8,
                "high_qfq": 10.2,
                "low_qfq": 9.6,
                "close_qfq": 10.0,
                "pct_chg": 1.0,
                "vol": 100.0,
                "amount": 1000.0,
                "turnover_rate_f": 1.2,
                "volume_ratio": 0.8,
                "boll_lower_qfq": 9.5,
                "rsi_qfq_6": 45.0,
                "rsi_qfq_12": 48.0,
                "ma_qfq_5": 9.9,
                "ma_qfq_20": 10.4,
                "ma_qfq_60": 10.8,
                "downdays": 0,
                "updays": 1,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240130",
                "open_qfq": 10.0,
                "high_qfq": 10.6,
                "low_qfq": 9.7,
                "close_qfq": 10.5,
                "pct_chg": 5.0,
                "vol": 150.0,
                "amount": 1500.0,
                "turnover_rate_f": 3.0,
                "volume_ratio": 1.8,
                "boll_lower_qfq": 9.2,
                "rsi_qfq_6": 34.0,
                "rsi_qfq_12": 39.0,
                "ma_qfq_5": 10.1,
                "ma_qfq_20": 10.2,
                "ma_qfq_60": 10.7,
                "downdays": 0,
                "updays": 2,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240131",
                "open_qfq": 10.6,
                "high_qfq": 11.0,
                "low_qfq": 10.3,
                "close_qfq": 10.8,
                "pct_chg": 2.0,
                "vol": 180.0,
                "amount": 1800.0,
                "turnover_rate_f": 3.5,
                "volume_ratio": 2.1,
                "boll_lower_qfq": 9.1,
                "rsi_qfq_6": 38.0,
                "rsi_qfq_12": 41.0,
                "ma_qfq_5": 10.4,
                "ma_qfq_20": 10.1,
                "ma_qfq_60": 10.6,
                "downdays": 0,
                "updays": 3,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240201",
                "open_qfq": 10.7,
                "high_qfq": 10.8,
                "low_qfq": 9.9,
                "close_qfq": 10.1,
                "pct_chg": -6.0,
                "vol": 220.0,
                "amount": 2100.0,
                "turnover_rate_f": 4.0,
                "volume_ratio": 2.5,
                "boll_lower_qfq": 9.0,
                "rsi_qfq_6": 29.0,
                "rsi_qfq_12": 35.0,
                "ma_qfq_5": 10.6,
                "ma_qfq_20": 10.2,
                "ma_qfq_60": 10.5,
                "downdays": 1,
                "updays": 0,
            },
        ]
    )
    limit_df = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240130",
                "limit_type": "U",
                "open_times": 1,
                "fd_amount": 80000000.0,
                "limit_times": 1,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240201",
                "limit_type": "D",
                "open_times": 0,
                "fd_amount": 0.0,
                "limit_times": 1,
            },
        ]
    )
    top_inst_df = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240130",
                "inst_buy": 150000000.0,
                "inst_sell": 50000000.0,
                "inst_net_buy": 100000000.0,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240201",
                "inst_buy": 20000000.0,
                "inst_sell": 80000000.0,
                "inst_net_buy": -60000000.0,
            },
        ]
    )
    seen_queries: list[tuple[str, dict | None]] = []

    def fake_query_df(sql: str, params=None):
        seen_queries.append((sql, params))
        if "FROM stock_stk_factor_pro" in sql:
            return base_df
        if "FROM stock_limit_list_d" in sql:
            return limit_df
        if "FROM stock_top_inst" in sql:
            return top_inst_df
        raise AssertionError(sql)

    monkeypatch.setattr(module, "query_df", fake_query_df)

    loaded_base = module.load_base_frame("20240101", "20240131")
    loaded_limit = module.load_limit_frame("20240101", "20240131")
    loaded_inst = module.load_top_inst_frame("20240101", "20240131")
    merged = module.merge_side_frames(loaded_base, loaded_limit, loaded_inst)
    featured = module.build_features(merged)

    assert seen_queries[0][1] == {"start_date": "20240101", "load_end_date": "20240210"}
    assert {"limit_type", "open_times", "fd_amount", "limit_times"}.issubset(loaded_limit.columns)
    assert {"inst_buy", "inst_sell", "inst_net_buy"}.issubset(loaded_inst.columns)
    assert len(merged) == len(base_df)

    required_columns = {
        "ret_1d",
        "ret_3d",
        "rolling_low_120",
        "rolling_high_120",
        "pos120",
        "close_to_low_120",
        "is_bottom_zone",
        "is_limit_up",
        "is_limit_down",
        "is_open_board",
        "is_one_word_board",
        "is_limit_up_first",
        "is_limit_up_multi",
        "inst_net_buy_ratio",
        "inst_gross_turnover_ratio",
        "inst_abs_buy_sell_ratio",
        "oversold_state",
        "volume_expand_state",
        "high_turnover_state",
        "ma_reclaim_state",
        "weak_trend_state",
        "strong_trend_state",
    }
    assert required_columns.issubset(set(featured.columns))

    row_up = featured.loc[featured["trade_date"] == "20240130"].iloc[0]
    row_down = featured.loc[featured["trade_date"] == "20240201"].iloc[0]
    assert bool(row_up["is_limit_up"]) is True
    assert bool(row_up["is_open_board"]) is True
    assert bool(row_up["is_limit_up_first"]) is True
    assert row_up["inst_net_buy_ratio"] > 0
    assert bool(row_down["is_limit_down"]) is True
    assert row_down["inst_net_buy_ratio"] < 0


def test_run_analysis_preserves_empty_side_frame_columns(monkeypatch, tmp_path: Path):
    base_df = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20260303",
                "open_qfq": 10.0,
                "high_qfq": 10.3,
                "low_qfq": 9.8,
                "close_qfq": 10.1,
                "pct_chg": 1.0,
                "vol": 100.0,
                "amount": 1000.0,
                "turnover_rate_f": 1.2,
                "volume_ratio": 1.1,
                "boll_lower_qfq": 9.7,
                "rsi_qfq_6": 42.0,
                "rsi_qfq_12": 45.0,
                "ma_qfq_5": 10.0,
                "ma_qfq_20": 10.2,
                "ma_qfq_60": 10.5,
                "downdays": 0,
                "updays": 1,
            },
            {
                "ts_code": "000001.SZ",
                "trade_date": "20260304",
                "open_qfq": 10.1,
                "high_qfq": 10.4,
                "low_qfq": 9.9,
                "close_qfq": 10.2,
                "pct_chg": 1.0,
                "vol": 110.0,
                "amount": 1050.0,
                "turnover_rate_f": 1.3,
                "volume_ratio": 1.0,
                "boll_lower_qfq": 9.8,
                "rsi_qfq_6": 44.0,
                "rsi_qfq_12": 46.0,
                "ma_qfq_5": 10.1,
                "ma_qfq_20": 10.2,
                "ma_qfq_60": 10.5,
                "downdays": 0,
                "updays": 2,
            },
        ]
    )
    empty_limit_df = module._empty_frame(
        ["ts_code", "trade_date", "limit_type", "open_times", "fd_amount", "limit_times"]
    )
    empty_top_inst_df = module._empty_frame(
        ["ts_code", "trade_date", "inst_buy", "inst_sell", "inst_net_buy"]
    )

    def fake_query_df(sql: str, params=None):
        if "FROM stock_stk_factor_pro" in sql:
            return base_df
        if "FROM stock_limit_list_d" in sql:
            return empty_limit_df
        if "FROM stock_top_inst" in sql:
            return empty_top_inst_df
        raise AssertionError(sql)

    monkeypatch.setattr(module, "query_df", fake_query_df)

    result = module.run_analysis(
        start_date="20260301",
        end_date="20260331",
        min_sample=1,
        top_n=20,
        output_dir=tmp_path,
        show_progress=False,
    )

    assert {"limit_type", "open_times", "fd_amount", "limit_times"}.issubset(result["merged_df"].columns)
    assert {"inst_buy", "inst_sell", "inst_net_buy"}.issubset(result["merged_df"].columns)
    assert {"is_limit_up", "is_limit_down", "inst_net_buy_ratio", "inst_gross_turnover_ratio"}.issubset(
        result["featured_df"].columns
    )
    assert result["compact_df"].empty


def test_build_signal_rule_defs_expands_event_and_state_families():
    rule_defs = module.build_signal_rule_defs()

    assert len(rule_defs) >= 120
    assert len({rule.code for rule in rule_defs}) == len(rule_defs)
    assert {
        "plain_momentum_event",
        "state_momentum_event",
        "plain_reversal_event",
        "state_reversal_event",
        "plain_inst_event",
        "state_inst_event",
    }.issubset({rule.family for rule in rule_defs})


def test_run_analysis_executes_contract_and_prints_stage_lines(monkeypatch, tmp_path: Path, capsys):
    base_df = pd.DataFrame(
        [
            {"ts_code": "000001.SZ", "trade_date": "20240130", "close_qfq": 10.0},
            {"ts_code": "000001.SZ", "trade_date": "20240131", "close_qfq": 10.5},
            {"ts_code": "000002.SZ", "trade_date": "20240201", "close_qfq": 8.8},
        ]
    )
    merged_df = base_df.assign(limit_type=["U", None, "D"])
    featured_df = merged_df.assign(feature_ready=[True, True, True])
    summary_df = pd.DataFrame(
        [
            {
                "strategy_family": "plain_momentum_event",
                "signal_code": "plain_momentum_event__limit_up_first",
                "sample_count": 2,
                "win_rate_1d": 0.5,
                "avg_ret_1d": 0.01,
                "var_ret_1d": 0.0001,
                "win_rate_3d": 0.5,
                "avg_ret_3d": 0.02,
                "var_ret_3d": 0.0002,
                "is_low_sample": False,
            }
        ]
    )
    trigger_df = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240131",
                "strategy_family": "plain_momentum_event",
                "signal_code": "plain_momentum_event__limit_up_first",
            }
        ]
    )
    compact_df = pd.DataFrame([{"signal_code": "plain_momentum_event__limit_up_first"}])
    rule_defs = [module.SignalRuleDef("plain_momentum_event", "demo_rule", "Demo", lambda df: pd.Series(True, index=df.index))]
    output_paths = {"summary_csv": tmp_path / "summary.csv", "summary_md": tmp_path / "summary.md"}
    captured: dict[str, object] = {}

    def fake_load_base_frame(start_date: str, end_date: str | None = None):
        captured["load_base_frame"] = {"start_date": start_date, "end_date": end_date}
        return base_df

    def fake_load_limit_frame(start_date: str, end_date: str | None = None):
        captured["load_limit_frame"] = {"start_date": start_date, "end_date": end_date}
        return pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "20240131", "limit_type": "U"}])

    def fake_load_top_inst_frame(start_date: str, end_date: str | None = None):
        captured["load_top_inst_frame"] = {"start_date": start_date, "end_date": end_date}
        return pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "20240131", "inst_net_buy": 1.0}])

    def fake_merge_side_frames(base_df_arg, limit_df_arg, top_inst_df_arg):
        captured["merge_side_frames"] = {
            "base_rows": len(base_df_arg),
            "limit_rows": len(limit_df_arg),
            "top_inst_rows": len(top_inst_df_arg),
        }
        return merged_df

    def fake_build_features(frame: pd.DataFrame):
        captured["build_features_input_dates"] = frame["trade_date"].tolist()
        return featured_df

    def fake_build_signal_rule_defs():
        captured["build_signal_rule_defs"] = True
        return rule_defs

    def fake_summarize_signal_matrix(frame: pd.DataFrame, rule_defs=None, min_sample=30, show_progress=False):
        captured["summarize_signal_matrix"] = {
            "dates": frame["trade_date"].tolist(),
            "rule_defs": rule_defs,
            "min_sample": min_sample,
            "show_progress": show_progress,
        }
        return summary_df, trigger_df

    def fake_build_compact_summary(summary_df_arg: pd.DataFrame, trigger_df_arg: pd.DataFrame):
        captured["build_compact_summary"] = {
            "summary_rows": len(summary_df_arg),
            "trigger_rows": len(trigger_df_arg),
        }
        return compact_df

    def fake_build_signal_code_markdown(rule_defs_arg):
        captured["build_signal_code_markdown"] = rule_defs_arg
        return "markdown"

    def fake_write_outputs(*, compact_df: pd.DataFrame, signal_code_markdown: str, output_dir: Path):
        captured["write_outputs"] = {
            "rows": len(compact_df),
            "signal_code_markdown": signal_code_markdown,
            "output_dir": output_dir,
        }
        return output_paths

    monkeypatch.setattr(module, "load_base_frame", fake_load_base_frame)
    monkeypatch.setattr(module, "load_limit_frame", fake_load_limit_frame)
    monkeypatch.setattr(module, "load_top_inst_frame", fake_load_top_inst_frame)
    monkeypatch.setattr(module, "merge_side_frames", fake_merge_side_frames)
    monkeypatch.setattr(module, "build_features", fake_build_features)
    monkeypatch.setattr(module, "build_signal_rule_defs", fake_build_signal_rule_defs)
    monkeypatch.setattr(module, "summarize_signal_matrix", fake_summarize_signal_matrix)
    monkeypatch.setattr(module, "build_compact_summary", fake_build_compact_summary)
    monkeypatch.setattr(module, "build_signal_code_markdown", fake_build_signal_code_markdown)
    monkeypatch.setattr(module, "write_outputs", fake_write_outputs)

    result = module.run_analysis(
        start_date="20240101",
        end_date="20240131",
        min_sample=5,
        top_n=10,
        output_dir=tmp_path,
        show_progress=True,
    )

    stdout = capsys.readouterr().out
    assert captured["load_base_frame"] == {"start_date": "20240101", "end_date": "20240131"}
    assert captured["load_limit_frame"] == {"start_date": "20240101", "end_date": "20240131"}
    assert captured["load_top_inst_frame"] == {"start_date": "20240101", "end_date": "20240131"}
    assert captured["merge_side_frames"] == {"base_rows": 3, "limit_rows": 1, "top_inst_rows": 1}
    assert captured["build_features_input_dates"] == ["20240130", "20240131", "20240201"]
    assert captured["summarize_signal_matrix"] == {
        "dates": ["20240130", "20240131"],
        "rule_defs": rule_defs,
        "min_sample": 5,
        "show_progress": True,
    }
    assert captured["build_compact_summary"] == {"summary_rows": 1, "trigger_rows": 1}
    assert captured["build_signal_code_markdown"] == rule_defs
    assert captured["write_outputs"] == {
        "rows": 1,
        "signal_code_markdown": "markdown",
        "output_dir": tmp_path,
    }
    assert result["source_df"] is base_df
    assert result["base_df"] is base_df
    assert result["merged_df"] is merged_df
    assert result["featured_df"] is featured_df
    assert result["summary_df"] is summary_df
    assert result["trigger_df"] is trigger_df
    assert result["compact_df"] is compact_df
    assert result["output_paths"] == output_paths
    assert "==> load_base_frame" in stdout
    assert "loaded_rows=3" in stdout
    assert "loaded_stocks=2" in stdout
    assert "date_range=20240130 -> 20240201" in stdout
    assert "==> build_features" in stdout
    assert "==> Scanning strategies" in stdout
    assert "==> write_outputs" in stdout


def test_analysis_readme_mentions_event_price_action_strategies():
    readme_path = Path("apps/data_hub/data_pipeline_ts/analysis/README.md")
    content = readme_path.read_text(encoding="utf-8")

    assert "- `event_price_action_strategies`：涨跌停、炸板、跌停、龙虎榜事件与主表状态的矩阵分析。" in content


def test_summarize_signal_matrix_and_compact_summary_build_expected_columns():
    rule_defs = [
        module.SignalRuleDef(
            family="plain_momentum_event",
            code="plain_momentum_event__limit_up_first",
            description="首板涨停",
            predicate=lambda df: df["is_limit_up_first"].fillna(False),
        ),
        module.SignalRuleDef(
            family="state_momentum_event",
            code="state_momentum_event__limit_up_first__bottom_zone",
            description="首板涨停 and 底部区",
            predicate=lambda df: df["is_limit_up_first"].fillna(False) & df["is_bottom_zone"].fillna(False),
        ),
    ]
    frame = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240101",
                "is_limit_up_first": True,
                "is_bottom_zone": False,
                "close_qfq": 10.0,
                "pct_chg": 5.0,
                "volume_ratio": 1.6,
                "turnover_rate_f": 2.2,
                "ret_1d": 0.05,
                "ret_3d": 0.10,
            },
            {
                "ts_code": "000002.SZ",
                "trade_date": "20240102",
                "is_limit_up_first": True,
                "is_bottom_zone": True,
                "close_qfq": 10.2,
                "pct_chg": 4.0,
                "volume_ratio": 1.5,
                "turnover_rate_f": 2.0,
                "ret_1d": -0.02,
                "ret_3d": 0.03,
            },
        ]
    )

    summary_df, trigger_df = module.summarize_signal_matrix(
        frame,
        rule_defs=rule_defs,
        min_sample=1,
        show_progress=False,
    )
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
    plain_row = compact_df.loc[compact_df["signal_code"] == "plain_momentum_event__limit_up_first"].iloc[0]
    assert plain_row["strategy_family"] == "plain_momentum_event"
    assert plain_row["latest_trade_date"] == "20240102"
    assert plain_row["latest_hit_stocks"] == "000002.SZ"


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
