import sys
from pathlib import Path

from fastapi.testclient import TestClient


def create_test_client(monkeypatch, tmp_path: Path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'stock-bi-v1.sqlite3'}"
    monkeypatch.setenv("STOCK_BI_V1_DATABASE_URL", database_url)
    monkeypatch.setenv("STOCK_BI_V1_FRONTEND_DIST", "")

    for module_name in list(sys.modules):
        if module_name.startswith("apps.stock_bi_v1.backend"):
            sys.modules.pop(module_name)

    from apps.stock_bi_v1.backend.models import db_models  # noqa: F401
    from apps.stock_bi_v1.backend.infrastructure.database import SessionLocal, reset_database
    from apps.stock_bi_v1.backend.main import create_app

    reset_database()
    app = create_app()
    return TestClient(app), SessionLocal
