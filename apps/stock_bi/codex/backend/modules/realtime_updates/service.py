from datetime import datetime
from typing import Optional


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
