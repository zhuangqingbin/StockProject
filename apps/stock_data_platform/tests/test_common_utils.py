from pathlib import Path

from apps.stock_data_platform import common as common_pkg
from apps.stock_data_platform.common.database_runtime import get_engine
from apps.stock_data_platform.common.market_calendar import get_prev_trade_days, get_trade_cal
from apps.stock_data_platform.common.timing import timer


COMMON_DIR = Path("apps/stock_data_platform/common")


def test_common_directory_contains_only_runtime_modules():
    python_files = {path.name for path in COMMON_DIR.glob("*.py")}

    assert python_files == {
        "__init__.py",
        "config.py",
        "database_runtime.py",
        "market_calendar.py",
        "timing.py",
        "venv_runtime.py",
    }


def test_common_directory_drops_legacy_helpers():
    for filename in (
        "AutoEmail.py",
        "IndustryTop.yaml",
        "backtrader_support.py",
        "code_repository.py",
        "date_formats.py",
        "finance_math.py",
        "pickle_store.py",
        "security_codes.py",
        "utils.py",
    ):
        assert not (COMMON_DIR / filename).exists()


def test_common_package_exports_only_runtime_helpers():
    assert common_pkg.__all__ == [
        "get_engine",
        "get_prev_trade_days",
        "get_trade_cal",
        "timer",
    ]
    assert common_pkg.get_engine is get_engine
    assert common_pkg.get_prev_trade_days is get_prev_trade_days
    assert common_pkg.get_trade_cal is get_trade_cal
    assert common_pkg.timer is timer
