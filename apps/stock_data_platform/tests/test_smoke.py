import io
import os
import sys
from importlib import import_module
from contextlib import redirect_stdout

from apps.stock_data_platform.main import main as app_main


def test_root_compatibility_imports():
    import DataFetch
    import common.config
    from DataFetch import StockBasicFetch

    assert hasattr(DataFetch, "StockBasicFetch")
    assert StockBasicFetch is not None
    assert hasattr(common.config, "TOKEN")


def test_main_without_token_prints_help(monkeypatch):
    monkeypatch.delenv("TUSHARE_TOKEN", raising=False)
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        app_main()
    assert "TUSHARE_TOKEN is not set" in stdout.getvalue()


def test_requirements_wrapper_points_to_app():
    with open("requirements.txt", "r", encoding="utf-8") as file_obj:
        content = file_obj.read().strip()
    assert content == "-r apps/stock_data_platform/requirements.txt"


def test_importing_app_main_does_not_mutate_sys_path(monkeypatch):
    repo_root = os.getcwd()
    original_path = [entry for entry in sys.path if entry != repo_root]
    monkeypatch.setattr(sys, "path", original_path[:])
    sys.modules.pop("apps.stock_data_platform.main", None)

    import_module("apps.stock_data_platform.main")

    assert repo_root not in sys.path
