from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .backtest_config import PortfolioBacktestConfig


def _pivot_long_frame(frame: pd.DataFrame, value_col: str) -> pd.DataFrame:
    if isinstance(frame.index, pd.MultiIndex):
        base = frame.reset_index()
    else:
        base = frame.copy()
    wide = base.pivot(index="trade_date", columns="ts_code", values=value_col).sort_index()
    wide.index = wide.index.astype(str)
    return wide.fillna(0.0)


def _constraint_base(frame: pd.DataFrame) -> pd.DataFrame:
    if isinstance(frame.index, pd.MultiIndex):
        return frame.reset_index()
    return frame.copy()


def build_trade_constraints(
    panel: pd.DataFrame,
    *,
    enforce_limit: bool = True,
    enforce_suspend: bool = True,
) -> pd.DataFrame:
    frame = _constraint_base(panel)
    constraints = frame.loc[:, ["trade_date", "ts_code"]].copy()
    constraints["can_buy"] = True
    constraints["can_sell"] = True
    constraints["is_suspended"] = False

    if enforce_limit:
        limit_up_col = next((column for column in ("limit_up_price", "up_limit") if column in frame.columns), None)
        limit_down_col = next((column for column in ("limit_down_price", "down_limit") if column in frame.columns), None)
        if limit_up_col is not None:
            close_hit_limit_up = np.isclose(
                frame.get("close", pd.Series(np.nan, index=frame.index, dtype=float)),
                frame[limit_up_col],
                equal_nan=False,
            )
            one_word_limit_up = np.isclose(
                frame.get("open", pd.Series(np.nan, index=frame.index, dtype=float)),
                frame[limit_up_col],
                equal_nan=False,
            )
            constraints.loc[close_hit_limit_up | one_word_limit_up, "can_buy"] = False
        if limit_down_col is not None:
            close_hit_limit_down = np.isclose(
                frame.get("close", pd.Series(np.nan, index=frame.index, dtype=float)),
                frame[limit_down_col],
                equal_nan=False,
            )
            constraints.loc[close_hit_limit_down, "can_sell"] = False

    if enforce_suspend:
        suspended_col = next((column for column in ("is_suspended", "_is_suspended") if column in frame.columns), None)
        if suspended_col is not None:
            suspended = frame[suspended_col].fillna(False).astype(bool)
            constraints["is_suspended"] = suspended
            constraints.loc[suspended, ["can_buy", "can_sell"]] = False

    return constraints


@dataclass
class PortfolioBacktestResult:
    daily_results: pd.DataFrame
    actual_weights: pd.DataFrame
    summary: dict[str, float]


class PortfolioBacktestEngine:
    def __init__(self, config: PortfolioBacktestConfig | None = None):
        self.config = config or PortfolioBacktestConfig()

    def _constraint_frames(self, constraints: pd.DataFrame | None, columns: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        if constraints is None or constraints.empty:
            empty = pd.DataFrame(index=[], columns=columns)
            return empty, empty, empty

        frame = constraints.reset_index(drop=True) if isinstance(constraints.index, pd.MultiIndex) else constraints.copy()
        can_buy = frame.pivot(index="trade_date", columns="ts_code", values="can_buy").reindex(columns=columns).fillna(True)
        can_sell = frame.pivot(index="trade_date", columns="ts_code", values="can_sell").reindex(columns=columns).fillna(True)
        suspended = frame.pivot(index="trade_date", columns="ts_code", values="is_suspended").reindex(columns=columns).fillna(False)
        can_buy.index = can_buy.index.astype(str)
        can_sell.index = can_sell.index.astype(str)
        suspended.index = suspended.index.astype(str)
        return can_buy, can_sell, suspended

    def _apply_constraints(
        self,
        target: pd.Series,
        previous: pd.Series,
        can_buy: pd.Series,
        can_sell: pd.Series,
        suspended: pd.Series,
    ) -> pd.Series:
        actual = previous.copy()

        sellable_mask = (~suspended) & can_sell & (target < actual)
        actual.loc[sellable_mask] = target.loc[sellable_mask]

        desired_additions = (target - actual).clip(lower=0.0)
        desired_additions.loc[suspended | (~can_buy)] = 0.0

        remaining_budget = max(1.0 - actual.clip(lower=0.0).sum(), 0.0)
        total_additions = desired_additions.sum()
        if total_additions > 0 and remaining_budget > 0:
            scaled_additions = desired_additions if total_additions <= remaining_budget else desired_additions / total_additions * remaining_budget
            actual = actual + scaled_additions

        actual.loc[suspended] = previous.loc[suspended]
        return actual

    def run(
        self,
        weights: pd.DataFrame,
        returns: pd.DataFrame,
        constraints: pd.DataFrame | None = None,
        benchmark_returns: pd.DataFrame | None = None,
    ) -> PortfolioBacktestResult:
        weight_wide = _pivot_long_frame(weights, "target_weight")
        return_wide = _pivot_long_frame(returns, returns.columns[-1] if "overnight_return" not in returns.columns else "overnight_return")
        benchmark_series = None
        if benchmark_returns is not None and not benchmark_returns.empty:
            benchmark_base = _constraint_base(benchmark_returns)
            benchmark_col = next(
                (column for column in benchmark_base.columns if column not in {"trade_date", "ts_code"}),
                None,
            )
            if benchmark_col is not None:
                benchmark_series = benchmark_base.groupby("trade_date", dropna=False)[benchmark_col].mean()
                benchmark_series.index = benchmark_series.index.astype(str)
        columns = sorted(set(weight_wide.columns).union(return_wide.columns))
        weight_wide = weight_wide.reindex(columns=columns, fill_value=0.0)
        return_wide = return_wide.reindex(index=weight_wide.index, columns=columns, fill_value=0.0)
        can_buy, can_sell, suspended = self._constraint_frames(constraints, columns)

        previous = pd.Series(0.0, index=columns, dtype=float)
        nav = self.config.initial_capital
        daily_records: list[dict[str, float | str]] = []
        actual_weights: list[pd.Series] = []

        for trade_date in weight_wide.index:
            target = weight_wide.loc[trade_date].fillna(0.0)
            buy_row = can_buy.loc[trade_date] if trade_date in can_buy.index else pd.Series(True, index=columns)
            sell_row = can_sell.loc[trade_date] if trade_date in can_sell.index else pd.Series(True, index=columns)
            suspended_row = suspended.loc[trade_date] if trade_date in suspended.index else pd.Series(False, index=columns)
            actual = self._apply_constraints(target, previous, buy_row, sell_row, suspended_row)

            delta = actual - previous
            turnover = float(delta.abs().sum())
            sell_turnover = float((-delta).clip(lower=0.0).sum())
            nav_before_trade = nav
            trade_notionals = delta.abs() * nav_before_trade
            if nav_before_trade > 0:
                commission_cost = float(
                    np.where(
                        trade_notionals.gt(0),
                        np.maximum(trade_notionals * self.config.commission_rate, self.config.min_commission),
                        0.0,
                    ).sum()
                    / nav_before_trade
                )
            else:
                commission_cost = 0.0
            slippage_cost = turnover * self.config.slippage
            stamp_tax_cost = sell_turnover * self.config.stamp_tax
            trading_cost = commission_cost + slippage_cost + stamp_tax_cost
            portfolio_return = float((actual * return_wide.loc[trade_date]).sum() - trading_cost)
            benchmark_return = float(benchmark_series.loc[trade_date]) if benchmark_series is not None and trade_date in benchmark_series.index else 0.0
            excess_return = portfolio_return - benchmark_return
            nav *= 1 + portfolio_return

            daily_records.append(
                {
                    "trade_date": trade_date,
                    "portfolio_return": portfolio_return,
                    "benchmark_return": benchmark_return,
                    "excess_return": excess_return,
                    "turnover": turnover,
                    "trading_cost": trading_cost,
                    "nav": nav,
                }
            )
            actual_weights.append(actual.rename(trade_date))
            previous = actual

        daily_results = pd.DataFrame(daily_records).set_index("trade_date")
        weight_history = pd.DataFrame(actual_weights)
        total_return = nav / self.config.initial_capital - 1
        annual_return = (1 + total_return) ** (252 / max(len(daily_results), 1)) - 1
        returns_series = daily_results["portfolio_return"]
        sharpe = 0.0 if returns_series.std(ddof=0) == 0 else float((returns_series.mean() / returns_series.std(ddof=0)) * np.sqrt(252))
        excess_series = daily_results["excess_return"]
        information_ratio = (
            0.0
            if excess_series.std(ddof=0) == 0
            else float((excess_series.mean() / excess_series.std(ddof=0)) * np.sqrt(252))
        )
        drawdown = daily_results["nav"] / daily_results["nav"].cummax() - 1
        max_drawdown = float(drawdown.min()) if not drawdown.empty else 0.0
        drawdown_duration = 0
        max_drawdown_duration = 0
        for value in drawdown.fillna(0.0):
            if value < 0:
                drawdown_duration += 1
                max_drawdown_duration = max(max_drawdown_duration, drawdown_duration)
            else:
                drawdown_duration = 0
        calmar = 0.0 if max_drawdown == 0 else float(annual_return / abs(max_drawdown))
        benchmark_total_return = (
            float((1 + daily_results["benchmark_return"]).prod() - 1) if not daily_results.empty else 0.0
        )
        win_rate = float((returns_series > 0).mean()) if not returns_series.empty else 0.0
        avg_gain = float(returns_series.loc[returns_series > 0].mean()) if (returns_series > 0).any() else 0.0
        avg_loss = float(abs(returns_series.loc[returns_series < 0].mean())) if (returns_series < 0).any() else 0.0
        profit_loss_ratio = 0.0 if avg_loss == 0 else float(avg_gain / avg_loss)
        monthly_win_rate = 0.0
        if not daily_results.empty:
            monthly_frame = daily_results.assign(trade_date_dt=pd.to_datetime(daily_results.index, errors="coerce")).dropna(
                subset=["trade_date_dt"]
            )
            if not monthly_frame.empty:
                monthly_excess = monthly_frame.groupby(
                    monthly_frame["trade_date_dt"].dt.to_period("M")
                )["excess_return"].apply(lambda values: float((1 + values).prod() - 1))
                monthly_win_rate = float((monthly_excess > 0).mean()) if not monthly_excess.empty else 0.0
        summary = {
            "final_nav": float(nav),
            "total_return": float(total_return),
            "annual_return": float(annual_return),
            "sharpe_ratio": float(sharpe),
            "max_drawdown": float(abs(max_drawdown)),
            "max_drawdown_duration": int(max_drawdown_duration),
            "calmar_ratio": float(calmar),
            "win_rate": float(win_rate),
            "profit_loss_ratio": float(profit_loss_ratio),
            "average_turnover": float(daily_results["turnover"].mean()) if not daily_results.empty else 0.0,
            "benchmark_return": float(benchmark_total_return),
            "excess_return": float(total_return - benchmark_total_return),
            "information_ratio": float(information_ratio),
            "monthly_win_rate": float(monthly_win_rate),
        }
        return PortfolioBacktestResult(daily_results=daily_results, actual_weights=weight_history, summary=summary)
