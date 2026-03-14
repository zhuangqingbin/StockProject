import os


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


def _get_csv(name: str, default: str = "") -> list[str]:
    raw_value = _get_env(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


TOKEN = _get_env("TUSHARE_TOKEN")

MAIL_HOST = _get_env("MAIL_HOST", "smtp.gmail.com")
MAIL_USER = _get_env("MAIL_USER")
MAIL_TOKEN = _get_env("MAIL_TOKEN")
SENDER = _get_env("MAIL_SENDER", MAIL_USER)
RECEVIERS = _get_csv("MAIL_RECEIVERS")
RECEIVERS = RECEVIERS
SENDER_NAME = _get_env("MAIL_SENDER_NAME", "量化机器人")
RECEVIER_NAME = _get_env("MAIL_RECEIVER_NAME", "终端用户")

MYSQL_USER = _get_env("MYSQL_USER", "root")
MYSQL_PASSWORD = _get_env("MYSQL_PASSWORD")
MYSQL_HOST = _get_env("MYSQL_HOST", "localhost")
MYSQL_PORT = _get_int("MYSQL_PORT", 3306)
MYSQL_DATABASE = _get_env("MYSQL_DATABASE", "stock_database")
MYSQL_CHARSET = _get_env("MYSQL_CHARSET", "utf8")

__all__ = [
    "TOKEN",
    "MAIL_HOST",
    "MAIL_USER",
    "MAIL_TOKEN",
    "SENDER",
    "RECEVIERS",
    "RECEIVERS",
    "SENDER_NAME",
    "RECEVIER_NAME",
    "MYSQL_USER",
    "MYSQL_PASSWORD",
    "MYSQL_HOST",
    "MYSQL_PORT",
    "MYSQL_DATABASE",
    "MYSQL_CHARSET",
]
