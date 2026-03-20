from __future__ import annotations

from typing import Literal, cast

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from shared.stock_core.db import build_mysql_url as build_shared_mysql_url


DatabaseSource = Literal["ts", "ak"]
DATABASE_ENV_BY_SOURCE = {
    "ts": "TS_MYSQL_DATABASE",
    "ak": "AK_MYSQL_DATABASE",
}

_engines: dict[DatabaseSource, Engine] = {}


def _resolve_database_env(source: DatabaseSource) -> str:
    env_name = DATABASE_ENV_BY_SOURCE.get(source)
    if env_name is None:
        raise ValueError(f"Unknown database source: {source}")
    return env_name


def build_mysql_url(source: DatabaseSource = "ts") -> str:
    return build_shared_mysql_url(_resolve_database_env(source))


def get_engine(source: DatabaseSource = "ts") -> Engine:
    engine = _engines.get(source)
    if engine is None:
        engine = create_engine(build_mysql_url(source), pool_pre_ping=True, pool_recycle=3600)
        _engines[cast(DatabaseSource, source)] = engine
    return engine
