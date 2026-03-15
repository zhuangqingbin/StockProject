from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request
from urllib.parse import urlparse, urlunparse


DEFAULT_TIMEOUT_SEC = 30.0
DEFAULT_PORT_SCAN_COUNT = 20
LOCAL_SYNC_HOSTS = {"127.0.0.1", "localhost", "::1"}


def normalize_trade_date(trade_date: str) -> str:
    return trade_date.replace("-", "").strip()


def is_enabled(env_var: str) -> bool:
    raw_value = os.getenv(env_var, "1").strip().lower()
    return raw_value not in {"0", "false", "no", "off"}


def resolve_trade_date_url(base_url: str, trade_date: str) -> str:
    return f"{base_url.rstrip('/')}/{normalize_trade_date(trade_date)}"


def resolve_timeout(timeout_sec: float | None, env_var: str, default_timeout: float = DEFAULT_TIMEOUT_SEC) -> float:
    if timeout_sec is not None:
        return timeout_sec
    raw_value = os.getenv(env_var, str(default_timeout)).strip()
    return float(raw_value)


def resolve_port_scan_count(env_var: str, default_count: int = DEFAULT_PORT_SCAN_COUNT) -> int:
    raw_value = os.getenv(env_var, str(default_count)).strip()
    return max(int(raw_value), 1)


def is_local_sync_target(target_url: str) -> bool:
    parsed = urlparse(target_url)
    return parsed.hostname in LOCAL_SYNC_HOSTS and parsed.port is not None


def replace_url_port(target_url: str, port: int) -> str:
    parsed = urlparse(target_url)
    hostname = parsed.hostname or ""
    netloc = hostname
    if ":" in hostname and not hostname.startswith("["):
        netloc = f"[{hostname}]"
    if parsed.username:
        credentials = parsed.username
        if parsed.password:
            credentials += f":{parsed.password}"
        netloc = f"{credentials}@{netloc}"
    netloc = f"{netloc}:{port}"
    return urlunparse(parsed._replace(netloc=netloc))


def iter_candidate_urls(target_url: str, port_scan_count: int) -> list[str]:
    candidate_urls = [target_url]
    if not is_local_sync_target(target_url):
        return candidate_urls

    parsed = urlparse(target_url)
    start_port = parsed.port
    if start_port is None:
        return candidate_urls

    for port_offset in range(1, port_scan_count):
        candidate_urls.append(replace_url_port(target_url, start_port + port_offset))
    return candidate_urls


def read_http_error_body(exc: error.HTTPError) -> str:
    return exc.read().decode("utf-8", errors="replace")


def post_sync_request(target_url: str, timeout: float) -> dict[str, Any]:
    http_request = request.Request(target_url, method="POST")
    with request.urlopen(http_request, timeout=timeout) as response:
        response_body = response.read().decode("utf-8").strip()

    if not response_body:
        return {"status": "success"}

    try:
        return json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"sync returned invalid JSON from url={target_url}: {response_body}") from exc


def run_trade_date_post(
    trade_date: str,
    *,
    operation_name: str,
    default_sync_url: str,
    enabled_env_var: str,
    url_env_var: str,
    timeout_env_var: str,
    port_scan_count_env_var: str,
    sync_url: str | None = None,
    timeout_sec: float | None = None,
) -> dict[str, Any]:
    normalized_trade_date = normalize_trade_date(trade_date)
    if not normalized_trade_date:
        raise ValueError(f"trade_date is required for {operation_name}")

    if not is_enabled(enabled_env_var):
        return {"status": "skipped", "reason": "disabled", "trade_date": normalized_trade_date}

    base_url = sync_url or os.getenv(url_env_var, default_sync_url)
    primary_url = resolve_trade_date_url(base_url, normalized_trade_date)
    timeout = resolve_timeout(timeout_sec, timeout_env_var)
    candidate_urls = iter_candidate_urls(primary_url, resolve_port_scan_count(port_scan_count_env_var))
    failures: list[str] = []

    for target_url in candidate_urls:
        try:
            result = post_sync_request(target_url, timeout)
            result.setdefault("trade_date", normalized_trade_date)
            result.setdefault("sync_url", target_url)
            return result
        except error.HTTPError as exc:
            response_body = read_http_error_body(exc)
            failure_message = f"status={exc.code} url={target_url} body={response_body}"
            if exc.code == 404 and is_local_sync_target(target_url):
                failures.append(failure_message)
                continue
            raise RuntimeError(f"{operation_name} failed with {failure_message}") from exc
        except error.URLError as exc:
            failure_message = f"url={target_url} reason={exc.reason}"
            if is_local_sync_target(target_url):
                failures.append(failure_message)
                continue
            raise RuntimeError(f"{operation_name} failed for {failure_message}") from exc

    attempted_summary = " | ".join(failures)
    raise RuntimeError(
        f"{operation_name} failed after scanning local ports: "
        f"trade_date={normalized_trade_date}; attempts={attempted_summary}"
    )
