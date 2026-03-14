"""
Shared in-memory cache helpers for the stock BI backend.
"""
import time
from functools import wraps
from typing import Any, Dict, Optional


class SimpleCache:
    """Simple in-memory cache with TTL-based expiry."""

    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None

        value, expire_time = self._cache[key]
        if time.time() >= expire_time:
            del self._cache[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        expire_after = self._default_ttl if ttl is None else ttl
        self._cache[key] = (value, time.time() + expire_after)

    def delete(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        self._cache.clear()


cache = SimpleCache(default_ttl=300)


def cached(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            result = cache.get(key)
            if result is not None:
                return result

            result = await func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result

        return wrapper

    return decorator
