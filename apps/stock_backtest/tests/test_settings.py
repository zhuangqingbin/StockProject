from pathlib import Path
import tempfile

from fastapi.testclient import TestClient

from apps.stock_backtest.backend.infrastructure.database import reset_database
from apps.stock_backtest.backend.infrastructure.settings import get_settings
from apps.stock_backtest.backend.main import create_app


def test_settings_prefer_database_override(monkeypatch):
    monkeypatch.setenv("STOCK_BACKTEST_DATABASE_URL", "sqlite+pysqlite:///./stock-backtest.db")
    monkeypatch.setenv("STOCK_BACKTEST_MAX_WORKERS", "6")
    monkeypatch.setenv("STOCK_BACKTEST_FRONTEND_DIST", "")

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.database_url == "sqlite+pysqlite:///./stock-backtest.db"
    assert settings.max_workers == 6
    assert settings.frontend_dist is None


def test_create_app_exposes_health_and_json_root_when_no_frontend(monkeypatch):
    monkeypatch.setenv("STOCK_BACKTEST_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("STOCK_BACKTEST_FRONTEND_DIST", "")

    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)

    health = client.get("/health")
    root = client.get("/")

    assert health.status_code == 200
    assert health.json()["status"] == "healthy"
    assert root.status_code == 200
    assert root.json()["name"] == "Stock Backtest Platform"


def test_create_app_serves_index_when_frontend_dist_exists(monkeypatch, tmp_path: Path):
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "index.html").write_text("<html><body>stock-backtest</body></html>", encoding="utf-8")

    monkeypatch.setenv("STOCK_BACKTEST_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("STOCK_BACKTEST_FRONTEND_DIST", str(dist_dir))

    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "stock-backtest" in response.text


def test_create_app_serves_index_for_frontend_routes_when_frontend_dist_exists(monkeypatch, tmp_path: Path):
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "index.html").write_text("<html><body>stock-backtest-shell</body></html>", encoding="utf-8")

    monkeypatch.setenv("STOCK_BACKTEST_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("STOCK_BACKTEST_FRONTEND_DIST", str(dist_dir))

    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)

    response = client.get("/strategies")

    assert response.status_code == 200
    assert "stock-backtest-shell" in response.text


def test_settings_load_stock_backtest_env_from_repo_env_file(monkeypatch):
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.delenv("STOCK_BACKTEST_EXECUTION_MODE", raising=False)
    monkeypatch.delenv("STOCK_BACKTEST_DATABASE_URL", raising=False)

    with tempfile.TemporaryDirectory(dir=repo_root) as temp_dir:
        temp_path = Path(temp_dir)
        (temp_path / ".env.local").write_text(
            "\n".join(
                [
                    "STOCK_BACKTEST_EXECUTION_MODE=inline",
                    "STOCK_BACKTEST_DATABASE_URL=sqlite+pysqlite:///./env-from-file.db",
                ]
            ),
            encoding="utf-8",
        )
        monkeypatch.chdir(temp_path)
        get_settings.cache_clear()

        settings = get_settings()

    assert settings.execution_mode == "inline"
    assert settings.database_url == "sqlite+pysqlite:///./env-from-file.db"


def test_create_app_seeds_default_template_strategies_when_database_is_empty(monkeypatch, tmp_path: Path):
    database_path = tmp_path / "seed-defaults.sqlite3"

    monkeypatch.setenv("STOCK_BACKTEST_DATABASE_URL", f"sqlite+pysqlite:///{database_path}")
    monkeypatch.setenv("STOCK_BACKTEST_FRONTEND_DIST", "")

    get_settings.cache_clear()
    reset_database()
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/api/strategies")

    payload = response.json()
    template_ids = {item["template_id"] for item in payload if item["template_id"]}

    assert response.status_code == 200
    assert {"ma_crossover", "breakout", "mean_reversion", "rsi_rotation", "atr_trend_following"} <= template_ids


def test_create_app_syncs_missing_template_strategies_into_existing_database(monkeypatch, tmp_path: Path):
    database_path = tmp_path / "seed-sync.sqlite3"

    monkeypatch.setenv("STOCK_BACKTEST_DATABASE_URL", f"sqlite+pysqlite:///{database_path}")
    monkeypatch.setenv("STOCK_BACKTEST_FRONTEND_DIST", "")

    get_settings.cache_clear()
    reset_database()

    first_app = create_app()
    with TestClient(first_app):
        pass

    app = create_app()
    with TestClient(app) as client:
        delete_response = client.delete("/api/strategies/1")
        assert delete_response.status_code == 204

    reset_database()
    synced_app = create_app()
    with TestClient(synced_app) as client:
        response = client.get("/api/strategies")

    payload = response.json()
    template_ids = {item["template_id"] for item in payload if item["template_id"]}

    assert {"ma_crossover", "breakout", "mean_reversion", "rsi_rotation", "atr_trend_following"} <= template_ids
