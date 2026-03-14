"""
Stable backend settings extracted from legacy compatibility modules.
"""
import os

from shared.stock_core.config import (
    MYSQL_CHARSET,
    MYSQL_DATABASE,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
    TOKEN as TUSHARE_TOKEN,
)
from shared.stock_core.db import build_mysql_url


def _get_env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip()


def _get_int(name: str, default: int) -> int:
    raw_value = _get_env(name, str(default))
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer, got {raw_value!r}") from exc


DATABASE_URL = build_mysql_url()

OPENAI_API_KEY = _get_env("OPENAI_API_KEY")
OPENAI_BASE_URL = _get_env("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = _get_env("OPENAI_MODEL", "gpt-4o-mini")

API_HOST = _get_env("API_HOST", "0.0.0.0")
API_PORT = _get_int("API_PORT", 8000)

__all__ = [
    "API_HOST",
    "API_PORT",
    "DATABASE_URL",
    "MYSQL_CHARSET",
    "MYSQL_DATABASE",
    "MYSQL_HOST",
    "MYSQL_PASSWORD",
    "MYSQL_PORT",
    "MYSQL_USER",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_MODEL",
    "TUSHARE_TOKEN",
]
