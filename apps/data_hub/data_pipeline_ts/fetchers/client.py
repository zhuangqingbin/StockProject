from __future__ import annotations

from collections import deque
import hashlib
import json
import os
import pickle
import time
from dataclasses import dataclass
from typing import Any, Callable

try:
    import tushare as ts
except ImportError:  # pragma: no cover - exercised only when dependency missing
    ts = None

from shared.stock_core.config import get_env


@dataclass(frozen=True)
class ClientConfig:
    token: str = get_env("TUSHARE_TOKEN", "")
    min_interval_seconds: float = 0.0
    max_calls_per_minute: int | None = None
    retries: int = 2
    backoff_seconds: float = 0.6
    timeout_seconds: float | None = None
    cache_dir: str | None = None
    cache_ttl_seconds: int | None = 24 * 3600


class TuShareClient:
    def __init__(self, config: ClientConfig | None = None, pro: Any = None):
        self.config = config or ClientConfig()
        if pro is not None:
            self.pro = pro
        else:
            if ts is None:
                raise RuntimeError("tushare is required when no pro client is injected")
            self.pro = ts.pro_api(self.config.token)
        self._last_call_ts = 0.0
        self._request_timestamps: deque[float] = deque()
        self.cache_dir = self._resolve_cache_dir()
        if self.cache_dir is not None:
            os.makedirs(self.cache_dir, exist_ok=True)

    def _resolve_cache_dir(self) -> str | None:
        if self.config.cache_dir is not None:
            return self.config.cache_dir
        app_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        return os.path.join(app_root, ".cache", "tushare")

    def _sleep_if_needed(self) -> None:
        min_interval = float(self.config.min_interval_seconds or 0.0)
        if min_interval <= 0:
            return
        elapsed = time.time() - self._last_call_ts
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

    def _throttle_if_needed(self) -> None:
        max_calls = self.config.max_calls_per_minute
        if max_calls is None or int(max_calls) <= 0:
            return

        window_seconds = 60.0
        now = time.monotonic()
        while self._request_timestamps and now - self._request_timestamps[0] >= window_seconds:
            self._request_timestamps.popleft()

        if len(self._request_timestamps) < int(max_calls):
            return

        sleep_seconds = window_seconds - (now - self._request_timestamps[0])
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

        now = time.monotonic()
        while self._request_timestamps and now - self._request_timestamps[0] >= window_seconds:
            self._request_timestamps.popleft()

    def _cache_path(self, endpoint: str, params: dict[str, Any]) -> str:
        payload = {"endpoint": endpoint, "params": params}
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
        key = hashlib.sha256(raw).hexdigest()[:24]
        safe_endpoint = "".join(ch if (ch.isalnum() or ch in {"-", "_"}) else "_" for ch in endpoint)
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
            with open(path, "rb") as handle:
                return pickle.load(handle)
        except Exception:
            return None

    def _cache_write(self, path: str, value: Any) -> None:
        try:
            with open(path, "wb") as handle:
                pickle.dump(value, handle, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception:
            pass

    def _execute(self, endpoint: str, fn: Callable[..., Any], **params: Any) -> Any:
        cache_path = None
        if self.cache_dir is not None:
            cache_path = self._cache_path(endpoint, params)
            cached = self._cache_read(cache_path)
            if cached is not None:
                return cached

        last_error: BaseException | None = None
        for attempt in range(int(self.config.retries) + 1):
            try:
                self._sleep_if_needed()
                self._throttle_if_needed()
                self._request_timestamps.append(time.monotonic())
                result = fn(**params)
                self._last_call_ts = time.time()
                if cache_path is not None:
                    self._cache_write(cache_path, result)
                return result
            except Exception as exc:
                last_error = exc
                if attempt >= int(self.config.retries):
                    break
                time.sleep(float(self.config.backoff_seconds) * (2**attempt))

        raise RuntimeError(f"TuShare call failed: {endpoint}, params={params}") from last_error

    def call(self, endpoint: str, **params: Any) -> Any:
        fn: Callable[..., Any] = getattr(self.pro, endpoint)
        return self._execute(endpoint, fn, **params)

    def pro_bar(self, **params: Any) -> Any:
        if ts is None:
            raise RuntimeError("tushare is required when pro_bar support is used")

        def _pro_bar(**call_params: Any) -> Any:
            return ts.pro_bar(**call_params)

        return self._execute("pro_bar", _pro_bar, **params)
