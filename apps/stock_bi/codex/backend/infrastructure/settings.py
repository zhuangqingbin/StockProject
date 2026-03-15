"""
Stable backend settings extracted from legacy compatibility modules.
"""
from shared.stock_core.config import (
    MYSQL_CHARSET,
    MYSQL_DATABASE,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
    TOKEN as TUSHARE_TOKEN,
    get_env,
    get_int,
)
from shared.stock_core.db import build_mysql_url


DATABASE_URL = build_mysql_url()

OPENAI_API_KEY = get_env("OPENAI_API_KEY")
OPENAI_BASE_URL = get_env("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = get_env("OPENAI_MODEL", "gpt-4o-mini")

API_HOST = get_env("API_HOST", "0.0.0.0")
API_PORT = get_int("API_PORT", 8000)

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
