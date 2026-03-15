import io
import os
import sys
import json
from importlib import import_module
from contextlib import redirect_stdout
from pathlib import Path

from apps.stock_data_platform import DataFetch as datafetch_pkg
from apps.stock_data_platform.main import main as app_main
from apps.stock_data_platform.DataFetch.client import TuShareClient


def test_root_compatibility_layer_has_been_removed():
    assert not Path("DataFetch").exists()
    assert not Path("common").exists()
    assert not Path("DataStore").exists()
    assert not Path("main.py").exists()
    assert not Path("demo_test.py").exists()
    assert not Path("requirements.txt").exists()
    assert not Path("scripts").exists()


def test_main_without_token_prints_help(monkeypatch):
    monkeypatch.delenv("TUSHARE_TOKEN", raising=False)
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        app_main()
    assert "TUSHARE_TOKEN is not set" in stdout.getvalue()


def test_pytest_configuration_lives_in_pyproject():
    assert not Path("pytest.ini").exists()

    pyproject = Path("pyproject.toml")
    assert pyproject.exists()
    content = pyproject.read_text(encoding="utf-8")
    assert "[tool.pytest.ini_options]" in content
    assert "apps/stock_data_platform/tests" in content
    assert "apps/stock_bi/codex/tests" in content


def test_importing_app_main_does_not_mutate_sys_path(monkeypatch):
    repo_root = os.getcwd()
    original_path = [entry for entry in sys.path if entry != repo_root]
    monkeypatch.setattr(sys, "path", original_path[:])
    sys.modules.pop("apps.stock_data_platform.main", None)

    import_module("apps.stock_data_platform.main")

    assert repo_root not in sys.path


def test_platform_uses_single_requirements_source():
    assert not Path("requirements2.txt").exists()
    assert not Path("apps/stock_data_platform/requirements2.txt").exists()
    assert not Path("apps/stock_data_platform/requirements.daily.txt").exists()


def test_platform_owns_data_and_script_directories():
    assert not Path("apps/stock_data_platform/DataStore").exists()
    assert Path("apps/stock_data_platform/scripts").exists()


def test_tushare_client_default_cache_dir_uses_app_cache(monkeypatch):
    repo_root = Path(os.getcwd())
    monkeypatch.setattr("apps.stock_data_platform.common.config.TOKEN", "test-token", raising=False)

    client = TuShareClient(pro=object())

    assert Path(client.cache_dir) == repo_root / "apps" / "stock_data_platform" / ".cache" / "tushare"


def test_datafetch_directory_contains_only_maintained_modules():
    datafetch_dir = Path("apps/stock_data_platform/DataFetch")
    python_files = {path.name for path in datafetch_dir.glob("*.py")}

    assert python_files == {
        "__init__.py",
        "BaseClass.py",
        "FetchBasic.py",
        "FetchDaily.py",
        "FetchIndex.py",
        "FetchLimit.py",
        "FetchMoneyFlow.py",
        "FetchTopList.py",
        "client.py",
    }


def test_datafetch_package_exports_only_runtime_fetchers():
    assert datafetch_pkg.__all__ == [
        "BaseDataFetch",
        "TuShareClient",
        "ClientConfig",
        "StockBasicFetch",
        "TradeCalFetch",
        "StockDailyFetch",
        "StockDailyBasicFetch",
        "MoneyFlowFetch",
        "MoneyFlowHSGTFetch",
        "TopListFetch",
        "StkLimitFetch",
        "IndexDailyFetch",
    ]


def test_datafetch_package_drops_legacy_fetchers():
    for name in (
        "HSGTTop10Fetch",
        "TopInstFetch",
        "LimitListFetch",
        "IndexBasicFetch",
        "SWIndexDailyFetch",
        "IndexClassifyFetch",
        "IndexMemberFetch",
        "MAIN_INDEX_CODES",
    ):
        assert not hasattr(datafetch_pkg, name)


def test_stock_data_platform_has_local_readme():
    readme = Path("apps/stock_data_platform/README.md")

    assert readme.exists()
    content = readme.read_text(encoding="utf-8")
    assert "stock_data_platform" in content
    assert "scripts/run_tests.sh" in content
    assert "jobs/daily_jobs.yaml" in content
    assert "install_stock_data_daily_schedule.sh" in content
    assert "STOCK_DATA_DAILY_SCHEDULE_HOUR" in content
    assert "notebooks/10_new_source_probe.ipynb" in content
    assert ".venv-stock-data-arm64" in content
    assert ".venv-stock-data-x86_64" in content
    assert "dispatch_stock_data_python.sh" in content


def test_daily_runner_script_defaults_sync_port_scan_to_20():
    script = Path("apps/stock_data_platform/scripts/run_stock_data_daily.sh")
    content = script.read_text(encoding="utf-8")

    assert "STOCK_BI_SYNC_PORT_SCAN_COUNT=${STOCK_BI_SYNC_PORT_SCAN_COUNT:-20}" in content


def test_daily_runner_script_defaults_stock_bi_v1_precompute_port_scan_to_20():
    script = Path("apps/stock_data_platform/scripts/run_stock_data_daily.sh")
    content = script.read_text(encoding="utf-8")

    assert "STOCK_BI_V1_PRECOMPUTE_PORT_SCAN_COUNT=${STOCK_BI_V1_PRECOMPUTE_PORT_SCAN_COUNT:-20}" in content


def test_stock_data_platform_schedule_scripts_exist():
    assert Path("apps/stock_data_platform/scripts/install_stock_data_daily_schedule.sh").exists()
    assert Path("apps/stock_data_platform/scripts/uninstall_stock_data_daily_schedule.sh").exists()
    assert Path("apps/stock_data_platform/scripts/run_jupyterlab.sh").exists()
    assert Path("apps/stock_data_platform/scripts/dispatch_stock_data_python.sh").exists()


def test_env_example_documents_daily_schedule_variables():
    content = Path(".env.example").read_text(encoding="utf-8")

    assert "STOCK_DATA_DAILY_SCHEDULE_HOUR" in content
    assert "STOCK_DATA_DAILY_SCHEDULE_MINUTE" in content


def test_stock_data_platform_requirements_include_notebook_runtime():
    content = Path("apps/stock_data_platform/requirements.txt").read_text(encoding="utf-8")

    assert "jupyterlab" in content
    assert "ipykernel" in content


def test_stock_data_platform_notebooks_exist():
    notebook_dir = Path("apps/stock_data_platform/notebooks")

    assert notebook_dir.exists()
    assert (notebook_dir / "README.md").exists()
    assert (notebook_dir / "notebook_support.py").exists()
    assert (notebook_dir / "01_job_catalog.ipynb").exists()
    assert (notebook_dir / "02_existing_table_preview.ipynb").exists()
    assert (notebook_dir / "10_new_source_probe.ipynb").exists()


def test_stock_data_platform_notebooks_default_to_project_kernel():
    for notebook_name in (
        "01_job_catalog.ipynb",
        "02_existing_table_preview.ipynb",
        "10_new_source_probe.ipynb",
    ):
        notebook_path = Path("apps/stock_data_platform/notebooks") / notebook_name
        payload = json.loads(notebook_path.read_text(encoding="utf-8"))

        assert payload["metadata"]["kernelspec"]["name"] == "python3"
        assert payload["metadata"]["kernelspec"]["display_name"] == "Python 3"


def test_stock_data_platform_new_source_templates_exist():
    template_dir = Path("apps/stock_data_platform/templates/new_data_source")

    assert template_dir.exists()
    assert (template_dir / "README.md").exists()
    assert (template_dir / "fetcher.py.template").exists()
    assert (template_dir / "daily_job.yaml.template").exists()
    assert (template_dir / "test_fetcher.py.template").exists()


def test_datafetch_source_files_drop_unused_class_definitions():
    for file_name, forbidden_names in {
        "FetchMoneyFlow.py": ("HSGTTop10Fetch",),
        "FetchTopList.py": ("TopInstFetch",),
        "FetchLimit.py": ("LimitListFetch",),
        "FetchIndex.py": (
            "MAIN_INDEX_CODES",
            "IndexBasicFetch",
            "SWIndexDailyFetch",
            "IndexClassifyFetch",
            "IndexMemberFetch",
        ),
    }.items():
        content = (Path("apps/stock_data_platform/DataFetch") / file_name).read_text(
            encoding="utf-8"
        )
        for forbidden_name in forbidden_names:
            assert forbidden_name not in content
