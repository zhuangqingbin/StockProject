"""Core shared stock project utilities."""

from importlib import import_module


__all__ = [
    "config",
    "db",
    "python_runtime",
    "build_mysql_url",
    "create_mysql_engine",
]


def __getattr__(name: str):
    if name in {"config", "db", "python_runtime"}:
        return import_module(f"{__name__}.{name}")

    if name in {"build_mysql_url", "create_mysql_engine"}:
        module = import_module(f"{__name__}.db")
        return getattr(module, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
