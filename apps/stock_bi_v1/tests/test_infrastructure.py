import importlib
import time


def test_settings_build_database_url_from_shared_env(monkeypatch):
    monkeypatch.setenv("MYSQL_USER", "stock_user")
    monkeypatch.setenv("MYSQL_PASSWORD", "secret")
    monkeypatch.setenv("MYSQL_HOST", "127.0.0.1")
    monkeypatch.setenv("MYSQL_PORT", "3307")
    monkeypatch.setenv("MYSQL_DATABASE", "stock_database")
    monkeypatch.setenv("STOCK_BI_V1_API_PORT", "8100")

    settings = importlib.import_module("apps.stock_bi_v1.backend.infrastructure.settings")
    settings = importlib.reload(settings)

    assert settings.DATABASE_URL.startswith("mysql+pymysql://stock_user:secret@127.0.0.1:3307/")
    assert settings.API_HOST == "0.0.0.0"
    assert settings.API_PORT == 8100
    assert settings.CACHE_TTL_OVERVIEW == 300


def test_cached_reuses_result_for_same_args():
    cache_module = importlib.import_module("apps.stock_bi_v1.backend.infrastructure.cache")
    cache_module = importlib.reload(cache_module)

    calls = {"count": 0}

    @cache_module.cached(ttl=10)
    def build_value(symbol: str, days: int = 30) -> str:
        calls["count"] += 1
        return f"{symbol}:{days}:{calls['count']}"

    assert build_value("000001.SZ", days=30) == "000001.SZ:30:1"
    assert build_value("000001.SZ", days=30) == "000001.SZ:30:1"
    assert build_value("000001.SZ", days=5) == "000001.SZ:5:2"
    assert calls["count"] == 2


def test_clear_all_caches_and_ttl_expiry():
    cache_module = importlib.import_module("apps.stock_bi_v1.backend.infrastructure.cache")
    cache_module = importlib.reload(cache_module)

    calls = {"count": 0}

    @cache_module.cached(ttl=1)
    def load_snapshot() -> int:
        calls["count"] += 1
        return calls["count"]

    assert load_snapshot() == 1
    cache_module.clear_all_caches()
    assert load_snapshot() == 2

    time.sleep(1.1)
    assert load_snapshot() == 3
