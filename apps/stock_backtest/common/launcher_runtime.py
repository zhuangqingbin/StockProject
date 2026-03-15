from __future__ import annotations


BACKEND_APP_IMPORT = "apps.stock_backtest.backend.main:app"


def backend_process_pattern() -> str:
    return f"uvicorn {BACKEND_APP_IMPORT}"
