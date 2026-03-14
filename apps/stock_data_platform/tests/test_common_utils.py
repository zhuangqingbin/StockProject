import io
from contextlib import redirect_stdout

import pytest

import common as common_compat
from apps.stock_data_platform import common as common_pkg
from apps.stock_data_platform.common.utils import (
    code_add_suffix,
    datetime2str,
    get_n,
    get_pmt,
    get_pv,
    get_rate,
    timer,
)


class FakeDate:
    year = 2025
    month = 3
    day = 14


def test_datetime2str_formats_yyyymmdd():
    assert datetime2str(FakeDate()) == "20250314"


def test_code_add_suffix_keeps_suffix_and_maps_exchange():
    assert code_add_suffix("600000") == "600000.SH"
    assert code_add_suffix("300001") == "300001.SZ"
    assert code_add_suffix(830001) == "830001.BJ"
    assert code_add_suffix("000001.SZ") == "000001.SZ"


def test_code_add_suffix_rejects_unknown_prefix():
    with pytest.raises(ValueError):
        code_add_suffix("100001")


def test_finance_helpers_round_trip_present_value_and_payment():
    pv = get_pv(1000, 0.05, 12)
    pmt = get_pmt(pv, 0.05, 12)

    assert round(pmt, 6) == 1000
    assert round(get_n(pv, pmt, 0.05), 6) == 12
    assert round(get_rate(pv, pmt, 12), 6) == 0.05


def test_timer_prints_elapsed_seconds():
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        with timer("fetch"):
            pass

    output = stdout.getvalue()
    assert "[fetch] done in " in output
    assert output.strip().endswith("s")


def test_common_package_exports_refactored_helpers():
    assert common_pkg.timer is timer
    assert common_pkg.datetime2str is datetime2str
    assert "timer" in common_pkg.__all__
    assert "datetime2str" in common_pkg.__all__


def test_root_common_wrapper_reexports_common_helpers():
    assert common_compat.timer is timer
    assert common_compat.code_add_suffix is code_add_suffix
