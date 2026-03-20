from sqlalchemy import create_engine

from .config import require_env, require_int


def build_mysql_url(database_env_name: str = "MYSQL_DATABASE") -> str:
    user = require_env("MYSQL_USER")
    password = require_env("MYSQL_PASSWORD")
    host = require_env("MYSQL_HOST")
    port = require_int("MYSQL_PORT")
    database = require_env(database_env_name)
    charset = require_env("MYSQL_CHARSET")
    return (
        f"mysql+pymysql://{user}:{password}@{host}:{port}/"
        f"{database}?charset={charset}"
    )


def create_mysql_engine():
    return create_engine(build_mysql_url())
