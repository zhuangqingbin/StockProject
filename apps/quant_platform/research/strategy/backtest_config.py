from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PortfolioBacktestConfig:
    initial_capital: float = 10_000_000
    commission_rate: float = 0.0003
    stamp_tax: float = 0.001
    slippage: float = 0.002
    min_commission: float = 0.0
    benchmark: str = "000300.SH"
    enforce_t1: bool = True
    enforce_limit: bool = True
    enforce_suspend: bool = True
