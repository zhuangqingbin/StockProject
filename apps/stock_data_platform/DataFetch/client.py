import hashlib
import json
import os
import pickle
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional

import tushare as ts

from common.config import TOKEN

"""
统一处理 重试 + backoff、简单限流、可选本地 pickle 缓存
    默认缓存到 DataStore/Temp/.tushare_cache, TTL 默认 24h
"""

@dataclass(frozen=True)
class ClientConfig:
    """
    Common behaviors for API calls.
    - cache_dir: set to None to disable cache
    - cache_ttl_seconds: set to 0/None to disable TTL (always reuse if exists)
    """

    token: str = TOKEN
    min_interval_seconds: float = 0.0
    retries: int = 2
    backoff_seconds: float = 0.6
    timeout_seconds: Optional[float] = None  # reserved for future use
    cache_dir: Optional[str] = None
    cache_ttl_seconds: Optional[int] = 24 * 3600


class TuShareClient:
    """
    Thin wrapper for TuShare `pro_api` that centralizes:
    - timer logging
    - retries + backoff
    - naive rate-limiting
    - optional local pickle cache (DataFrame or other picklable payload)
    """

    def __init__(self, config: Optional[ClientConfig] = None, pro: Any = None):
        self.config = config or ClientConfig()
        self.pro = pro if pro is not None else ts.pro_api(self.config.token)
        self._last_call_ts = 0.0

        if self.config.cache_dir is None:
            self.cache_dir = self._default_cache_dir()
        else:
            self.cache_dir = self.config.cache_dir

        if self.cache_dir is not None:
            os.makedirs(self.cache_dir, exist_ok=True)

    def _default_cache_dir(self) -> str:
        project_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        return os.path.join(project_root, "DataStore", "Temp", ".tushare_cache")

    def _sleep_if_needed(self) -> None:
        min_interval = float(self.config.min_interval_seconds or 0.0)
        if min_interval <= 0:
            return
        now = time.time()
        elapsed = now - self._last_call_ts
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

    def _cache_path(self, endpoint: str, params: dict[str, Any]) -> str:
        payload = {"endpoint": endpoint, "params": params}
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
        key = hashlib.sha256(raw).hexdigest()[:24]
        safe_endpoint = "".join(ch if (ch.isalnum() or ch in ("-", "_")) else "_" for ch in endpoint)
        return os.path.join(self.cache_dir or "", f"{safe_endpoint}-{key}.pkl")

    def _cache_read(self, path: str) -> Any:
        if not os.path.exists(path):
            return None
        ttl = self.config.cache_ttl_seconds
        if ttl is not None and ttl > 0:
            age = time.time() - os.path.getmtime(path)
            if age > ttl:
                return None
        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except Exception:
            return None

    def _cache_write(self, path: str, value: Any) -> None:
        try:
            with open(path, "wb") as f:
                pickle.dump(value, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception:
            # Cache must never break data fetching.
            pass

    def call(self, endpoint: str, **params: Any) -> Any:
        """
        Call `self.pro.<endpoint>(**params)` with common behaviors.
        - endpoint: e.g. "daily", "trade_cal"
        """

        fn: Callable[..., Any] = getattr(self.pro, endpoint)

        cache_path = None
        if self.cache_dir is not None:
            cache_path = self._cache_path(endpoint, params)
            cached = self._cache_read(cache_path)
            if cached is not None:
                return cached

        last_error: Optional[BaseException] = None

        for attempt in range(int(self.config.retries) + 1):
            try:
                self._sleep_if_needed()
                result = fn(**params)
                self._last_call_ts = time.time()
                if cache_path is not None:
                    self._cache_write(cache_path, result)
                return result
            except Exception as e:
                last_error = e
                if attempt >= int(self.config.retries):
                    break
                time.sleep(float(self.config.backoff_seconds) * (2**attempt))

        raise RuntimeError(f"TuShare call failed: {endpoint}, params={params}") from last_error
