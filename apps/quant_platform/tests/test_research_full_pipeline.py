import json
import sys
from pathlib import Path

import pandas as pd

import apps.quant_platform.research.pipeline as pipeline_module
from apps.quant_platform.research.scripts import run_factor_research as factor_research_script
from apps.quant_platform.research.factor_engine.technical import TechnicalFactorBuilder
from apps.quant_platform.research.pipeline import FullResearchBuildResult, FullResearchPipeline, FullResearchPipelineConfig
from apps.quant_platform.research.scripts.run_factor_research import run_factor_research, run_full_factor_research


def test_technical_factor_builder_expands_requirement_level_derived_columns():
    panel = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "2026-01-03",
                "pct_chg": 1.2,
                "roc_qfq": 0.8,
                "mtm_qfq": 1.1,
                "ma_qfq_5": 10.5,
                "ma_qfq_20": 10.0,
                "ma_qfq_60": 9.0,
                "ema_qfq_10": 10.4,
                "ema_qfq_60": 9.2,
                "atr_qfq": 0.6,
                "close_qfq": 10.2,
                "boll_upper_qfq": 11.0,
                "boll_lower_qfq": 9.0,
                "macd_dif_qfq": 0.3,
                "macd_dea_qfq": 0.2,
                "macd_qfq": 0.1,
                "dmi_pdi_qfq": 24.0,
                "dmi_mdi_qfq": 18.0,
                "dmi_adx_qfq": 30.0,
                "dmi_adxr_qfq": 28.0,
                "trix_qfq": 0.05,
                "cr_qfq": 105.0,
                "topdays": 3,
                "lowdays": 12,
                "volume_ratio": 1.3,
                "turnover_rate_f": 2.6,
                "obv_qfq": 1500.0,
                "mfi_qfq": 55.0,
                "rsi_qfq_6": 52.0,
                "rsi_qfq_12": 49.0,
                "rsi_qfq_24": 46.0,
                "kdj_k_qfq": 62.0,
                "kdj_d_qfq": 57.0,
                "wr_qfq": -25.0,
                "cci_qfq": 88.0,
                "psy_qfq": 61.0,
                "bias1_qfq": 0.02,
                "bias2_qfq": 0.03,
                "bias3_qfq": 0.04,
                "pe_ttm": 18.0,
                "pb": 2.1,
                "ps_ttm": 3.4,
                "dv_ttm": 1.5,
                "total_mv": 100000.0,
                "circ_mv": 60000.0,
            }
        ]
    )

    factor_panel = TechnicalFactorBuilder().build(panel)

    assert round(factor_panel.loc[0, "ma_spread_20_60"], 6) == round(10.0 / 9.0 - 1, 6)
    assert round(factor_panel.loc[0, "boll_bandwidth"], 6) == round((11.0 - 9.0) / 10.2, 6)
    assert factor_panel.loc[0, "kdj_j_qfq"] == 72.0
    assert "roc_qfq" in factor_panel.columns
    assert "mtm_qfq" in factor_panel.columns
    assert "rsi_qfq_24" in factor_panel.columns
    assert "pe_ttm" in factor_panel.columns


def test_run_factor_research_returns_requirement_level_summary_columns(tmp_path):
    panel = pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "ts_code": "A", "alpha": 1.0, "overnight_return": 0.06},
            {"trade_date": "2026-01-02", "ts_code": "B", "alpha": 2.0, "overnight_return": 0.02},
            {"trade_date": "2026-01-03", "ts_code": "A", "alpha": 2.0, "overnight_return": 0.03},
            {"trade_date": "2026-01-03", "ts_code": "B", "alpha": 1.0, "overnight_return": 0.07},
        ]
    )

    result = run_factor_research(panel, factor_cols=["alpha"], output_dir=tmp_path)
    ranking = result["ranking"]

    assert {
        "p_value",
        "fdr_p_value",
        "long_short_mean",
        "monotonicity",
        "coverage",
        "trade_date_coverage",
        "eligible_trade_date_coverage",
        "active_stock_coverage",
        "active_trade_date_coverage",
        "rolling_1y_valid_ratio",
        "passes_rolling_stability",
    }.issubset(ranking.columns)
    assert ranking.loc[0, "eligible_trade_date_coverage"] == 1.0
    assert "correlation_plot" in result
    assert Path(result["correlation_plot"]).exists()
    assert Path(result["ranking_overview_html"]).exists()


def test_run_factor_research_main_defaults_to_full_research_for_from_db(monkeypatch, capsys):
    captured: dict[str, Path] = {}

    def fake_run_full_factor_research(*, start_date, end_date=None, output_dir, target_col, time_series_windows, event_windows, include_chip_distribution):
        captured["output_dir"] = Path(output_dir)
        return {"split_summary_path": str(Path(output_dir) / "split_factor_summary.csv")}

    def fake_publish_research_snapshot(*, output_root, full_research_dir):
        captured["output_root"] = Path(output_root)
        captured["full_research_dir"] = Path(full_research_dir)
        return {"available": True}

    monkeypatch.setattr(factor_research_script, "run_full_factor_research", fake_run_full_factor_research)
    monkeypatch.setattr(factor_research_script, "publish_research_snapshot", fake_publish_research_snapshot)
    monkeypatch.setattr(sys, "argv", ["run_factor_research.py", "--from-db"])

    factor_research_script.main()

    payload = json.loads(capsys.readouterr().out)
    expected = Path("apps/quant_platform/research/output/full_research")
    assert captured["output_dir"] == expected
    assert captured["full_research_dir"] == expected
    assert captured["output_root"] == expected.parent
    assert payload["snapshot"]["available"] is True


def test_run_factor_research_skips_dates_with_excess_factor_missingness(tmp_path):
    panel = pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "ts_code": "A", "alpha": 1.0, "overnight_return": 0.01},
            {"trade_date": "2026-01-02", "ts_code": "B", "alpha": 2.0, "overnight_return": 0.02},
            {"trade_date": "2026-01-02", "ts_code": "C", "alpha": 3.0, "overnight_return": 0.03},
            {"trade_date": "2026-01-03", "ts_code": "A", "alpha": 1.0, "overnight_return": 0.01},
            {"trade_date": "2026-01-03", "ts_code": "B", "alpha": None, "overnight_return": 0.02},
            {"trade_date": "2026-01-03", "ts_code": "C", "alpha": 3.0, "overnight_return": 0.03},
        ]
    )

    result = run_factor_research(panel, factor_cols=["alpha"], output_dir=tmp_path)
    ranking = result["ranking"]

    assert round(float(ranking.loc[0, "daily_missing_ratio_max"]), 6) > 0.3
    assert ranking.loc[0, "eligible_trade_date_coverage"] == 0.5


def test_full_research_pipeline_builds_multi_source_factor_panel_and_sample_splits():
    dataset = {
        "panel": pd.DataFrame(
            [
                {
                    "ts_code": "000001.SZ",
                    "trade_date": "20231229",
                    "open": 10.0,
                    "close": 10.1,
                    "pct_chg": 1.0,
                    "roc_qfq": 0.8,
                    "mtm_qfq": 0.9,
                    "ma_qfq_5": 10.2,
                    "ma_qfq_20": 10.0,
                    "ma_qfq_60": 9.5,
                    "ema_qfq_10": 10.1,
                    "ema_qfq_60": 9.6,
                    "atr_qfq": 0.3,
                    "close_qfq": 10.1,
                    "boll_upper_qfq": 10.8,
                    "boll_lower_qfq": 9.4,
                    "macd_dif_qfq": 0.2,
                    "macd_dea_qfq": 0.1,
                    "macd_qfq": 0.1,
                    "dmi_pdi_qfq": 20.0,
                    "dmi_mdi_qfq": 12.0,
                    "dmi_adx_qfq": 25.0,
                    "dmi_adxr_qfq": 24.0,
                    "trix_qfq": 0.04,
                    "cr_qfq": 102.0,
                    "topdays": 1,
                    "lowdays": 10,
                    "volume_ratio": 1.0,
                    "turnover_rate_f": 2.0,
                    "obv_qfq": 1000.0,
                    "mfi_qfq": 52.0,
                    "rsi_qfq_6": 48.0,
                    "rsi_qfq_12": 46.0,
                    "rsi_qfq_24": 44.0,
                    "kdj_k_qfq": 55.0,
                    "kdj_d_qfq": 50.0,
                    "wr_qfq": -20.0,
                    "cci_qfq": 80.0,
                    "psy_qfq": 55.0,
                    "bias1_qfq": 0.01,
                    "bias2_qfq": 0.02,
                    "bias3_qfq": 0.03,
                    "pe_ttm": 15.0,
                    "pb": 1.5,
                    "ps_ttm": 2.1,
                    "dv_ttm": 1.2,
                    "total_mv": 1000.0,
                    "circ_mv": 700.0,
                    "amount": 100.0,
                },
                {
                    "ts_code": "000001.SZ",
                    "trade_date": "20240103",
                    "open": 10.2,
                    "close": 10.5,
                    "pct_chg": 3.0,
                    "roc_qfq": 2.0,
                    "mtm_qfq": 1.8,
                    "ma_qfq_5": 10.3,
                    "ma_qfq_20": 10.1,
                    "ma_qfq_60": 9.6,
                    "ema_qfq_10": 10.25,
                    "ema_qfq_60": 9.7,
                    "atr_qfq": 0.4,
                    "close_qfq": 10.5,
                    "boll_upper_qfq": 11.1,
                    "boll_lower_qfq": 9.6,
                    "macd_dif_qfq": 0.3,
                    "macd_dea_qfq": 0.15,
                    "macd_qfq": 0.15,
                    "dmi_pdi_qfq": 24.0,
                    "dmi_mdi_qfq": 11.0,
                    "dmi_adx_qfq": 28.0,
                    "dmi_adxr_qfq": 25.0,
                    "trix_qfq": 0.05,
                    "cr_qfq": 105.0,
                    "topdays": 2,
                    "lowdays": 9,
                    "volume_ratio": 1.2,
                    "turnover_rate_f": 2.2,
                    "obv_qfq": 1100.0,
                    "mfi_qfq": 54.0,
                    "rsi_qfq_6": 53.0,
                    "rsi_qfq_12": 50.0,
                    "rsi_qfq_24": 47.0,
                    "kdj_k_qfq": 60.0,
                    "kdj_d_qfq": 54.0,
                    "wr_qfq": -18.0,
                    "cci_qfq": 82.0,
                    "psy_qfq": 57.0,
                    "bias1_qfq": 0.02,
                    "bias2_qfq": 0.03,
                    "bias3_qfq": 0.04,
                    "pe_ttm": 16.0,
                    "pb": 1.6,
                    "ps_ttm": 2.2,
                    "dv_ttm": 1.1,
                    "total_mv": 1010.0,
                    "circ_mv": 705.0,
                    "amount": 120.0,
                },
                {
                    "ts_code": "000001.SZ",
                    "trade_date": "20250702",
                    "open": 10.6,
                    "close": 10.4,
                    "pct_chg": -1.0,
                    "roc_qfq": -0.5,
                    "mtm_qfq": -0.4,
                    "ma_qfq_5": 10.4,
                    "ma_qfq_20": 10.2,
                    "ma_qfq_60": 9.8,
                    "ema_qfq_10": 10.35,
                    "ema_qfq_60": 9.9,
                    "atr_qfq": 0.35,
                    "close_qfq": 10.4,
                    "boll_upper_qfq": 11.0,
                    "boll_lower_qfq": 9.7,
                    "macd_dif_qfq": 0.1,
                    "macd_dea_qfq": 0.12,
                    "macd_qfq": -0.02,
                    "dmi_pdi_qfq": 18.0,
                    "dmi_mdi_qfq": 17.0,
                    "dmi_adx_qfq": 22.0,
                    "dmi_adxr_qfq": 21.0,
                    "trix_qfq": 0.01,
                    "cr_qfq": 99.0,
                    "topdays": 1,
                    "lowdays": 6,
                    "volume_ratio": 1.1,
                    "turnover_rate_f": 1.8,
                    "obv_qfq": 1080.0,
                    "mfi_qfq": 49.0,
                    "rsi_qfq_6": 45.0,
                    "rsi_qfq_12": 47.0,
                    "rsi_qfq_24": 46.0,
                    "kdj_k_qfq": 49.0,
                    "kdj_d_qfq": 51.0,
                    "wr_qfq": -28.0,
                    "cci_qfq": 70.0,
                    "psy_qfq": 49.0,
                    "bias1_qfq": -0.01,
                    "bias2_qfq": 0.01,
                    "bias3_qfq": 0.02,
                    "pe_ttm": 14.0,
                    "pb": 1.4,
                    "ps_ttm": 2.0,
                    "dv_ttm": 1.3,
                    "total_mv": 990.0,
                    "circ_mv": 690.0,
                    "amount": 110.0,
                },
                {
                    "ts_code": "000001.SZ",
                    "trade_date": "20250703",
                    "open": 10.5,
                    "close": 10.7,
                    "pct_chg": 1.8,
                    "roc_qfq": 1.1,
                    "mtm_qfq": 0.8,
                    "ma_qfq_5": 10.5,
                    "ma_qfq_20": 10.25,
                    "ma_qfq_60": 9.85,
                    "ema_qfq_10": 10.4,
                    "ema_qfq_60": 9.95,
                    "atr_qfq": 0.33,
                    "close_qfq": 10.7,
                    "boll_upper_qfq": 11.2,
                    "boll_lower_qfq": 9.8,
                    "macd_dif_qfq": 0.15,
                    "macd_dea_qfq": 0.13,
                    "macd_qfq": 0.02,
                    "dmi_pdi_qfq": 22.0,
                    "dmi_mdi_qfq": 14.0,
                    "dmi_adx_qfq": 24.0,
                    "dmi_adxr_qfq": 23.0,
                    "trix_qfq": 0.03,
                    "cr_qfq": 103.0,
                    "topdays": 2,
                    "lowdays": 5,
                    "volume_ratio": 1.15,
                    "turnover_rate_f": 1.9,
                    "obv_qfq": 1120.0,
                    "mfi_qfq": 53.0,
                    "rsi_qfq_6": 51.0,
                    "rsi_qfq_12": 49.0,
                    "rsi_qfq_24": 47.0,
                    "kdj_k_qfq": 56.0,
                    "kdj_d_qfq": 52.0,
                    "wr_qfq": -21.0,
                    "cci_qfq": 78.0,
                    "psy_qfq": 54.0,
                    "bias1_qfq": 0.01,
                    "bias2_qfq": 0.02,
                    "bias3_qfq": 0.03,
                    "pe_ttm": 14.5,
                    "pb": 1.45,
                    "ps_ttm": 2.05,
                    "dv_ttm": 1.25,
                    "total_mv": 1005.0,
                    "circ_mv": 695.0,
                    "amount": 115.0,
                },
            ]
        ),
        "stock_basic": pd.DataFrame([{"ts_code": "000001.SZ", "list_date": "20100101", "industry": "Bank"}]),
        "stock_money_flow": pd.DataFrame(
            [
                {"ts_code": "000001.SZ", "trade_date": "20240103", "buy_sm_amount": 8.0, "sell_sm_amount": 6.0, "buy_lg_amount": 12.0, "sell_lg_amount": 3.0, "buy_elg_amount": 14.0, "sell_elg_amount": 2.0, "net_mf_amount": 10.0},
                {"ts_code": "000001.SZ", "trade_date": "20250702", "buy_sm_amount": 7.0, "sell_sm_amount": 5.0, "buy_lg_amount": 9.0, "sell_lg_amount": 4.0, "buy_elg_amount": 10.0, "sell_elg_amount": 4.0, "net_mf_amount": 6.0},
            ]
        ),
        "stock_money_flow_dc": pd.DataFrame(
            [
                {"ts_code": "000001.SZ", "trade_date": "20240103", "net_amount": 9.0, "net_amount_rate": 0.1, "buy_elg_amount_rate": 0.3, "buy_sm_amount_rate": 0.1},
                {"ts_code": "000001.SZ", "trade_date": "20250702", "net_amount": 4.0, "net_amount_rate": 0.04, "buy_elg_amount_rate": 0.2, "buy_sm_amount_rate": 0.08},
            ]
        ),
        "stock_cyq_perf": pd.DataFrame(
            [
                {"ts_code": "000001.SZ", "trade_date": "20240103", "winner_rate": 60.0, "weight_avg": 10.0, "cost_5pct": 9.0, "cost_15pct": 9.5, "cost_50pct": 10.0, "cost_85pct": 10.5, "cost_95pct": 11.0}
            ]
        ),
        "stock_cyq_chips": pd.DataFrame(
            [
                {"ts_code": "000001.SZ", "trade_date": "20240103", "price": 10.1, "percent": 0.3},
                {"ts_code": "000001.SZ", "trade_date": "20240103", "price": 10.8, "percent": 0.7},
            ]
        ),
        "stock_hk_hold": pd.DataFrame(
            [
                {"ts_code": "000001.SZ", "trade_date": "20231229", "ratio": 2.0, "vol": 100.0},
                {"ts_code": "000001.SZ", "trade_date": "20240103", "ratio": 3.0, "vol": 120.0},
            ]
        ),
        "stock_hsgt_top10": pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "20240103", "net_amount": 5.0}]),
        "stock_ccass_hold": pd.DataFrame(
            [
                {"ts_code": "000001.SZ", "trade_date": "20231229", "hold_nums": 20, "hold_ratio": 1.5},
                {"ts_code": "000001.SZ", "trade_date": "20240103", "hold_nums": 24, "hold_ratio": 1.8},
            ]
        ),
        "stock_margin_detail": pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "20240103", "rzye": 40.0, "rqye": 5.0, "rzmre": 6.0}]),
        "stock_limit_list_d": pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "20240103", "limit": "U", "fd_amount": 30.0, "float_mv": 700.0, "open_times": 1, "limit_times": 2}]),
        "stock_top_list": pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "20240103", "net_rate": 0.05, "net_amount": 4.0}]),
        "stock_top_inst": pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "20240103", "net_buy": 3.0, "buy": 8.0, "sell": 5.0}]),
        "stock_block_trade": pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "20240103", "price": 10.0, "amount": 10.0}]),
        "stock_stk_limit": pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "20240103", "pre_close": 10.1, "up_limit": 11.1, "down_limit": 9.1}]),
        "stock_stk_ah_comparison": pd.DataFrame(
            [
                {"ts_code": "000001.SZ", "trade_date": "20240103", "ah_comparison": 1.1, "ah_premium": 0.10},
                {"ts_code": "000001.SZ", "trade_date": "20250702", "ah_comparison": 1.2, "ah_premium": 0.15},
            ]
        ),
        "stock_stk_holdernumber": pd.DataFrame([{"ts_code": "000001.SZ", "ann_date": "20240102", "end_date": "20231231", "holder_num": 1000}]),
        "stock_stk_holdertrade": pd.DataFrame([{"ts_code": "000001.SZ", "ann_date": "20240102", "in_de": "IN", "change_ratio": 0.02}]),
        "stock_repurchase": pd.DataFrame([{"ts_code": "000001.SZ", "ann_date": "20240102", "amount": 20.0, "high_limit": 11.0}]),
        "stock_share_float": pd.DataFrame([{"ts_code": "000001.SZ", "float_date": "20250702", "float_ratio": 0.08}]),
        "stock_pledge_stat": pd.DataFrame([{"ts_code": "000001.SZ", "end_date": "20240102", "pledge_ratio": 0.12}]),
        "stock_top10_holders": pd.DataFrame(
            [{"ts_code": "000001.SZ", "ann_date": "20240102", "end_date": "20231231", "hold_ratio": 11.0, "hold_float_ratio": 8.0, "hold_change": 0.5}]
        ),
        "stock_top10_floatholders": pd.DataFrame(
            [{"ts_code": "000001.SZ", "ann_date": "20240102", "end_date": "20231231", "hold_ratio": 7.0, "hold_float_ratio": 5.0, "hold_change": 0.2}]
        ),
        "stock_forecast_vip": pd.DataFrame([{"ts_code": "000001.SZ", "ann_date": "20240102", "type": "扭亏", "p_change_min": 10.0, "p_change_max": 20.0}]),
        "stock_express_vip": pd.DataFrame([{"ts_code": "000001.SZ", "ann_date": "20240102", "yoy_dedu_np": 25.0, "yoy_eps": 8.0}]),
        "stock_report_rc": pd.DataFrame([{"ts_code": "000001.SZ", "report_date": "20240102", "report_title": "r1", "max_price": 12.0, "min_price": 11.0}]),
        "stock_disclosure_date": pd.DataFrame([{"ts_code": "000001.SZ", "ann_date": "20240102", "actual_date": "20240110", "pre_date": "20240109"}]),
        "stock_stk_surv": pd.DataFrame([{"ts_code": "000001.SZ", "surv_date": "20240102", "name": "x"}]),
        "stock_fina_indicator_vip": pd.DataFrame([{"ts_code": "000001.SZ", "ann_date": "20240102", "q_roe": 0.12, "gross_margin": 0.35}]),
        "stock_income_vip": pd.DataFrame([{"ts_code": "000001.SZ", "ann_date": "20240102", "revenue": 100.0}]),
        "stock_balancesheet_vip": pd.DataFrame([{"ts_code": "000001.SZ", "ann_date": "20240102", "total_assets": 200.0, "total_liab": 80.0}]),
        "stock_cashflow_vip": pd.DataFrame([{"ts_code": "000001.SZ", "ann_date": "20240102", "n_cashflow_act": 40.0}]),
        "stock_fina_audit": pd.DataFrame([{"ts_code": "000001.SZ", "ann_date": "20240102", "audit_result": "标准无保留意见"}]),
        "stock_money_flow_hsgt": pd.DataFrame([{"trade_date": "20240103", "north_money": 100.0}]),
        "stock_money_flow_mkt_dc": pd.DataFrame(
            [
                {
                    "trade_date": "20240103",
                    "net_amount": 300.0,
                    "net_amount_rate": 0.15,
                    "buy_elg_amount_rate": 0.32,
                    "buy_sm_amount_rate": 0.11,
                }
            ]
        ),
        "stock_margin": pd.DataFrame([{"trade_date": "20240103", "rzrqye": 500.0}]),
        "stock_st": pd.DataFrame(columns=["ts_code", "trade_date", "type_name"]),
        "stock_suspend_d": pd.DataFrame(columns=["ts_code", "trade_date", "suspend_type"]),
    }

    config = FullResearchPipelineConfig(
        time_series_windows=(1,),
        event_windows=(2,),
        train_end_date="2023-12-31",
        validation_end_date="2025-06-30",
    )
    result = FullResearchPipeline(config=config).build_from_dataset(dataset)

    assert "ma_spread_20_60" in result.factor_catalog["technical"]
    assert "net_mf_rate" in result.factor_catalog["money_flow"]
    assert "forecast_surprise_mid" in result.factor_catalog["event"]
    assert "forecast_surprise_mid_event_decay_2" in result.factor_catalog["event_state"]
    assert "chip_breakout_strength" in result.factor_catalog["cross_feature"]
    assert "ind_rel_pct_chg" in result.factor_catalog["industry"]
    assert "top10_holder_concentration" in result.factor_catalog["ownership"]
    assert "mkt_advance_ratio" in result.factor_catalog["market"]
    assert "mkt_dc_main_strength" in result.factor_catalog["market"]
    assert "ah_premium_chg" in result.factor_catalog["market"]
    assert "pct_chg_momentum_1" in result.factor_catalog["time_series"]
    assert "audit_result" not in result.factor_catalog["fundamental"]
    assert "next_disclosure_date" not in result.factor_catalog["event"]
    assert "limit" not in result.factor_catalog["limit"]
    assert "limit_up_price" in result.panel.columns
    assert all(pd.api.types.is_numeric_dtype(result.panel[column]) for column in result.factor_columns)
    assert set(result.sample_panels) == {"train", "validation", "test"}
    assert len(result.sample_panels["train"]) == 1
    assert len(result.sample_panels["validation"]) == 1
    assert len(result.sample_panels["test"]) == 2


def test_run_full_factor_research_outputs_train_validation_consistency_summary(tmp_path, monkeypatch):
    panel = pd.DataFrame(
        [
            {"trade_date": "2023-12-28", "ts_code": "A", "alpha": 1.0, "beta": 1.0, "overnight_return": 0.01},
            {"trade_date": "2023-12-28", "ts_code": "B", "alpha": 2.0, "beta": 2.0, "overnight_return": 0.02},
            {"trade_date": "2023-12-29", "ts_code": "A", "alpha": 1.0, "beta": 1.0, "overnight_return": 0.02},
            {"trade_date": "2023-12-29", "ts_code": "B", "alpha": 2.0, "beta": 2.0, "overnight_return": 0.03},
            {"trade_date": "2024-01-02", "ts_code": "A", "alpha": 1.0, "beta": 2.0, "overnight_return": 0.01},
            {"trade_date": "2024-01-02", "ts_code": "B", "alpha": 2.0, "beta": 1.0, "overnight_return": 0.02},
            {"trade_date": "2024-01-03", "ts_code": "A", "alpha": 1.0, "beta": 2.0, "overnight_return": 0.02},
            {"trade_date": "2024-01-03", "ts_code": "B", "alpha": 2.0, "beta": 1.0, "overnight_return": 0.03},
        ]
    )

    def fake_load_dataset_from_database(self, start_date, end_date=None):
        return {}

    def fake_build_from_dataset(self, dataset):
        return FullResearchBuildResult(
            panel=panel,
            factor_catalog={"custom": ["alpha", "beta"]},
            sample_panels=self.split_panel_by_sample(panel),
            factor_columns=["alpha", "beta"],
        )

    monkeypatch.setattr(FullResearchPipeline, "load_dataset_from_database", fake_load_dataset_from_database)
    monkeypatch.setattr(FullResearchPipeline, "build_from_dataset", fake_build_from_dataset)

    result = run_full_factor_research(start_date="2023-12-28", output_dir=tmp_path)
    summary = pd.read_csv(result["split_summary_path"])
    alpha_row = summary.loc[summary["factor_name"] == "alpha"].iloc[0]
    beta_row = summary.loc[summary["factor_name"] == "beta"].iloc[0]

    assert Path(result["qualified_summary_path"]).exists()
    assert Path(result["split_summary_html"]).exists()
    assert Path(result["qualified_summary_html"]).exists()
    assert "train_validation_consistent" in summary.columns
    assert str(alpha_row["train_validation_same_direction"]).lower() == "true"
    assert str(beta_row["train_validation_same_direction"]).lower() == "false"


def test_load_dataset_from_database_quotes_reserved_identifiers(monkeypatch):
    captured_queries = []

    class DummyConn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class DummyEngine:
        def connect(self):
            return DummyConn()

    class DummyLoader:
        def __init__(self, config=None, engine=None, source_specs=None):
            self.engine = engine or DummyEngine()

        def get_engine(self):
            return self.engine

        def load_panel(self, start_date=None, end_date=None, columns=None):
            return pd.DataFrame(
                [
                    {
                        "ts_code": "000001.SZ",
                        "trade_date": "20250701",
                        "open": 10.0,
                        "close": 10.1,
                        "pct_chg": 1.0,
                        "roc_qfq": 0.8,
                        "mtm_qfq": 0.7,
                        "ma_qfq_5": 10.0,
                        "ma_qfq_20": 9.8,
                        "ma_qfq_60": 9.5,
                        "ema_qfq_10": 9.9,
                        "ema_qfq_60": 9.4,
                        "atr_qfq": 0.2,
                        "close_qfq": 10.1,
                        "boll_upper_qfq": 10.5,
                        "boll_lower_qfq": 9.7,
                        "macd_dif_qfq": 0.1,
                        "macd_dea_qfq": 0.05,
                        "macd_qfq": 0.05,
                        "dmi_pdi_qfq": 20.0,
                        "dmi_mdi_qfq": 10.0,
                        "dmi_adx_qfq": 25.0,
                        "dmi_adxr_qfq": 23.0,
                        "trix_qfq": 0.02,
                        "cr_qfq": 101.0,
                        "topdays": 1,
                        "lowdays": 2,
                        "volume_ratio": 1.1,
                        "turnover_rate_f": 2.0,
                        "obv_qfq": 1000.0,
                        "mfi_qfq": 55.0,
                        "rsi_qfq_6": 52.0,
                        "rsi_qfq_12": 50.0,
                        "rsi_qfq_24": 48.0,
                        "kdj_k_qfq": 60.0,
                        "kdj_d_qfq": 55.0,
                        "wr_qfq": -20.0,
                        "cci_qfq": 80.0,
                        "psy_qfq": 56.0,
                        "bias1_qfq": 0.02,
                        "bias2_qfq": 0.03,
                        "bias3_qfq": 0.04,
                        "pe_ttm": 18.0,
                        "pb": 2.0,
                        "ps_ttm": 3.0,
                        "dv_ttm": 1.1,
                        "total_mv": 1000.0,
                        "circ_mv": 700.0,
                        "amount": 100.0,
                    }
                ]
            )

    def fake_read_sql_query(query, conn, params=None):
        captured_queries.append(str(query))
        return pd.DataFrame()

    monkeypatch.setattr(pipeline_module, "ResearchDataLoader", DummyLoader)
    monkeypatch.setattr(pipeline_module, "create_engine", lambda *args, **kwargs: DummyEngine())
    monkeypatch.setattr(pipeline_module, "build_tushare_db_url", lambda *args, **kwargs: "mysql://dummy")
    monkeypatch.setattr(pipeline_module.pd, "read_sql_query", fake_read_sql_query)

    FullResearchPipeline().load_dataset_from_database(start_date="2025-07-01", end_date="2025-07-02")

    limit_query = next(query for query in captured_queries if "stock_limit_list_d" in query)
    assert "SELECT `ts_code`, `trade_date`, `limit`, `fd_amount`, `float_mv`, `open_times`, `limit_times`" in limit_query
    assert "FROM `stock_limit_list_d`" in limit_query
    assert "WHERE `trade_date` >= :start_date" in limit_query


def test_load_dataset_from_database_can_skip_chip_distribution(monkeypatch):
    captured_queries = []

    class DummyConn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class DummyEngine:
        def connect(self):
            return DummyConn()

    class DummyLoader:
        def __init__(self, config=None, engine=None, source_specs=None):
            self.engine = engine or DummyEngine()

        def get_engine(self):
            return self.engine

        def load_panel(self, start_date=None, end_date=None, columns=None):
            return pd.DataFrame(
                [
                    {
                        "ts_code": "000001.SZ",
                        "trade_date": "20260303",
                        "open": 10.0,
                        "close": 10.1,
                        "pct_chg": 1.0,
                        "roc_qfq": 0.8,
                        "mtm_qfq": 0.7,
                        "ma_qfq_5": 10.0,
                        "ma_qfq_20": 9.8,
                        "ma_qfq_60": 9.5,
                        "ema_qfq_10": 9.9,
                        "ema_qfq_60": 9.4,
                        "atr_qfq": 0.2,
                        "close_qfq": 10.1,
                        "boll_upper_qfq": 10.5,
                        "boll_lower_qfq": 9.7,
                        "macd_dif_qfq": 0.1,
                        "macd_dea_qfq": 0.05,
                        "macd_qfq": 0.05,
                        "dmi_pdi_qfq": 20.0,
                        "dmi_mdi_qfq": 10.0,
                        "dmi_adx_qfq": 25.0,
                        "dmi_adxr_qfq": 23.0,
                        "trix_qfq": 0.02,
                        "cr_qfq": 101.0,
                        "topdays": 1,
                        "lowdays": 2,
                        "volume_ratio": 1.1,
                        "turnover_rate_f": 2.0,
                        "obv_qfq": 1000.0,
                        "mfi_qfq": 55.0,
                        "rsi_qfq_6": 52.0,
                        "rsi_qfq_12": 50.0,
                        "rsi_qfq_24": 48.0,
                        "kdj_k_qfq": 60.0,
                        "kdj_d_qfq": 55.0,
                        "wr_qfq": -20.0,
                        "cci_qfq": 80.0,
                        "psy_qfq": 56.0,
                        "bias1_qfq": 0.02,
                        "bias2_qfq": 0.03,
                        "bias3_qfq": 0.04,
                        "pe_ttm": 18.0,
                        "pb": 2.0,
                        "ps_ttm": 3.0,
                        "dv_ttm": 1.1,
                        "total_mv": 1000.0,
                        "circ_mv": 700.0,
                        "amount": 100.0,
                    }
                ]
            )

    def fake_read_sql_query(query, conn, params=None):
        captured_queries.append(str(query))
        return pd.DataFrame()

    monkeypatch.setattr(pipeline_module, "ResearchDataLoader", DummyLoader)
    monkeypatch.setattr(pipeline_module, "create_engine", lambda *args, **kwargs: DummyEngine())
    monkeypatch.setattr(pipeline_module, "build_tushare_db_url", lambda *args, **kwargs: "mysql://dummy")
    monkeypatch.setattr(pipeline_module.pd, "read_sql_query", fake_read_sql_query)

    pipeline = FullResearchPipeline(config=FullResearchPipelineConfig(include_chip_distribution=False))
    pipeline.load_dataset_from_database(start_date="2026-03-01", end_date="2026-04-04")

    assert not any("stock_cyq_chips" in query for query in captured_queries)
