import json
import sys

import pandas as pd

from apps.quant_platform.research.scripts import run_single_factor as single_factor_script
from apps.quant_platform.research.factor_engine.composite import CompositeFactorBuilder
from apps.quant_platform.research.scripts.run_single_factor import run_single_factor_analysis
from apps.quant_platform.research.strategy.backtest_config import PortfolioBacktestConfig
from apps.quant_platform.research.strategy.exit_rules import ExitRuleConfig, ExitRuleEngine
from apps.quant_platform.research.strategy.factor_strategy import FactorStrategy
from apps.quant_platform.research.strategy.portfolio_backtest import PortfolioBacktestEngine, build_trade_constraints
from apps.quant_platform.research.strategy.signal_generator import TopPercentSignalGenerator


def test_signal_generator_exit_rules_and_backtest_engine_work_together():
    factor_panel = pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "ts_code": "A", "composite_factor": 2.0},
            {"trade_date": "2026-01-02", "ts_code": "B", "composite_factor": 1.0},
            {"trade_date": "2026-01-03", "ts_code": "A", "composite_factor": -1.0},
            {"trade_date": "2026-01-03", "ts_code": "B", "composite_factor": 3.0},
        ]
    )
    future_returns = pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "ts_code": "A", "overnight_return": 0.10},
            {"trade_date": "2026-01-02", "ts_code": "B", "overnight_return": 0.01},
            {"trade_date": "2026-01-03", "ts_code": "A", "overnight_return": -0.05},
            {"trade_date": "2026-01-03", "ts_code": "B", "overnight_return": 0.02},
        ]
    )
    trade_constraints = pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "ts_code": "A", "can_buy": True, "can_sell": True, "is_suspended": False},
            {"trade_date": "2026-01-02", "ts_code": "B", "can_buy": True, "can_sell": True, "is_suspended": False},
            {"trade_date": "2026-01-03", "ts_code": "A", "can_buy": True, "can_sell": False, "is_suspended": False},
            {"trade_date": "2026-01-03", "ts_code": "B", "can_buy": True, "can_sell": True, "is_suspended": False},
        ]
    )

    signal_generator = TopPercentSignalGenerator(top_pct=0.5, hold_pct=0.5, max_holdings=1, weighting="equal")
    target_weights = signal_generator.generate(factor_panel, factor_col="composite_factor")
    adjusted_weights = ExitRuleEngine(ExitRuleConfig(max_holding_days=1, require_positive_factor=True)).apply(
        target_weights,
        factor_panel=factor_panel,
        factor_col="composite_factor",
    )
    result = PortfolioBacktestEngine(
        PortfolioBacktestConfig(initial_capital=100.0, commission_rate=0.0, stamp_tax=0.0, slippage=0.0)
    ).run(weights=adjusted_weights, returns=future_returns, constraints=trade_constraints)

    assert target_weights.loc[("2026-01-02", "A"), "target_weight"] == 1.0
    assert adjusted_weights.loc[("2026-01-03", "A"), "target_weight"] == 0.0
    assert round(result.summary["final_nav"], 6) == 104.5
    assert result.daily_results.loc["2026-01-02", "turnover"] == 1.0


def test_factor_strategy_and_single_factor_script_helpers():
    panel = pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "ts_code": "A", "alpha_1": 1.0, "alpha_2": 2.0, "overnight_return": 0.10},
            {"trade_date": "2026-01-02", "ts_code": "B", "alpha_1": 2.0, "alpha_2": 1.0, "overnight_return": 0.00},
            {"trade_date": "2026-01-03", "ts_code": "A", "alpha_1": 0.5, "alpha_2": 1.0, "overnight_return": 0.02},
            {"trade_date": "2026-01-03", "ts_code": "B", "alpha_1": 3.0, "alpha_2": 4.0, "overnight_return": 0.05},
        ]
    )
    composite_panel = CompositeFactorBuilder().build(panel, factor_cols=["alpha_1", "alpha_2"], method="equal_weight")

    strategy = FactorStrategy(
        signal_generator=TopPercentSignalGenerator(top_pct=0.5, hold_pct=0.5, max_holdings=1, weighting="equal"),
        backtest_engine=PortfolioBacktestEngine(
            PortfolioBacktestConfig(initial_capital=100.0, commission_rate=0.0, stamp_tax=0.0, slippage=0.0)
        ),
    )
    strategy_result = strategy.run(
        factor_panel=composite_panel,
        factor_col="composite_factor",
        return_col="overnight_return",
    )
    single_factor = run_single_factor_analysis(panel, factor_col="alpha_1", target_col="overnight_return")

    assert "summary" in strategy_result
    assert strategy_result["summary"]["final_nav"] > 100.0
    assert single_factor["ic"]["mean_ic"] != 0.0
    assert "group_return_means" in single_factor["layered"]


def test_single_factor_main_requests_requested_factor_column(monkeypatch, capsys):
    captured: dict[str, object] = {}

    class DummyLoader:
        def load_panel(self, start_date=None, end_date=None, columns=None):
            captured["columns"] = list(columns or [])
            return pd.DataFrame(
                [
                    {"trade_date": "2026-01-02", "ts_code": "A", "pct_chg": 1.0, "overnight_return": 0.10},
                    {"trade_date": "2026-01-02", "ts_code": "B", "pct_chg": 2.0, "overnight_return": 0.00},
                    {"trade_date": "2026-01-03", "ts_code": "A", "pct_chg": 0.5, "overnight_return": 0.02},
                    {"trade_date": "2026-01-03", "ts_code": "B", "pct_chg": 3.0, "overnight_return": 0.05},
                ]
            )

        def prepare_panel(self, panel):
            return panel

    monkeypatch.setattr(single_factor_script, "ResearchDataLoader", lambda: DummyLoader())
    monkeypatch.setattr(sys, "argv", ["run_single_factor.py", "--factor", "pct_chg"])

    single_factor_script.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["factor"] == "pct_chg"
    assert "pct_chg" in captured["columns"]


def test_factor_strategy_auto_constraints_and_extended_metrics():
    factor_panel = pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "ts_code": "A",
                "composite_factor": 1.0,
                "overnight_return": 0.03,
                "benchmark_return": 0.01,
                "open": 10.0,
                "close": 10.0,
                "limit_up_price": 11.0,
                "limit_down_price": 9.0,
            },
            {
                "trade_date": "2026-01-02",
                "ts_code": "B",
                "composite_factor": 2.0,
                "overnight_return": 0.04,
                "benchmark_return": 0.01,
                "open": 10.0,
                "close": 10.0,
                "limit_up_price": 11.0,
                "limit_down_price": 9.0,
            },
            {
                "trade_date": "2026-01-03",
                "ts_code": "A",
                "composite_factor": 3.0,
                "overnight_return": 0.01,
                "benchmark_return": 0.00,
                "open": 10.0,
                "close": 10.0,
                "limit_up_price": 11.0,
                "limit_down_price": 9.0,
            },
            {
                "trade_date": "2026-01-03",
                "ts_code": "B",
                "composite_factor": 1.0,
                "overnight_return": -0.05,
                "benchmark_return": 0.00,
                "open": 9.0,
                "close": 9.0,
                "limit_up_price": 11.0,
                "limit_down_price": 9.0,
            },
        ]
    )

    constraints = build_trade_constraints(factor_panel)
    strategy = FactorStrategy(
        signal_generator=TopPercentSignalGenerator(top_pct=0.5, hold_pct=0.5, max_holdings=1, weighting="equal"),
        backtest_engine=PortfolioBacktestEngine(
            PortfolioBacktestConfig(initial_capital=100.0, commission_rate=0.0, stamp_tax=0.0, slippage=0.0)
        ),
    )
    result = strategy.run(factor_panel=factor_panel, factor_col="composite_factor", return_col="overnight_return")

    assert constraints.loc[3, "can_sell"] == False
    assert result["daily_results"].loc["2026-01-02", "benchmark_return"] == 0.01
    assert result["summary"]["max_drawdown_duration"] >= 0
    assert "information_ratio" in result["summary"]
    assert result["summary"]["monthly_win_rate"] >= 0.0
    assert result["daily_results"].loc["2026-01-03", "turnover"] == 0.0


def test_exit_rule_take_profit_uses_position_return_history():
    factor_panel = pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "ts_code": "A", "composite_factor": 1.0, "overnight_return": 0.05},
            {"trade_date": "2026-01-03", "ts_code": "A", "composite_factor": 1.0, "overnight_return": 0.02},
            {"trade_date": "2026-01-06", "ts_code": "A", "composite_factor": 1.0, "overnight_return": 0.01},
        ]
    )

    strategy = FactorStrategy(
        signal_generator=TopPercentSignalGenerator(top_pct=1.0, hold_pct=1.0, max_holdings=1, weighting="equal"),
        backtest_engine=PortfolioBacktestEngine(
            PortfolioBacktestConfig(initial_capital=100.0, commission_rate=0.0, stamp_tax=0.0, slippage=0.0)
        ),
        exit_rule_engine=ExitRuleEngine(
            ExitRuleConfig(take_profit=0.03, stop_loss=None, max_holding_days=None)
        ),
    )

    result = strategy.run(factor_panel=factor_panel, factor_col="composite_factor", return_col="overnight_return")

    assert result["weights"].loc[("2026-01-03", "A"), "target_weight"] == 0.0
