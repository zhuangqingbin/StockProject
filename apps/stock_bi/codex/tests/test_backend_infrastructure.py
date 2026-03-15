import time

from apps.stock_bi.codex import runtime_server
from apps.stock_bi.codex.backend.infrastructure.cache import SimpleCache
from apps.stock_bi.codex.backend.infrastructure.settings import API_HOST, API_PORT, DATABASE_URL, OPENAI_MODEL
from apps.stock_bi.codex.runtime_server import build_local_urls, resolve_server_host_port


def test_simple_cache_expires_entries():
    cache = SimpleCache(default_ttl=1)
    cache.set("answer", 42)

    assert cache.get("answer") == 42

    time.sleep(1.1)
    assert cache.get("answer") is None


def test_simple_cache_respects_explicit_ttl():
    cache = SimpleCache(default_ttl=10)
    cache.set("soon", "gone", ttl=1)

    time.sleep(1.1)
    assert cache.get("soon") is None


def test_backend_settings_expose_runtime_configuration():
    assert API_HOST
    assert isinstance(API_PORT, int)
    assert OPENAI_MODEL == "gpt-4o-mini"
    assert DATABASE_URL.startswith("mysql+pymysql://")


def test_runtime_server_uses_default_host_and_port(monkeypatch):
    monkeypatch.delenv("API_HOST", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)

    assert resolve_server_host_port() == ("0.0.0.0", 8000)


def test_runtime_server_uses_env_host_and_port(monkeypatch):
    monkeypatch.setenv("API_HOST", "127.0.0.1")
    monkeypatch.setenv("API_PORT", "8001")

    assert resolve_server_host_port() == ("127.0.0.1", 8001)
    assert build_local_urls(8001) == ("http://localhost:8001", "http://localhost:8001/api/docs")


def test_runtime_server_scans_to_next_port_when_default_port_is_taken(monkeypatch):
    monkeypatch.delenv("API_HOST", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.setenv("API_PORT_SCAN_COUNT", "3")

    availability = {8000: False, 8001: True}
    monkeypatch.setattr(
        runtime_server,
        "_is_port_available",
        lambda host, port: availability.get(port, False),
    )

    assert resolve_server_host_port() == ("0.0.0.0", 8001)
