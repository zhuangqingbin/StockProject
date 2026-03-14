from sqlalchemy import create_engine

from .config import MYSQL_CHARSET, MYSQL_DATABASE, MYSQL_HOST, MYSQL_PASSWORD, MYSQL_PORT, MYSQL_USER


def build_mysql_url() -> str:
    return (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/"
        f"{MYSQL_DATABASE}?charset={MYSQL_CHARSET}"
    )


def create_mysql_engine():
    return create_engine(build_mysql_url())
