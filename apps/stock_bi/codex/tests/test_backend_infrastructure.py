import time

from apps.stock_bi.codex.backend.infrastructure.cache import SimpleCache
from apps.stock_bi.codex.backend.infrastructure.settings import API_HOST, API_PORT, DATABASE_URL, OPENAI_MODEL


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


def test_backend_settings_keep_expected_defaults():
    assert API_HOST == "0.0.0.0"
    assert API_PORT == 8000
    assert OPENAI_MODEL == "gpt-4o-mini"
    assert DATABASE_URL.startswith("mysql+pymysql://")
