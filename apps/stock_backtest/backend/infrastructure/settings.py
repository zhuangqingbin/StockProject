from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

from shared.stock_core.db import build_mysql_url
from shared.stock_core.env import bootstrap_project_env


APP_ROOT = Path(__file__).resolve().parents[2]


def _get_env(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned if cleaned else ""


def _get_int(name: str, default: int) -> int:
    raw_value = _get_env(name)
    if raw_value in (None, ""):
        return default
    return int(raw_value)


def _get_float(name: str, default: float) -> float:
    raw_value = _get_env(name)
    if raw_value in (None, ""):
        return default
    return float(raw_value)


@dataclass(frozen=True)
class Settings:
    app_name: str
    api_prefix: str
    database_url: str
    frontend_dist: Optional[Path]
    templates_dir: Path
    notebooks_dir: Path
    execution_mode: str
    max_workers: int
    progress_poll_interval_seconds: float
    default_timeout_seconds: int
    notebook_port: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    bootstrap_project_env(__file__)
    frontend_raw = _get_env("STOCK_BACKTEST_FRONTEND_DIST")
    default_frontend_dist = APP_ROOT / "frontend" / "dist"
    if frontend_raw == "":
        frontend_dist = None
    elif frontend_raw:
        frontend_dist = Path(frontend_raw).expanduser().resolve()
    elif default_frontend_dist.exists():
        frontend_dist = default_frontend_dist
    else:
        frontend_dist = None

    execution_mode = (_get_env("STOCK_BACKTEST_EXECUTION_MODE") or "process").lower()
    if execution_mode not in {"process", "inline"}:
        raise ValueError(f"Unsupported STOCK_BACKTEST_EXECUTION_MODE: {execution_mode}")

    database_url = _get_env("STOCK_BACKTEST_DATABASE_URL") or build_mysql_url()

    return Settings(
        app_name="Stock Backtest Platform",
        api_prefix="/api",
        database_url=database_url,
        frontend_dist=frontend_dist,
        templates_dir=APP_ROOT / "templates",
        notebooks_dir=APP_ROOT / "notebooks",
        execution_mode=execution_mode,
        max_workers=_get_int("STOCK_BACKTEST_MAX_WORKERS", 4),
        progress_poll_interval_seconds=_get_float("STOCK_BACKTEST_PROGRESS_POLL_SECONDS", 1.0),
        default_timeout_seconds=_get_int("STOCK_BACKTEST_TIMEOUT_SECONDS", 600),
        notebook_port=_get_int("STOCK_BACKTEST_NOTEBOOK_PORT", 8891),
    )
