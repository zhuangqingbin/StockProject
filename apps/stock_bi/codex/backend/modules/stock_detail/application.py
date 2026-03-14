from typing import Iterable, Optional

from ..market_summary.application import format_date
from ..ranking_kline.application import to_float


def _build_stock_daily_payload(row: Optional[tuple], ts_code: str) -> Optional[dict]:
    if not row:
        return None
    return {
        "ts_code": row[0],
        "trade_date": format_date(row[1]),
        "open": to_float(row[2]),
        "high": to_float(row[3]),
        "low": to_float(row[4]),
        "close": to_float(row[5]),
        "pre_close": to_float(row[6]),
        "pct_chg": to_float(row[7]),
        "vol": to_float(row[8]),
        "amount": to_float(row[9]),
        "name": row[10] or ts_code[:6],
    }


def _build_stock_basic_payload(row: Optional[tuple]) -> Optional[dict]:
    if not row:
        return None
    return {
        "turnover_rate": to_float(row[2]),
        "pe": to_float(row[3]),
        "pe_ttm": to_float(row[4]),
        "pb": to_float(row[5]),
        "total_mv": round(to_float(row[6]) / 10000, 2),
        "circ_mv": round(to_float(row[7]) / 10000, 2),
        "volume_ratio": to_float(row[8]),
    }


def _build_stock_kline_rows(rows: Iterable[tuple]) -> list:
    return [
        {
            "date": format_date(row[0]),
            "open": to_float(row[1]),
            "high": to_float(row[2]),
            "low": to_float(row[3]),
            "close": to_float(row[4]),
            "vol": to_float(row[5]),
            "amount": to_float(row[6]),
            "pct_chg": to_float(row[7]),
        }
        for row in reversed(list(rows))
    ]


def _build_stock_company_payload(row: Optional[tuple]) -> Optional[dict]:
    if not row:
        return None
    return {
        "ts_code": row[0],
        "name": row[1],
        "area": row[2],
        "industry": row[3],
        "market": row[4],
        "list_date": row[5],
    }


def build_stock_detail_payload(
    ts_code: str,
    trade_date: str,
    daily_row: Optional[tuple],
    basic_row: Optional[tuple],
    kline_rows: Iterable[tuple],
    company_row: Optional[tuple],
) -> dict:
    return {
        "ts_code": ts_code,
        "trade_date": format_date(trade_date),
        "daily": _build_stock_daily_payload(daily_row, ts_code),
        "basic": _build_stock_basic_payload(basic_row),
        "kline": _build_stock_kline_rows(kline_rows),
        "company": _build_stock_company_payload(company_row),
    }


def build_company_info_payload(base_row: tuple, detail_row: Optional[tuple]) -> dict:
    result = {
        "ts_code": base_row[0],
        "symbol": base_row[1],
        "name": base_row[2],
        "area": base_row[3],
        "industry": base_row[4],
        "market": base_row[5],
        "exchange": base_row[6],
        "list_date": base_row[7],
    }

    if detail_row:
        result.update(
            {
                "chairman": detail_row[0],
                "manager": detail_row[1],
                "secretary": detail_row[2],
                "reg_capital": to_float(detail_row[3]),
                "province": detail_row[4],
                "city": detail_row[5],
                "introduction": detail_row[6],
                "website": detail_row[7],
                "employees": detail_row[8],
                "main_business": detail_row[9],
            }
        )

    return result


def build_industry_base_payload(industry: str, trade_date: str) -> dict:
    return {
        "industry": industry,
        "trade_date": format_date(trade_date),
        "kline": [],
        "today": None,
        "index_code": None,
    }


def build_sw_industry_kline_rows(rows: Iterable[tuple]) -> list:
    return [
        {
            "date": row[0],
            "open": round(to_float(row[1]), 2),
            "high": round(to_float(row[2]), 2),
            "low": round(to_float(row[3]), 2),
            "close": round(to_float(row[4]), 2),
            "vol": round(to_float(row[5]), 2),
            "amount": round(to_float(row[6]) / 10000, 2),
            "pct_chg": round(to_float(row[7]), 2),
        }
        for row in reversed(list(rows))
    ]


def build_sw_industry_today_payload(row: Optional[tuple]) -> Optional[dict]:
    if not row:
        return None
    return {
        "open": round(to_float(row[0]), 2),
        "high": round(to_float(row[1]), 2),
        "low": round(to_float(row[2]), 2),
        "close": round(to_float(row[3]), 2),
        "pct_chg": round(to_float(row[4]), 2),
        "vol": round(to_float(row[5]), 2),
        "amount": round(to_float(row[6]) / 10000, 2),
        "pe": round(to_float(row[7]), 2) if row[7] else None,
        "pb": round(to_float(row[8]), 2) if row[8] else None,
    }


def build_aggregate_industry_kline_rows(rows: Iterable[tuple]) -> list:
    return [
        {
            "date": row[0],
            "open": round(to_float(row[1]), 2),
            "high": round(to_float(row[2]), 2),
            "low": round(to_float(row[3]), 2),
            "close": round(to_float(row[4]), 2),
            "vol": round(to_float(row[5]) / 10000, 2),
            "amount": round(to_float(row[6]) / 100000000, 2),
            "pct_chg": round(to_float(row[7]), 2),
        }
        for row in reversed(list(rows))
    ]


def build_industry_stats_payload(row: Optional[tuple]) -> Optional[dict]:
    if not row:
        return None
    return {
        "stock_count": int(row[0] or 0),
        "up_count": int(row[1] or 0),
        "down_count": int(row[2] or 0),
        "avg_pct_chg": round(to_float(row[3]), 2),
        "total_amount": round(to_float(row[4]), 2),
    }
