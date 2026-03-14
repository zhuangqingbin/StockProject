from decimal import Decimal
from typing import Any, Iterable, List, Optional

from ..market_summary.application import format_date


def to_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def select_ranking_rows(summary: dict, sort_by: str, order: str) -> List[dict]:
    if sort_by == "amount":
        return list(summary.get("top_amount", []))
    if sort_by == "turnover":
        return list(summary.get("top_turnover", []))
    if order == "asc":
        return list(summary.get("top_losers", []))
    return list(summary.get("top_gainers", []))


def filter_market_rows(rows: Iterable[dict], market: Optional[str]) -> List[dict]:
    data = list(rows)
    if not market:
        return data

    market_filters = {
        "科创板": lambda row: row["ts_code"].startswith("68"),
        "创业板": lambda row: row["ts_code"].startswith("30"),
        "沪市主板": lambda row: row["ts_code"].startswith("60") and not row["ts_code"].startswith("68"),
        "深市主板": lambda row: row["ts_code"].startswith("00"),
        "北交所": lambda row: row["ts_code"].startswith("4") or row["ts_code"].startswith("8"),
    }
    predicate = market_filters.get(market)
    if predicate is None:
        return data
    return [row for row in data if predicate(row)]


def build_kline_rows(rows: Iterable[tuple]) -> List[dict]:
    return [
        {
            "ts_code": row[0],
            "date": format_date(row[1]),
            "open": to_float(row[2]),
            "high": to_float(row[3]),
            "low": to_float(row[4]),
            "close": to_float(row[5]),
            "pct_chg": to_float(row[6]),
            "vol": to_float(row[7]),
            "amount": to_float(row[8]),
        }
        for row in reversed(list(rows))
    ]


def build_search_results(rows: Iterable[tuple]) -> List[dict]:
    return [{"ts_code": row[0], "name": row[1] or row[0]} for row in rows]


def build_ranking_enhanced_payload(
    trade_date: str,
    rows: Iterable[tuple],
    sort_by: str,
    order: str,
    market: Optional[str],
    industry: Optional[str],
) -> dict:
    stocks = [
        {
            "ts_code": row[0],
            "name": row[1] or row[0][:6],
            "pct_chg": round(to_float(row[2]), 2),
            "close": round(to_float(row[3]), 2),
            "amount": round(to_float(row[4]), 2),
            "vol": round(to_float(row[5]) / 10000, 2),
            "turnover_rate": round(to_float(row[6]), 2),
            "industry": row[7],
            "pe": round(to_float(row[8]), 2) if row[8] else None,
            "pb": round(to_float(row[9]), 2) if row[9] else None,
        }
        for row in rows
    ]

    return {
        "trade_date": format_date(trade_date),
        "sort_by": sort_by,
        "order": order,
        "market": market,
        "industry": industry,
        "stocks": stocks,
    }


def build_industry_stocks_payload(trade_date: str, industry: str, order: str, rows: Iterable[tuple]) -> dict:
    stocks = [
        {
            "ts_code": row[0],
            "name": row[1] or row[0][:6],
            "pct_chg": round(to_float(row[2]), 2),
            "close": round(to_float(row[3]), 2),
            "open": round(to_float(row[4]), 2),
            "high": round(to_float(row[5]), 2),
            "low": round(to_float(row[6]), 2),
            "vol": round(to_float(row[7]), 2),
            "amount": round(to_float(row[8]), 2),
            "turnover_rate": round(to_float(row[9]), 2) if row[9] else None,
            "pe": round(to_float(row[10]), 2) if row[10] else None,
            "pb": round(to_float(row[11]), 2) if row[11] else None,
            "total_mv": round(to_float(row[12]), 2) if row[12] else None,
        }
        for row in rows
    ]

    up_count = sum(1 for stock in stocks if stock["pct_chg"] > 0)
    down_count = sum(1 for stock in stocks if stock["pct_chg"] < 0)
    flat_count = len(stocks) - up_count - down_count

    return {
        "trade_date": format_date(trade_date),
        "industry": industry,
        "order": order,
        "total": len(stocks),
        "up_count": up_count,
        "down_count": down_count,
        "flat_count": flat_count,
        "stocks": stocks,
    }


def build_moneyflow_payload(ts_code: str, trade_date: str, row: Optional[tuple]) -> dict:
    if not row:
        return {"ts_code": ts_code, "trade_date": format_date(trade_date), "message": "无资金流向数据"}

    return {
        "ts_code": row[0],
        "trade_date": format_date(row[1]),
        "small": {
            "buy_vol": to_float(row[2]),
            "buy_amount": to_float(row[3]),
            "sell_vol": to_float(row[4]),
            "sell_amount": to_float(row[5]),
            "net_amount": to_float(row[3]) - to_float(row[5]),
        },
        "medium": {
            "buy_vol": to_float(row[6]),
            "buy_amount": to_float(row[7]),
            "sell_vol": to_float(row[8]),
            "sell_amount": to_float(row[9]),
            "net_amount": to_float(row[7]) - to_float(row[9]),
        },
        "large": {
            "buy_vol": to_float(row[10]),
            "buy_amount": to_float(row[11]),
            "sell_vol": to_float(row[12]),
            "sell_amount": to_float(row[13]),
            "net_amount": to_float(row[11]) - to_float(row[13]),
        },
        "extra_large": {
            "buy_vol": to_float(row[14]),
            "buy_amount": to_float(row[15]),
            "sell_vol": to_float(row[16]),
            "sell_amount": to_float(row[17]),
            "net_amount": to_float(row[15]) - to_float(row[17]),
        },
        "net_mf_vol": to_float(row[18]),
        "net_mf_amount": to_float(row[19]),
    }
