from __future__ import annotations

__all__ = [
    "get_engine",
    "get_prev_trade_days",
    "get_trade_cal",
    "timer",
]


def __getattr__(name: str):
    if name == "get_engine":
        from .database_runtime import get_engine

        return get_engine
    if name in {"get_prev_trade_days", "get_trade_cal"}:
        from .market_calendar import get_prev_trade_days, get_trade_cal

        return {
            "get_prev_trade_days": get_prev_trade_days,
            "get_trade_cal": get_trade_cal,
        }[name]
    if name == "timer":
        from .timing import timer

        return timer
    raise AttributeError(name)
