from __future__ import annotations

import numpy as np
import pandas as pd

from .exit_rules import ExitRuleEngine
from .portfolio_backtest import PortfolioBacktestEngine, build_trade_constraints
from .signal_generator import TopPercentSignalGenerator


def _build_position_return_frame(
    weights: pd.DataFrame,
    factor_panel: pd.DataFrame,
    return_col: str,
) -> pd.DataFrame:
    merged = weights.reset_index().merge(
        factor_panel.loc[:, ["trade_date", "ts_code", return_col]],
        on=["trade_date", "ts_code"],
        how="left",
    )
    merged = merged.sort_values(["ts_code", "trade_date"]).reset_index(drop=True)
    merged["position_return"] = np.nan

    for _, index in merged.groupby("ts_code", sort=False).groups.items():
        group = merged.loc[index]
        cumulative_return = 0.0
        was_active = False
        values: list[float] = []
        for active, value in zip(group["target_weight"].gt(0), group[return_col].fillna(0.0)):
            if not active:
                values.append(np.nan)
                cumulative_return = 0.0
                was_active = False
                continue
            values.append(cumulative_return if was_active else 0.0)
            cumulative_return = (1 + cumulative_return) * (1 + float(value)) - 1
            was_active = True
        merged.loc[index, "position_return"] = values

    return merged.loc[:, ["trade_date", "ts_code", "position_return"]]


class FactorStrategy:
    def __init__(
        self,
        signal_generator: TopPercentSignalGenerator | None = None,
        backtest_engine: PortfolioBacktestEngine | None = None,
        exit_rule_engine: ExitRuleEngine | None = None,
    ):
        self.signal_generator = signal_generator or TopPercentSignalGenerator()
        self.backtest_engine = backtest_engine or PortfolioBacktestEngine()
        self.exit_rule_engine = exit_rule_engine

    def run(
        self,
        factor_panel: pd.DataFrame,
        factor_col: str = "composite_factor",
        return_col: str = "overnight_return",
        constraints: pd.DataFrame | None = None,
        benchmark_returns: pd.DataFrame | None = None,
    ) -> dict[str, object]:
        weights = self.signal_generator.generate(factor_panel, factor_col=factor_col)
        enriched_panel = factor_panel
        if self.exit_rule_engine is not None:
            enriched_panel = factor_panel.merge(
                _build_position_return_frame(weights, factor_panel, return_col=return_col),
                on=["trade_date", "ts_code"],
                how="left",
            )
            weights = self.exit_rule_engine.apply(weights, factor_panel=enriched_panel, factor_col=factor_col)
        if constraints is None:
            constraints = build_trade_constraints(
                factor_panel,
                enforce_limit=self.backtest_engine.config.enforce_limit,
                enforce_suspend=self.backtest_engine.config.enforce_suspend,
            )
        returns = factor_panel.loc[:, ["trade_date", "ts_code", return_col]].copy()
        benchmark_frame = benchmark_returns
        if benchmark_frame is None and "benchmark_return" in factor_panel.columns:
            benchmark_frame = factor_panel.loc[:, ["trade_date", "benchmark_return"]].drop_duplicates("trade_date")
        result = self.backtest_engine.run(
            weights=weights,
            returns=returns,
            constraints=constraints,
            benchmark_returns=benchmark_frame,
        )
        return {
            "weights": weights,
            "daily_results": result.daily_results,
            "summary": result.summary,
        }
