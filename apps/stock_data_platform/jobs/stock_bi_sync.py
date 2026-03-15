from __future__ import annotations

from typing import Any

from .trade_date_http_sync import run_trade_date_post, resolve_port_scan_count


DEFAULT_STOCK_BI_SYNC_URL = "http://127.0.0.1:8000/api/market/sync-update"


def _resolve_port_scan_count() -> int:
    return resolve_port_scan_count("STOCK_BI_SYNC_PORT_SCAN_COUNT")


def sync_stock_bi(trade_date: str, sync_url: str | None = None, timeout_sec: float | None = None) -> dict[str, Any]:
    return run_trade_date_post(
        trade_date,
        operation_name="stock_bi sync",
        default_sync_url=DEFAULT_STOCK_BI_SYNC_URL,
        enabled_env_var="STOCK_BI_SYNC_ENABLED",
        url_env_var="STOCK_BI_SYNC_URL",
        timeout_env_var="STOCK_BI_SYNC_TIMEOUT_SEC",
        port_scan_count_env_var="STOCK_BI_SYNC_PORT_SCAN_COUNT",
        sync_url=sync_url,
        timeout_sec=timeout_sec,
    )
