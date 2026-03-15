from __future__ import annotations

from collections.abc import Generator
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .settings import get_settings


class Base(DeclarativeBase):
    """Base ORM model for stock backtest tables."""


_engine = None
_session_factory = None


def create_database_engine(database_url: Optional[str] = None):
    url = database_url or get_settings().database_url
    engine_kwargs: dict[str, object] = {"future": True}

    if url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in url:
            engine_kwargs["poolclass"] = StaticPool
    else:
        engine_kwargs["pool_pre_ping"] = True

    return create_engine(url, **engine_kwargs)


def reset_database() -> None:
    global _engine, _session_factory

    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def get_engine():
    global _engine

    if _engine is None:
        _engine = create_database_engine()
    return _engine


def get_session_factory():
    global _session_factory

    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)
    return _session_factory


def init_database() -> None:
    from apps.stock_backtest.backend.models import db_models  # noqa: F401

    Base.metadata.create_all(bind=get_engine())


def get_db_session() -> Generator[Session, None, None]:
    init_database()
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
