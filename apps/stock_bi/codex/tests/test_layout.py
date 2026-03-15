from pathlib import Path


def test_stock_bi_has_local_readme():
    readme = Path("apps/stock_bi/README.md")

    assert readme.exists()
    content = readme.read_text(encoding="utf-8")
    assert "stock_bi" in content
    assert "run.sh" in content
    assert "backend/" in content
    assert "frontend/" in content


def test_stock_bi_drops_legacy_backend_shims():
    for path in (
        "apps/stock_bi/codex/backend/cache.py",
        "apps/stock_bi/codex/backend/config.py",
        "apps/stock_bi/codex/backend/database.py",
        "apps/stock_bi/codex/backend/services",
        "apps/stock_bi/codex/add_indexes.sql",
    ):
        assert not Path(path).exists()


def test_stock_bi_routers_do_not_import_removed_shims():
    router_dir = Path("apps/stock_bi/codex/backend/routers")

    for file_name in ("chat.py", "market.py", "websocket.py"):
        content = (router_dir / file_name).read_text(encoding="utf-8")
        assert "from ..cache import" not in content
        assert "from ..database import" not in content
