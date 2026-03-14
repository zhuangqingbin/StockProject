from typing import Any, Callable, Dict, Optional

from ...infrastructure.cache import cache
from ...infrastructure.database import engine
from .repository import MarketSummaryRepository


repository = MarketSummaryRepository(engine=engine, cache_backend=cache)


def convert_decimal(obj: Any) -> Any:
    from decimal import Decimal

    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {key: convert_decimal(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [convert_decimal(item) for item in obj]
    return obj


def save_summary(summary: Dict[str, Any]) -> None:
    repository.save(summary)


def load_summary(trade_date: str) -> Optional[Dict[str, Any]]:
    return repository.load(trade_date)


def build_or_load_summary(trade_date: str, builder: Callable[[str], Dict[str, Any]]) -> Dict[str, Any]:
    summary = load_summary(trade_date)
    if summary:
        return summary

    summary = builder(trade_date)
    save_summary(summary)
    return summary
