from pathlib import Path

import pandas as pd

from apps.quant_platform.research.analyzer.correlation import analyze_factor_correlation
from apps.quant_platform.research.analyzer.report import ResearchReportBuilder
from apps.quant_platform.research.factor_engine.base import (
    generate_event_features,
    generate_time_series_features,
    run_standard_factor_pipeline,
)
from apps.quant_platform.research.factor_engine.chip import ChipFactorBuilder
from apps.quant_platform.research.factor_engine.composite import CompositeFactorBuilder
from apps.quant_platform.research.factor_engine.cross_feature import CrossFeatureBuilder
from apps.quant_platform.research.factor_engine.dragon import DragonFactorBuilder
from apps.quant_platform.research.factor_engine.event import EventFactorBuilder
from apps.quant_platform.research.factor_engine.fundamental import FundamentalFactorBuilder
from apps.quant_platform.research.factor_engine.industry import IndustryFactorBuilder
from apps.quant_platform.research.factor_engine.limit import LimitFactorBuilder
from apps.quant_platform.research.factor_engine.margin import MarginFactorBuilder
from apps.quant_platform.research.factor_engine.market import MarketFactorBuilder
from apps.quant_platform.research.factor_engine.money_flow import MoneyFlowFactorBuilder
from apps.quant_platform.research.factor_engine.northbound import NorthboundFactorBuilder
from apps.quant_platform.research.factor_engine.ownership import OwnershipFactorBuilder


def test_generate_time_series_and_event_features():
    panel = pd.DataFrame(
        [
            {"ts_code": "000001.SZ", "trade_date": "2026-01-02", "alpha": 1.0, "event_flag": 0.0},
            {"ts_code": "000001.SZ", "trade_date": "2026-01-03", "alpha": 2.0, "event_flag": 1.0},
            {"ts_code": "000001.SZ", "trade_date": "2026-01-06", "alpha": 4.0, "event_flag": 0.0},
        ]
    )

    transformed = generate_time_series_features(panel, factor_cols=["alpha"], windows=[1, 2])
    event_features = generate_event_features(panel, event_cols=["event_flag"], windows=[2])

    assert transformed.loc[2, "alpha_momentum_1"] == 2.0
    assert round(transformed.loc[2, "alpha_mr_distance_2"], 6) == round((4.0 - 3.0) / (2**0.5), 6)
    assert event_features.loc[1, "event_flag_event_age"] == 0.0
    assert event_features.loc[2, "event_flag_event_age"] == 1.0
    assert event_features.loc[2, "event_flag_event_count_2"] == 1.0


def test_factor_builders_cover_remaining_domain_modules():
    panel = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "2026-01-03",
                "amount": 1000.0,
                "float_mv": 5000.0,
                "circ_mv": 4000.0,
                "total_mv": 8000.0,
                "close_qfq": 10.0,
                "close": 10.0,
                "pct_chg": -1.0,
                "volume_ratio": 1.5,
                "turnover_rate_f": 2.0,
                "macd_dif_qfq": 0.5,
                "winner_rate": 55.0,
                "rsi_qfq_6": 40.0,
                "industry": "Bank",
                "open": 10.0,
                "high": 10.2,
                "low": 9.8,
                "list_date": "2010-01-01",
            },
            {
                "ts_code": "000002.SZ",
                "trade_date": "2026-01-03",
                "amount": 2000.0,
                "float_mv": 6000.0,
                "circ_mv": 4500.0,
                "total_mv": 9000.0,
                "close_qfq": 20.0,
                "close": 20.0,
                "pct_chg": 2.0,
                "volume_ratio": 0.8,
                "turnover_rate_f": 1.0,
                "macd_dif_qfq": -0.2,
                "winner_rate": 65.0,
                "rsi_qfq_6": 55.0,
                "industry": "Tech",
                "open": 19.5,
                "high": 20.2,
                "low": 19.2,
                "list_date": "2010-01-01",
            },
        ]
    )
    money_flow = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "2026-01-03",
                "net_mf_amount": 100.0,
                "buy_elg_amount": 200.0,
                "sell_elg_amount": 50.0,
                "buy_lg_amount": 120.0,
                "sell_lg_amount": 70.0,
                "buy_sm_amount": 80.0,
                "sell_sm_amount": 140.0,
            }
        ]
    )
    money_flow_dc = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "2026-01-03",
                "net_amount_rate": 0.12,
                "buy_elg_amount_rate": 0.30,
                "buy_sm_amount_rate": 0.10,
                "net_amount": 60.0,
            }
        ]
    )
    chip_perf = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "2026-01-03",
                "winner_rate": 55.0,
                "weight_avg": 9.5,
                "cost_5pct": 8.0,
                "cost_15pct": 9.0,
                "cost_50pct": 10.0,
                "cost_85pct": 11.0,
                "cost_95pct": 12.0,
            }
        ]
    )
    chip_dist = pd.DataFrame(
        [
            {"ts_code": "000001.SZ", "trade_date": "2026-01-03", "price": 9.0, "percent": 0.2},
            {"ts_code": "000001.SZ", "trade_date": "2026-01-03", "price": 10.2, "percent": 0.4},
            {"ts_code": "000001.SZ", "trade_date": "2026-01-03", "price": 10.5, "percent": 0.4},
        ]
    )
    hk_hold = pd.DataFrame(
        [
            {"ts_code": "000001.SZ", "trade_date": "2026-01-02", "ratio": 4.0, "vol": 1000.0},
            {"ts_code": "000001.SZ", "trade_date": "2026-01-03", "ratio": 5.0, "vol": 1200.0},
        ]
    )
    hsgt_top10 = pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "2026-01-03", "net_amount": 100.0}])
    ccass_hold = pd.DataFrame(
        [
            {"ts_code": "000001.SZ", "trade_date": "2026-01-02", "hold_ratio": 2.5, "hold_nums": 90},
            {"ts_code": "000001.SZ", "trade_date": "2026-01-03", "hold_ratio": 3.0, "hold_nums": 100},
        ]
    )
    margin_detail = pd.DataFrame(
        [
            {"ts_code": "000001.SZ", "trade_date": "2026-01-02", "rzye": 190.0, "rzmre": 30.0, "rqye": 15.0},
            {"ts_code": "000001.SZ", "trade_date": "2026-01-03", "rzye": 200.0, "rzmre": 50.0, "rqye": 20.0},
        ]
    )
    limit_list = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "2026-01-03",
                "limit": "U",
                "fd_amount": 250.0,
                "open_times": 1,
                "limit_times": 2,
            }
        ]
    )
    top_list = pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "2026-01-03", "net_rate": 0.06}])
    top_inst = pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "2026-01-03", "net_buy": 30.0, "buy": 80.0, "sell": 50.0}])
    block_trade = pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "2026-01-03", "price": 9.8, "amount": 120.0}])
    holder_number = pd.DataFrame(
        [
            {"ts_code": "000001.SZ", "trade_date": "2026-01-02", "holder_num": 1000},
            {"ts_code": "000001.SZ", "trade_date": "2026-01-03", "holder_num": 900},
        ]
    )
    holder_trade = pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "2026-01-03", "in_de": "IN", "change_ratio": 1.2}])
    repurchase = pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "2026-01-03", "amount": 100.0, "high_limit": 11.0}])
    share_float = pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "2026-01-03", "float_ratio": 0.08}])
    pledge_stat = pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "2026-01-03", "pledge_ratio": 0.15}])
    top10_holders = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "2026-01-03",
                "hold_ratio": 12.0,
                "hold_float_ratio": 8.0,
                "hold_change": 1.5,
            }
        ]
    )
    top10_floatholders = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "2026-01-03",
                "hold_ratio": 6.0,
                "hold_float_ratio": 4.0,
                "hold_change": 0.8,
            }
        ]
    )
    forecast = pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "2026-01-03", "p_change_min": 10.0, "p_change_max": 20.0, "type": "扭亏"}])
    express = pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "2026-01-03", "yoy_dedu_np": 25.0, "yoy_eps": 10.0}])
    report_rc = pd.DataFrame(
        [
            {"ts_code": "000001.SZ", "trade_date": "2026-01-01", "report_id": "r1", "max_price": 12.0, "min_price": 11.0},
            {"ts_code": "000001.SZ", "trade_date": "2026-01-02", "report_id": "r2", "max_price": 12.5, "min_price": 11.5},
        ]
    )
    disclosure_date = pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "2026-01-03", "next_disclosure_date": "2026-01-10"}])
    survey = pd.DataFrame(
        [
            {"ts_code": "000001.SZ", "trade_date": "2025-12-28", "event_id": "s1"},
            {"ts_code": "000001.SZ", "trade_date": "2026-01-02", "event_id": "s2"},
        ]
    )
    fina_indicator = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "2026-01-03",
                "q_roe": 0.12,
                "gross_margin": 0.35,
                "q_gr_yoy": 0.20,
                "q_profit_yoy": 0.25,
            }
        ]
    )
    income = pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "2026-01-03", "revenue": 100.0}])
    balancesheet = pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "2026-01-03", "total_assets": 200.0, "total_liab": 80.0}])
    cashflow = pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "2026-01-03", "n_cashflow_act": 40.0}])
    audit = pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "2026-01-03", "audit_result": "标准无保留意见"}])

    factor_panel = MoneyFlowFactorBuilder().build(panel, money_flow=money_flow, money_flow_dc=money_flow_dc)
    factor_panel = ChipFactorBuilder().build(factor_panel, chip_perf=chip_perf, chip_distribution=chip_dist)
    factor_panel = NorthboundFactorBuilder().build(factor_panel, hk_hold=hk_hold, hsgt_top10=hsgt_top10, ccass_hold=ccass_hold)
    factor_panel = MarginFactorBuilder().build(factor_panel, margin_detail=margin_detail)
    factor_panel = LimitFactorBuilder().build(factor_panel, limit_list=limit_list)
    factor_panel = DragonFactorBuilder().build(
        factor_panel,
        top_list=top_list,
        top_inst=top_inst,
        block_trade=block_trade,
    )
    factor_panel = OwnershipFactorBuilder().build(
        factor_panel,
        holder_number=holder_number,
        holder_trade=holder_trade,
        repurchase=repurchase,
        share_float=share_float,
        pledge_stat=pledge_stat,
        top10_holders=top10_holders,
        top10_floatholders=top10_floatholders,
    )
    factor_panel = EventFactorBuilder().build(
        factor_panel,
        forecast=forecast,
        express=express,
        report_rc=report_rc,
        disclosure_date=disclosure_date,
        survey=survey,
    )
    factor_panel = FundamentalFactorBuilder().build(
        factor_panel,
        fina_indicator=fina_indicator,
        income=income,
        balancesheet=balancesheet,
        cashflow=cashflow,
        audit=audit,
    )
    factor_panel = CrossFeatureBuilder().build(factor_panel)
    factor_panel = IndustryFactorBuilder().build(factor_panel, base_factor_cols=["pct_chg", "net_mf_rate", "winner_rate"])
    factor_panel = MarketFactorBuilder().build(
        factor_panel,
        market_money_flow=pd.DataFrame(
            [
                {
                    "trade_date": "2026-01-03",
                    "net_mf_amount": 500.0,
                    "net_amount_rate": 0.12,
                    "buy_elg_amount_rate": 0.30,
                    "buy_sm_amount_rate": 0.10,
                }
            ]
        ),
        market_hsgt=pd.DataFrame([{"trade_date": "2026-01-03", "north_money": 200.0}]),
        ah_comparison=pd.DataFrame(
            [
                {"ts_code": "000001.SZ", "trade_date": "2026-01-02", "ah_comparison": 1.1, "ah_premium": 0.10},
                {"ts_code": "000001.SZ", "trade_date": "2026-01-03", "ah_comparison": 1.2, "ah_premium": 0.15},
            ]
        ),
        market_margin=pd.DataFrame(
            [
                {"trade_date": "2026-01-02", "rzrqye": 1000.0},
                {"trade_date": "2026-01-03", "rzrqye": 1100.0},
            ]
        ),
    )

    assert round(factor_panel.loc[0, "net_mf_rate"], 6) == 0.1
    assert round(factor_panel.loc[0, "chip_width"], 6) == round((12.0 - 8.0) / 9.5, 6)
    assert factor_panel.loc[0, "hsgt_top10_flag"] == 1.0
    assert round(factor_panel.loc[0, "rzmre_intensity"], 6) == 0.05
    assert round(factor_panel.loc[0, "seal_amount_ratio"], 6) == 0.05
    assert factor_panel.loc[0, "inst_net_buy"] == 30.0
    assert round(factor_panel.loc[0, "block_discount"], 6) == -0.02
    assert round(factor_panel.loc[0, "holder_num_chg"], 6) == -0.1
    assert factor_panel.loc[0, "top10_holder_concentration"] == 12.0
    assert factor_panel.loc[0, "top10_float_holder_concentration"] == 6.0
    assert factor_panel.loc[0, "turnaround_flag"] == 1.0
    assert round(factor_panel.loc[0, "q_ocf_to_sales"], 6) == 0.4
    assert "chip_breakout_strength" in factor_panel.columns
    assert "ind_rel_pct_chg" in factor_panel.columns
    assert "mkt_advance_ratio" in factor_panel.columns
    assert factor_panel.loc[0, "mkt_dc_main_strength"] == 0.12
    assert round(factor_panel.loc[0, "mkt_big_small_split"], 6) == 0.20
    assert round(factor_panel.loc[0, "ah_premium_chg"], 6) == 0.5
    assert "peer_momentum" in factor_panel.columns


def test_limit_factor_builder_merges_limit_price_metadata():
    panel = pd.DataFrame(
        [
            {"ts_code": "000001.SZ", "trade_date": "2026-01-03", "open": 10.0, "close": 11.0},
        ]
    )
    limit_price = pd.DataFrame(
        [
            {"ts_code": "000001.SZ", "trade_date": "2026-01-03", "pre_close": 10.0, "up_limit": 11.0, "down_limit": 9.0},
        ]
    )

    factor_panel = LimitFactorBuilder().build(panel, limit_price=limit_price)

    assert factor_panel.loc[0, "limit_up_price"] == 11.0
    assert factor_panel.loc[0, "limit_down_price"] == 9.0
    assert factor_panel.loc[0, "close_limit_up_flag"] == 1.0
    assert factor_panel.loc[0, "one_word_limit_up_flag"] == 0.0


def test_chip_factor_builder_handles_missing_chip_sources():
    panel = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "2026-01-03",
                "close_qfq": 10.0,
            }
        ]
    )

    factor_panel = ChipFactorBuilder().build(panel)

    assert "avg_cost_gap" in factor_panel.columns
    assert factor_panel["avg_cost_gap"].isna().all()
    assert factor_panel["upper_overhang"].isna().all()


def test_composite_pipeline_correlation_and_report_generation(tmp_path):
    panel = pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "ts_code": "A", "alpha_1": 1.0, "alpha_2": 1.2, "overnight_return": 0.01},
            {"trade_date": "2026-01-02", "ts_code": "B", "alpha_1": 2.0, "alpha_2": 2.4, "overnight_return": 0.02},
            {"trade_date": "2026-01-03", "ts_code": "A", "alpha_1": 1.5, "alpha_2": 1.7, "overnight_return": 0.03},
            {"trade_date": "2026-01-03", "ts_code": "B", "alpha_1": 0.5, "alpha_2": 0.4, "overnight_return": -0.01},
        ]
    )

    composite = CompositeFactorBuilder().build(
        panel,
        factor_cols=["alpha_1", "alpha_2"],
        target_col="overnight_return",
        method="equal_weight",
    )
    standardized = run_standard_factor_pipeline(composite, factor_cols=["composite_factor"])
    correlation = analyze_factor_correlation(standardized, factor_cols=["alpha_1", "alpha_2", "composite_factor"])

    output_dir = tmp_path / "reports"
    report = ResearchReportBuilder(output_dir)
    report_paths = report.build_factor_report(
        factor_name="composite_factor",
        ic_result={
            "ic_series": pd.DataFrame({"trade_date": ["2026-01-02"], "ic": [1.0], "rank_ic": [1.0]}),
            "mean_ic": 1.0,
            "rank_ic": 1.0,
            "ic_ir": 0.0,
            "positive_rate": 1.0,
            "coverage": 1.0,
            "trade_date_coverage": 1.0,
            "active_trade_date_coverage": 1.0,
            "rolling_1y_valid_ratio": 0.0,
            "passes_rolling_stability": False,
        },
        layered_result={
            "group_returns": pd.DataFrame({1: [0.01], 5: [0.03]}, index=["2026-01-02"]),
            "long_short_returns": pd.Series([0.02], index=["2026-01-02"]),
            "group_return_means": {1: 0.01, 5: 0.03},
            "grouped_panel": standardized,
        },
        correlation_result=correlation,
    )
    ranking_assets = report.build_ranking_report(
        pd.DataFrame([{"factor_name": "composite_factor", "ic_ir": 0.8, "coverage": 1.0}]),
        report_name="factor_ranking",
    )
    strategy_assets = report.build_strategy_comparison_report(
        pd.DataFrame(
            [
                {"strategy_name": "equal", "sharpe_ratio": 1.2, "annual_return": 0.2, "max_drawdown": -0.1},
                {"strategy_name": "ml", "sharpe_ratio": 1.4, "annual_return": 0.25, "max_drawdown": -0.12},
            ]
        )
    )

    assert "composite_factor" in composite.columns
    assert round(float(composite["composite_factor_weight"].iloc[0]), 6) == 0.5
    assert correlation["correlation_matrix"].shape == (3, 3)
    assert Path(report_paths["summary_csv"]).exists()
    assert Path(report_paths["detail_html"]).exists()
    assert Path(report_paths["ic_series_csv"]).exists()
    assert Path(report_paths["ic_plot"]).exists()
    assert Path(report_paths["correlation_heatmap"]).exists()
    assert Path(ranking_assets["overview_html"]).exists()
    assert Path(strategy_assets["overview_html"]).exists()
    assert Path(strategy_assets["sharpe_plot"]).exists()


def test_composite_ml_builder_tracks_selected_model():
    panel = pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "ts_code": "A", "alpha_1": 1.0, "alpha_2": 1.2, "overnight_return": 0.01},
            {"trade_date": "2026-01-02", "ts_code": "B", "alpha_1": 2.0, "alpha_2": 2.4, "overnight_return": 0.02},
            {"trade_date": "2026-01-03", "ts_code": "A", "alpha_1": 1.2, "alpha_2": 1.1, "overnight_return": 0.015},
            {"trade_date": "2026-01-03", "ts_code": "B", "alpha_1": 2.4, "alpha_2": 2.1, "overnight_return": 0.03},
        ]
    )

    composite = CompositeFactorBuilder().build(
        panel,
        factor_cols=["alpha_1", "alpha_2"],
        target_col="overnight_return",
        method="ml",
    )

    assert "composite_factor" in composite.columns
    assert composite.attrs["composite_ml_model"] in {"lightgbm", "xgboost", "gradient_boosting", "fallback_equal_weight"}
    assert {"weight_alpha_1", "weight_alpha_2"}.issubset(composite.columns)
