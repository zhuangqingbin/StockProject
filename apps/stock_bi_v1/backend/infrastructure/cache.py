import functools
import hashlib
import json
from collections.abc import Callable
from typing import Any, TypeVar

from cachetools import TTLCache


F = TypeVar("F", bound=Callable[..., Any])

_caches: list[TTLCache] = []


def _make_cache_key(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    payload = json.dumps({"args": args, "kwargs": kwargs}, default=str, sort_keys=True)
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


def cached(ttl: int, maxsize: int = 256) -> Callable[[F], F]:
    cache = TTLCache(maxsize=maxsize, ttl=ttl)
    _caches.append(cache)

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            key = f"{func.__module__}:{func.__qualname__}:{_make_cache_key(args, kwargs)}"
            if key in cache:
                return cache[key]

            result = func(*args, **kwargs)
            cache[key] = result
            return result

        return wrapper  # type: ignore[return-value]

    return decorator


def clear_all_caches() -> None:
    for cache in _caches:
        cache.clear()
