from __future__ import annotations

from datetime import datetime as real_datetime
from pathlib import Path

import pandas as pd

from apps.data_hub.data_pipeline_ts.analysis.supply_shock_strategies import (
    supply_shock_matrix as module,
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
    assert "strategy = supply_shock_matrix" in stdout
    assert "description = 供给冲击 / 吸收修复矩阵" in stdout
    assert (
        "source_tables = stock_stk_factor_pro, stock_share_float, stock_stk_holdertrade"
        in stdout
    )
    assert "requested_date_range = 20240101 -> 20240131" in stdout
    assert f"output_dir = {tmp_path}" in stdout
    assert "==> summary_csv = " in stdout
    assert "==> summary_md = " in stdout
    assert "==> rows = 1" in stdout


def test_loaders_and_feature_layer_build_expected_daily_frames(monkeypatch):
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
    share_float_df = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "ann_date": "20240130",
                "float_date": "20240201",
                "float_share": 1000000.0,
                "float_ratio": 1.2,
                "holder_name": "A",
                "share_type": "首发股",
            },
            {
                "ts_code": "000001.SZ",
                "ann_date": "20240131",
                "float_date": "20240131",
                "float_share": 2000000.0,
                "float_ratio": 2.4,
                "holder_name": "B",
                "share_type": "首发原始股",
            },
            {
                "ts_code": "000001.SZ",
                "ann_date": None,
                "float_date": "20240131",
                "float_share": 3000000.0,
                "float_ratio": 3.6,
                "holder_name": "C",
                "share_type": "定增股份",
            },
        ]
    )
    holdertrade_df = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "ann_date": "20240130",
                "holder_name": "Exec A",
                "holder_type": "G",
                "in_de": "DE",
                "change_vol": 100000.0,
                "change_ratio": 1.5,
                "after_share": 500000.0,
                "after_ratio": 4.0,
                "avg_price": 10.0,
                "total_share": 9000000.0,
                "begin_date": "20240129",
                "close_date": "20240131",
            },
            {
                "ts_code": "000001.SZ",
                "ann_date": "20240131",
                "holder_name": "Company B",
                "holder_type": "C",
                "in_de": "IN",
                "change_vol": 150000.0,
                "change_ratio": 2.2,
                "after_share": 650000.0,
                "after_ratio": 5.5,
                "avg_price": 10.2,
                "total_share": 9200000.0,
                "begin_date": "20240130",
                "close_date": "20240201",
            },
            {
                "ts_code": "000001.SZ",
                "ann_date": None,
                "holder_name": "Person C",
                "holder_type": "P",
                "in_de": "DE",
                "change_vol": 120000.0,
                "change_ratio": 1.8,
                "after_share": 450000.0,
                "after_ratio": 3.2,
                "avg_price": 10.3,
                "total_share": 9300000.0,
                "begin_date": "20240131",
                "close_date": "20240201",
            },
        ]
    )
    seen_queries: list[tuple[str, dict | None]] = []

    def fake_query_df(sql: str, params=None):
        seen_queries.append((sql, params))
        if "FROM stock_stk_factor_pro" in sql:
            return base_df
        if "FROM stock_share_float" in sql:
            return share_float_df
        if "FROM stock_stk_holdertrade" in sql:
            return holdertrade_df
        raise AssertionError(sql)

    monkeypatch.setattr(module, "query_df", fake_query_df)

    loaded_base = module.load_base_frame("20240101", "20240131")
    loaded_share = module.load_share_float_frame("20240101", "20240131")
    loaded_holder = module.load_holdertrade_frame("20240101", "20240131")
    share_daily = module.aggregate_share_float_events(loaded_share)
    holder_daily = module.aggregate_holdertrade_events(loaded_holder)
    merged = module.merge_side_frames(loaded_base, share_daily, holder_daily)
    featured = module.build_features(merged)

    assert seen_queries[0][1] == {"start_date": "20240101", "load_end_date": "20240210"}
    assert seen_queries[1][1] == {"start_date": "20240101", "load_end_date": "20240210"}
    assert seen_queries[2][1] == {"start_date": "20240101", "load_end_date": "20240210"}

    assert {
        "ts_code",
        "ann_date",
        "float_date",
        "float_share",
        "float_ratio",
        "holder_name",
        "share_type",
    }.issubset(loaded_share.columns)
    assert {
        "ts_code",
        "ann_date",
        "holder_name",
        "holder_type",
        "in_de",
        "change_vol",
        "change_ratio",
        "after_share",
        "after_ratio",
        "avg_price",
        "total_share",
        "begin_date",
        "close_date",
    }.issubset(loaded_holder.columns)

    assert "sf_ann_event_count" in share_daily.columns
    assert "sf_float_event_count" in share_daily.columns
    assert "sf_ann_total_float_share" in share_daily.columns
    assert "sf_float_total_float_ratio" in share_daily.columns
    assert "sf_ann_ratio_ipo" in share_daily.columns
    assert "sf_float_ratio_private_placement" in share_daily.columns

    assert "ht_ann_event_count" in holder_daily.columns
    assert "ht_begin_event_count" in holder_daily.columns
    assert "ht_close_event_count" in holder_daily.columns
    assert "ht_ann_de_event_count" in holder_daily.columns
    assert "ht_ann_in_total_change_ratio" in holder_daily.columns
    assert "ht_close_de_exec_max_change_ratio" in holder_daily.columns

    assert {"sf_ann_event_count", "ht_ann_event_count"}.issubset(merged.columns)

    expected_columns = {
        "ret_1d",
        "ret_3d",
        "rolling_low_120",
        "rolling_high_120",
        "pos120",
        "close_to_low_120",
        "is_bottom_zone",
        "oversold_state",
        "volume_expand_state",
        "high_turnover_state",
        "ma_reclaim_state",
        "weak_trend_state",
        "strong_trend_state",
        "pullback_state",
        "has_supply_event",
        "has_share_float_event",
        "has_holdertrade_event",
        "has_de_event",
        "has_in_event",
    }
    assert expected_columns.issubset(set(featured.columns))

    row = featured.loc[featured["trade_date"] == "20240131"].iloc[0]
    assert bool(row["has_supply_event"]) is True
    assert bool(row["has_share_float_event"]) is True
    assert bool(row["has_holdertrade_event"]) is True
    assert bool(row["has_de_event"]) is True
    assert bool(row["has_in_event"]) is True


def test_loaders_null_outside_window_prevents_reanchoring(monkeypatch):
    share_float_df = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "ann_date": "20240130",
                "float_date": "20240220",
                "float_share": 1000000.0,
                "float_ratio": 1.2,
                "holder_name": "A",
                "share_type": "首发股",
            }
        ]
    )
    holdertrade_df = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "ann_date": "20240130",
                "holder_name": "Exec A",
                "holder_type": "G",
                "in_de": "DE",
                "change_vol": 100000.0,
                "change_ratio": 1.5,
                "after_share": 500000.0,
                "after_ratio": 4.0,
                "avg_price": 10.0,
                "total_share": 9000000.0,
                "begin_date": "20240220",
                "close_date": "20240221",
            }
        ]
    )

    def fake_query_df(sql: str, params=None):
        if "FROM stock_share_float" in sql:
            return share_float_df
        if "FROM stock_stk_holdertrade" in sql:
            return holdertrade_df
        if "FROM stock_stk_factor_pro" in sql:
            return pd.DataFrame(
                [
                    {
                        "ts_code": "000001.SZ",
                        "trade_date": "20240130",
                        "open_qfq": 10.0,
                        "high_qfq": 10.2,
                        "low_qfq": 9.8,
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
                    }
                ]
            )
        raise AssertionError(sql)

    monkeypatch.setattr(module, "query_df", fake_query_df)

    loaded_share = module.load_share_float_frame("20240101", "20240131")
    loaded_holder = module.load_holdertrade_frame("20240101", "20240131")

    assert loaded_share.loc[0, "ann_date"] == "20240130"
    assert pd.isna(loaded_share.loc[0, "float_date"])
    assert loaded_holder.loc[0, "ann_date"] == "20240130"
    assert pd.isna(loaded_holder.loc[0, "close_date"])

    share_daily = module.aggregate_share_float_events(loaded_share)
    holder_daily = module.aggregate_holdertrade_events(loaded_holder)

    assert set(share_daily["trade_date"].dropna()) == {"20240130"}
    assert set(holder_daily["trade_date"].dropna()) == {"20240130"}
    assert "20240205" not in set(share_daily["trade_date"].dropna())
    assert "20240205" not in set(holder_daily["trade_date"].dropna())


def test_run_analysis_contract(monkeypatch, tmp_path: Path, capsys):
    base_df = pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "20240101"}])
    share_float_df = pd.DataFrame([{"ts_code": "000001.SZ", "ann_date": "20240101"}])
    holdertrade_df = pd.DataFrame([{"ts_code": "000001.SZ", "ann_date": "20240101"}])
    share_float_daily_df = pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "20240101"}])
    holdertrade_daily_df = pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "20240101"}])
    merged_df = pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "20240101"}])
    featured_df = pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "20240101", "ret_1d": 0.1}])
    summary_df = pd.DataFrame([{"strategy_family": "demo", "signal_code": "demo__001"}])
    trigger_df = pd.DataFrame([{"signal_code": "demo__001", "ts_code": "000001.SZ", "trade_date": "20240101"}])
    compact_df = pd.DataFrame([{"strategy_family": "demo", "signal_code": "demo__001"}])

    call_order: list[str] = []

    monkeypatch.setattr(module, "load_base_frame", lambda **kwargs: call_order.append("load_base_frame") or base_df)
    monkeypatch.setattr(module, "load_share_float_frame", lambda **kwargs: call_order.append("load_share_float_frame") or share_float_df)
    monkeypatch.setattr(module, "load_holdertrade_frame", lambda **kwargs: call_order.append("load_holdertrade_frame") or holdertrade_df)
    monkeypatch.setattr(module, "aggregate_share_float_events", lambda frame: call_order.append("aggregate_share_float_events") or share_float_daily_df)
    monkeypatch.setattr(module, "aggregate_holdertrade_events", lambda frame: call_order.append("aggregate_holdertrade_events") or holdertrade_daily_df)
    monkeypatch.setattr(module, "merge_side_frames", lambda base_df, share_float_daily_df, holdertrade_daily_df: call_order.append("merge_side_frames") or merged_df)
    monkeypatch.setattr(module, "build_features", lambda frame: call_order.append("build_features") or featured_df)
    monkeypatch.setattr(module, "build_signal_rule_defs", lambda: call_order.append("build_signal_rule_defs") or [module.SignalRuleDef("demo", "demo__001", "demo", lambda df: pd.Series([True], index=df.index))])

    captured = {}

    def fake_summarize_signal_matrix(frame, rule_defs=None, min_sample=30, show_progress=False):
        call_order.append("summarize_signal_matrix")
        captured["summarize_kwargs"] = {
            "rule_defs_len": len(rule_defs or []),
            "min_sample": min_sample,
            "show_progress": show_progress,
        }
        return summary_df, trigger_df

    def fake_build_compact_summary(summary_df_arg, trigger_df_arg):
        call_order.append("build_compact_summary")
        assert summary_df_arg.equals(summary_df)
        assert trigger_df_arg.equals(trigger_df)
        return compact_df

    def fake_build_signal_code_markdown(rule_defs):
        call_order.append("build_signal_code_markdown")
        assert len(rule_defs) == 1
        return "## Signal Codes\n"

    def fake_write_outputs(compact_df_arg, signal_code_markdown, output_dir):
        call_order.append("write_outputs")
        assert compact_df_arg.equals(compact_df)
        assert signal_code_markdown == "## Signal Codes\n"
        assert output_dir == tmp_path
        return {"summary_csv": tmp_path / "0421_1200.csv", "summary_md": tmp_path / "0421_1200.md"}

    monkeypatch.setattr(module, "summarize_signal_matrix", fake_summarize_signal_matrix)
    monkeypatch.setattr(module, "build_compact_summary", fake_build_compact_summary)
    monkeypatch.setattr(module, "build_signal_code_markdown", fake_build_signal_code_markdown)
    monkeypatch.setattr(module, "write_outputs", fake_write_outputs)

    result = module.run_analysis(
        start_date="20240101",
        end_date="20240131",
        min_sample=30,
        top_n=20,
        output_dir=tmp_path,
        show_progress=False,
    )

    stdout = capsys.readouterr().out
    assert "==> load_base_frame" in stdout
    assert "==> build_features" in stdout
    assert "==> Scanning strategies" in stdout
    assert "==> write_outputs" in stdout
    assert "==> load_base_frame done | loaded_rows=1 | loaded_stocks=1 | date_range=20240101 -> 20240101" in stdout
    assert captured["summarize_kwargs"] == {"rule_defs_len": 1, "min_sample": 30, "show_progress": False}
    assert call_order == [
        "load_base_frame",
        "load_share_float_frame",
        "load_holdertrade_frame",
        "aggregate_share_float_events",
        "aggregate_holdertrade_events",
        "merge_side_frames",
        "build_features",
        "build_signal_rule_defs",
        "summarize_signal_matrix",
        "build_compact_summary",
        "build_signal_code_markdown",
        "write_outputs",
    ]
    assert result["source_df"].equals(base_df)
    assert result["base_df"].equals(base_df)
    assert result["share_float_df"].equals(share_float_df)
    assert result["holdertrade_df"].equals(holdertrade_df)
    assert result["share_float_daily_df"].equals(share_float_daily_df)
    assert result["holdertrade_daily_df"].equals(holdertrade_daily_df)
    assert result["merged_df"].equals(merged_df)
    assert result["featured_df"].equals(featured_df)
    assert result["summary_df"].equals(summary_df)
    assert result["trigger_df"].equals(trigger_df)
    assert result["compact_df"].equals(compact_df)
    assert result["output_paths"]["summary_csv"].name == "0421_1200.csv"
    assert result["output_paths"]["summary_md"].name == "0421_1200.md"


def test_analysis_readme_mentions_supply_shock_strategies():
    readme_path = Path(__file__).resolve().parents[1] / "analysis" / "README.md"
    content = readme_path.read_text(encoding="utf-8")
    assert "supply_shock_strategies" in content


def test_build_signal_rule_defs_generates_large_unique_rule_set_and_expected_families():
    rule_defs = module.build_signal_rule_defs()

    assert len(rule_defs) >= 150
    assert len({rule.code for rule in rule_defs}) == len(rule_defs)
    assert {rule.family for rule in rule_defs} == {
        "plain_supply_pressure",
        "state_supply_pressure",
        "plain_absorption_repair",
        "state_absorption_repair",
    }

    codes = {rule.code for rule in rule_defs}
    assert "plain_supply_pressure__sf_float_total_float_ratio_ge_1" in codes
    assert "state_supply_pressure__sf_float_total_float_ratio_ge_1__weak_trend_state" in codes
    assert "plain_absorption_repair__has_supply_event__pct_chg_gt_0" in codes
    assert "state_absorption_repair__has_supply_event__pct_chg_gt_0__oversold_state" in codes


def test_signal_rule_predicates_fire_on_synthetic_frame():
    frame = pd.DataFrame(
        [
            {
                "sf_float_total_float_ratio": 1.5,
                "sf_ann_total_float_ratio": 0.8,
                "sf_float_max_float_ratio": 0.4,
                "sf_ann_max_float_ratio": 0.2,
                "sf_float_ratio_orig": 0.1,
                "sf_ann_ratio_orig": 0.1,
                "sf_float_ratio_private_placement": 0.1,
                "sf_ann_ratio_private_placement": 0.1,
                "sf_float_ratio_ipo": 0.2,
                "sf_ann_ratio_ipo": 0.2,
                "ht_ann_de_total_change_ratio": 0.1,
                "ht_begin_de_total_change_ratio": 0.1,
                "ht_close_de_total_change_ratio": 0.6,
                "ht_ann_de_max_change_ratio": 0.1,
                "ht_begin_de_max_change_ratio": 0.1,
                "ht_close_de_max_change_ratio": 0.1,
                "ht_ann_de_event_count": 0.0,
                "ht_begin_de_event_count": 0.0,
                "ht_close_de_event_count": 0.0,
                "ht_ann_de_exec_total_change_ratio": 0.1,
                "ht_begin_de_exec_total_change_ratio": 0.1,
                "ht_close_de_exec_total_change_ratio": 0.1,
                "ht_ann_de_company_total_change_ratio": 0.1,
                "ht_begin_de_company_total_change_ratio": 0.1,
                "ht_close_de_company_total_change_ratio": 0.1,
                "ht_close_in_total_change_ratio": 0.2,
                "ht_ann_in_total_change_ratio": 0.2,
                "has_supply_event": True,
                "has_de_event": True,
                "has_share_float_event": True,
                "has_in_event": True,
                "weak_trend_state": True,
                "high_turnover_state": True,
                "volume_expand_state": True,
                "is_bottom_zone": True,
                "oversold_state": True,
                "ma_reclaim_state": False,
                "pullback_state": False,
                "strong_trend_state": False,
                "pct_chg": 1.2,
            }
        ]
    )

    rule_map = {rule.code: rule for rule in module.build_signal_rule_defs()}

    assert bool(rule_map["plain_supply_pressure__sf_float_total_float_ratio_ge_1"].predicate(frame).iloc[0]) is True
    assert bool(
        rule_map["state_supply_pressure__sf_float_total_float_ratio_ge_1__weak_trend_state"].predicate(frame).iloc[0]
    ) is True
    assert bool(rule_map["plain_absorption_repair__has_supply_event__pct_chg_gt_0"].predicate(frame).iloc[0]) is True
    assert bool(
        rule_map["state_absorption_repair__has_supply_event__pct_chg_gt_0__oversold_state"].predicate(frame).iloc[0]
    ) is True


def test_summarize_and_compact_summary_use_latest_hits():
    frame = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20240130",
                "close_qfq": 10.0,
                "pct_chg": 1.5,
                "volume_ratio": 1.2,
                "turnover_rate_f": 2.1,
                "ret_1d": 0.08,
                "ret_3d": 0.12,
                "is_bottom_zone": True,
                "has_supply_event": False,
            },
            {
                "ts_code": "000002.SZ",
                "trade_date": "20240131",
                "close_qfq": 8.0,
                "pct_chg": -2.0,
                "volume_ratio": 1.8,
                "turnover_rate_f": 3.4,
                "ret_1d": 0.18,
                "ret_3d": 0.22,
                "is_bottom_zone": False,
                "has_supply_event": True,
            },
            {
                "ts_code": "000003.SZ",
                "trade_date": "20240131",
                "close_qfq": 12.0,
                "pct_chg": 2.0,
                "volume_ratio": 0.9,
                "turnover_rate_f": 1.0,
                "ret_1d": 0.15,
                "ret_3d": 0.25,
                "is_bottom_zone": True,
                "has_supply_event": True,
            },
        ]
    )
    rule_defs = [
        module.SignalRuleDef(
            family="plain_supply_pressure",
            code="plain_supply_pressure__bottom_zone",
            description="底部区",
            predicate=lambda df: df["is_bottom_zone"].fillna(False).astype(bool),
        ),
        module.SignalRuleDef(
            family="plain_absorption_repair",
            code="plain_absorption_repair__has_supply_event",
            description="供给事件",
            predicate=lambda df: df["has_supply_event"].fillna(False).astype(bool),
        ),
        module.SignalRuleDef(
            family="plain_supply_pressure",
            code="plain_supply_pressure__no_hits",
            description="无命中",
            predicate=lambda df: df["close_qfq"] > 1000,
        ),
    ]

    summary_df, trigger_df = module.summarize_signal_matrix(frame, rule_defs=rule_defs, min_sample=1)
    compact_df = module.build_compact_summary(summary_df, trigger_df)

    assert list(summary_df.columns) == [
        "strategy_family",
        "signal_code",
        "sample_count",
        "win_rate_1d",
        "avg_ret_1d",
        "var_ret_1d",
        "win_rate_3d",
        "avg_ret_3d",
        "var_ret_3d",
        "is_low_sample",
    ]
    assert {"ts_code", "trade_date", "strategy_family", "signal_code", "close_qfq", "pct_chg", "volume_ratio", "turnover_rate_f", "ret_1d", "ret_3d"}.issubset(trigger_df.columns)
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
    assert compact_df.loc[compact_df["signal_code"] == "plain_supply_pressure__bottom_zone", "latest_trade_date"].iloc[0] == "20240131"
    assert compact_df.loc[compact_df["signal_code"] == "plain_supply_pressure__bottom_zone", "latest_hit_stocks"].iloc[0] == "000003.SZ"
    assert compact_df.loc[compact_df["signal_code"] == "plain_absorption_repair__has_supply_event", "latest_hit_stocks"].iloc[0] == "000002.SZ,000003.SZ"
    assert compact_df.loc[compact_df["signal_code"] == "plain_supply_pressure__no_hits", "latest_trade_date"].iloc[0] == ""
    assert compact_df.loc[compact_df["signal_code"] == "plain_supply_pressure__no_hits", "latest_hit_stocks"].iloc[0] == ""
    assert module._series_variance(pd.Series([1.0, 2.0, 3.0])) == 1.0


def test_write_outputs_uses_fixed_timestamp_stem(monkeypatch, tmp_path: Path):
    class FixedDateTime:
        @classmethod
        def now(cls):
            return real_datetime(2026, 4, 18, 16, 30)

    monkeypatch.setattr(module, "datetime", FixedDateTime)

    compact_df = pd.DataFrame(
        [
            {
                "strategy_family": "plain_supply_pressure",
                "signal_code": "plain_supply_pressure__bottom_zone",
                "sample_count": 3,
                "win_rate_1d": 0.66,
                "avg_ret_1d": 0.12,
                "var_ret_1d": 0.01,
                "win_rate_3d": 0.5,
                "avg_ret_3d": 0.08,
                "var_ret_3d": 0.02,
                "latest_trade_date": "20240131",
                "latest_hit_stocks": "000003.SZ",
            }
        ]
    )

    result = module.write_outputs(compact_df, "signal codebook", tmp_path)

    assert result["summary_csv"].name == "0418_1630.csv"
    assert result["summary_md"].name == "0418_1630.md"
    assert result["summary_csv"].exists()
    assert result["summary_md"].exists()
    assert "signal codebook" in result["summary_md"].read_text(encoding="utf-8")
