from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .settings import DATABASE_URL


class Base(DeclarativeBase):
    pass


def _build_connect_args() -> dict[str, object]:
    if DATABASE_URL.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


engine = create_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=not DATABASE_URL.startswith("sqlite"),
    pool_recycle=3600,
    connect_args=_build_connect_args(),
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def execute_sql(sql: str, params: dict[str, object] | None = None) -> list[dict[str, object]]:
    with SessionLocal() as session:
        result = session.execute(text(sql), params or {})
        return [dict(row) for row in result.mappings().all()]


def execute_scalar(sql: str, params: dict[str, object] | None = None) -> object:
    with SessionLocal() as session:
        return session.execute(text(sql), params or {}).scalar()


def create_all() -> None:
    Base.metadata.create_all(bind=engine)


def drop_all() -> None:
    Base.metadata.drop_all(bind=engine)


def reset_database() -> None:
    drop_all()
    create_all()
