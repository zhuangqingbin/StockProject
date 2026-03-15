from datetime import datetime
from typing import Optional

from ..market_summary.application import normalize_trade_date


def precompute_and_save(trade_date: str):
    from ...precompute import precompute_and_save as _precompute_and_save

    return _precompute_and_save(trade_date)


async def notify_data_update(trade_date: Optional[str] = None):
    from ...routers.websocket import notify_data_update as _notify_data_update

    return await _notify_data_update(trade_date)


def build_connected_message(trade_date: str) -> dict:
    return {
        "type": "connected",
        "trade_date": trade_date,
        "timestamp": datetime.now().isoformat(),
    }


def build_status_message(trade_date: str, connections: int) -> dict:
    return {
        "type": "status",
        "trade_date": trade_date,
        "connections": connections,
    }


def build_data_updated_message(current_date: str, previous_date: Optional[str] = None, manual: bool = False) -> dict:
    payload = {
        "type": "data_updated",
        "trade_date": current_date,
        "timestamp": datetime.now().isoformat(),
    }
    if previous_date:
        payload["previous_date"] = previous_date
    if manual:
        payload["manual"] = True
    return payload


async def sync_market_data_update(trade_date: str) -> dict:
    target_date = normalize_trade_date(trade_date)
    if target_date is None:
        raise ValueError("trade_date is required")

    summary = precompute_and_save(target_date)
    notification = await notify_data_update(target_date)

    return {
        "status": "success",
        "trade_date": target_date,
        "summary_total_stocks": int(summary.get("total_stocks", 0) or 0),
        "notification": notification,
    }
