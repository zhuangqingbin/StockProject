from __future__ import annotations

import io
from urllib import error

import pytest

from apps.stock_data_platform.jobs import stock_bi_sync
from apps.stock_data_platform.jobs import trade_date_http_sync


class _FakeResponse:
    def __init__(self, body: str):
        self._body = body.encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_sync_stock_bi_scans_next_local_port_after_404(monkeypatch):
    attempted_urls: list[str] = []

    def fake_urlopen(http_request, timeout):
        attempted_urls.append(http_request.full_url)
        if http_request.full_url.endswith(":8000/api/market/sync-update/20260209"):
            raise error.HTTPError(
                http_request.full_url,
                404,
                "Not Found",
                hdrs=None,
                fp=io.BytesIO(b'{"detail":"Not Found"}'),
            )
        if http_request.full_url.endswith(":8001/api/market/sync-update/20260209"):
            return _FakeResponse('{"status":"success","trade_date":"20260209"}')
        raise AssertionError(f"Unexpected URL: {http_request.full_url}")

    monkeypatch.setenv("STOCK_BI_SYNC_PORT_SCAN_COUNT", "3")
    monkeypatch.setattr(trade_date_http_sync.request, "urlopen", fake_urlopen)

    result = stock_bi_sync.sync_stock_bi("2026-02-09", timeout_sec=1)

    assert result == {
        "status": "success",
        "trade_date": "20260209",
        "sync_url": "http://127.0.0.1:8001/api/market/sync-update/20260209",
    }
    assert attempted_urls == [
        "http://127.0.0.1:8000/api/market/sync-update/20260209",
        "http://127.0.0.1:8001/api/market/sync-update/20260209",
    ]


def test_sync_stock_bi_does_not_hide_non_404_http_errors(monkeypatch):
    attempted_urls: list[str] = []

    def fake_urlopen(http_request, timeout):
        attempted_urls.append(http_request.full_url)
        raise error.HTTPError(
            http_request.full_url,
            500,
            "Server Error",
            hdrs=None,
            fp=io.BytesIO(b'{"detail":"boom"}'),
        )

    monkeypatch.setenv("STOCK_BI_SYNC_PORT_SCAN_COUNT", "3")
    monkeypatch.setattr(trade_date_http_sync.request, "urlopen", fake_urlopen)

    with pytest.raises(RuntimeError, match="status=500"):
        stock_bi_sync.sync_stock_bi("2026-02-09", timeout_sec=1)

    assert attempted_urls == [
        "http://127.0.0.1:8000/api/market/sync-update/20260209",
    ]


def test_sync_stock_bi_defaults_to_scanning_20_ports(monkeypatch):
    monkeypatch.delenv("STOCK_BI_SYNC_PORT_SCAN_COUNT", raising=False)

    assert stock_bi_sync._resolve_port_scan_count() == 20
