from decimal import Decimal

from apps.stock_bi.codex.backend.modules.precompute_read_model.repository import (
    build_summary_cache_key,
    decode_summary_row,
)
from apps.stock_bi.codex.backend.modules.precompute_read_model.service import convert_decimal


def test_convert_decimal_handles_nested_values():
    payload = {
        "amount": Decimal("1.23"),
        "items": [Decimal("4.56"), {"nested": Decimal("7.89")}],
    }

    converted = convert_decimal(payload)

    assert converted == {"amount": 1.23, "items": [4.56, {"nested": 7.89}]}


def test_build_summary_cache_key_is_stable():
    assert build_summary_cache_key("20250314") == "summary:20250314"


def test_decode_summary_row_parses_json_fields_and_keeps_invalid_json():
    row = (
        "20250314",
        10,
        6,
        4,
        0,
        2,
        1,
        1.23,
        100.0,
        50.0,
        '[{"sector":"科创板"}]',
        None,
        "not-json",
        '[{"ts_code":"000001.SZ"}]',
        None,
        None,
        None,
        '{"north_total": 1.2}',
        None,
        None,
        None,
        None,
    )

    summary = decode_summary_row(row)

    assert summary["trade_date"] == "20250314"
    assert summary["sector_stats"] == [{"sector": "科创板"}]
    assert summary["pct_distribution"] == "not-json"
    assert summary["north_money"] == {"north_total": 1.2}
