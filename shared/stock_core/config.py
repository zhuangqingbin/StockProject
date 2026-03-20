import os

from .env import bootstrap_project_env


bootstrap_project_env(__file__)


def get_env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip()


def require_env(name: str) -> str:
    value = get_env(name)
    if not value:
        raise ValueError(f"Missing required environment variable {name}")
    return value


def get_int(name: str, default: int) -> int:
    raw_value = get_env(name, str(default))
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer, got {raw_value!r}") from exc


def require_int(name: str) -> int:
    raw_value = require_env(name)
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer, got {raw_value!r}") from exc


def get_csv(name: str, default: str = "") -> list[str]:
    raw_value = get_env(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


_get_env = get_env
_get_int = get_int
_get_csv = get_csv

TOKEN = get_env("TUSHARE_TOKEN")

MAIL_HOST = get_env("MAIL_HOST", "smtp.gmail.com")
MAIL_USER = get_env("MAIL_USER")
MAIL_TOKEN = get_env("MAIL_TOKEN")
SENDER = get_env("MAIL_SENDER", MAIL_USER)
RECEVIERS = get_csv("MAIL_RECEIVERS")
RECEIVERS = RECEVIERS
SENDER_NAME = get_env("MAIL_SENDER_NAME", "量化机器人")
RECEVIER_NAME = get_env("MAIL_RECEIVER_NAME", "终端用户")
RECEIVER_NAME = RECEVIER_NAME

MYSQL_USER = get_env("MYSQL_USER")
MYSQL_PASSWORD = get_env("MYSQL_PASSWORD")
MYSQL_HOST = get_env("MYSQL_HOST")
MYSQL_PORT = get_env("MYSQL_PORT")
MYSQL_DATABASE = get_env("MYSQL_DATABASE")
MYSQL_CHARSET = get_env("MYSQL_CHARSET")

__all__ = [
    "get_env",
    "require_env",
    "get_int",
    "require_int",
    "get_csv",
    "TOKEN",
    "MAIL_HOST",
    "MAIL_USER",
    "MAIL_TOKEN",
    "SENDER",
    "RECEVIERS",
    "RECEIVERS",
    "SENDER_NAME",
    "RECEVIER_NAME",
    "RECEIVER_NAME",
    "MYSQL_USER",
    "MYSQL_PASSWORD",
    "MYSQL_HOST",
    "MYSQL_PORT",
    "MYSQL_DATABASE",
    "MYSQL_CHARSET",
]
