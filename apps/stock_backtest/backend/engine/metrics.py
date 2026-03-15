from __future__ import annotations

import math

import numpy as np
import pandas as pd
from typing import Optional


def build_daily_snapshots(equity_curve: list[dict]) -> list[dict]:
    if not equity_curve:
        return []

    frame = pd.DataFrame(equity_curve).copy()
    frame["trade_date"] = pd.to_datetime(frame["trade_date"])
    frame = frame.sort_values("trade_date").reset_index(drop=True)
    frame["daily_return"] = frame["portfolio_value"].pct_change().fillna(0.0)
    first_value = frame.loc[0, "portfolio_value"]
    frame["cumulative_return"] = frame["portfolio_value"] / first_value - 1
    frame["rolling_peak"] = frame["portfolio_value"].cummax()
    frame["drawdown"] = frame["portfolio_value"] / frame["rolling_peak"] - 1
    return [
        {
            "trade_date": row.trade_date.date().isoformat(),
            "portfolio_value": float(row.portfolio_value),
            "cash": float(row.cash),
            "daily_return": float(row.daily_return),
            "cumulative_return": float(row.cumulative_return),
            "drawdown": float(row.drawdown),
        }
        for row in frame.itertuples(index=False)
    ]


def calculate_performance_metrics(equity_curve: list[dict], trades: Optional[list[dict]] = None) -> dict:
    snapshots = build_daily_snapshots(equity_curve)
    if not snapshots:
        return {
            "total_return": 0.0,
            "annual_return": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "volatility": 0.0,
            "trading_days": 0,
            "trade_count": 0,
            "win_rate": 0.0,
            "profit_loss_ratio": 0.0,
        }

    frame = pd.DataFrame(snapshots)
    daily_returns = frame["daily_return"].astype(float)
    total_return = float(frame.iloc[-1]["cumulative_return"])
    periods = max(len(frame) - 1, 1)
    annual_return = (1 + total_return) ** (252 / periods) - 1
    max_drawdown = float(frame["drawdown"].min())

    std_dev = float(daily_returns.std(ddof=0))
    volatility = std_dev * math.sqrt(252)
    if std_dev == 0:
        sharpe_ratio = 0.0
    else:
        sharpe_ratio = float(daily_returns.mean() / std_dev * math.sqrt(252))

    closed_trade_pnls = [float(item.get("pnl", 0.0)) for item in (trades or []) if item.get("direction") == "sell"]
    wins = [pnl for pnl in closed_trade_pnls if pnl > 0]
    losses = [abs(pnl) for pnl in closed_trade_pnls if pnl < 0]
    trade_count = len(closed_trade_pnls)
    win_rate = float(len(wins) / trade_count) if trade_count else 0.0
    profit_loss_ratio = float(np.mean(wins) / np.mean(losses)) if wins and losses else 0.0

    return {
        "total_return": round(total_return, 6),
        "annual_return": round(float(annual_return), 6),
        "max_drawdown": round(max_drawdown, 6),
        "sharpe_ratio": round(sharpe_ratio, 4),
        "volatility": round(volatility, 6),
        "trading_days": len(frame),
        "trade_count": trade_count,
        "win_rate": round(win_rate, 4),
        "profit_loss_ratio": round(profit_loss_ratio, 4),
    }
