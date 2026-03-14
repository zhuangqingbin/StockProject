from decimal import Decimal
from typing import Any, Dict, Optional


def normalize_trade_date(trade_date: Optional[str], latest_trade_date: Optional[str] = None) -> Optional[str]:
    if trade_date is None:
        return latest_trade_date
    return trade_date.replace("-", "")


def format_date(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str) and len(value) == 8 and value.isdigit():
        return f"{value[:4]}-{value[4:6]}-{value[6:8]}"
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    return str(value)


def _to_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def build_latest_date_payload(latest_trade_date: Optional[str]) -> Dict[str, Optional[str]]:
    if latest_trade_date is None:
        return {"latest_date": None}
    return {"latest_date": format_date(latest_trade_date), "raw_date": latest_trade_date}


def build_summary_payload(
    trade_date: str,
    summary: Dict[str, Any],
    consistency: Dict[str, Any],
) -> Dict[str, Any]:
    payload = dict(summary)
    payload["trade_date_fmt"] = format_date(trade_date)
    payload["data_consistency"] = {
        "consistent": consistency["consistent"],
        "primary_date": consistency["primary_date"],
        "warnings": consistency["warnings"],
    }
    return payload


def build_overview_payload(trade_date: str, summary: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "trade_date": format_date(trade_date),
        "total_stocks": summary.get("total_stocks", 0),
        "up_count": summary.get("up_count", 0),
        "down_count": summary.get("down_count", 0),
        "flat_count": summary.get("flat_count", 0),
        "limit_up": summary.get("limit_up", 0),
        "limit_down": summary.get("limit_down", 0),
        "total_amount": summary.get("total_amount", 0),
        "avg_pct_chg": summary.get("avg_pct_chg", 0),
    }


def build_top_list_summary_payload(trade_date: str, summary: Dict[str, Any]) -> Dict[str, Any]:
    top_list = summary.get("top_list_summary")
    if top_list:
        return {"trade_date": format_date(trade_date), **top_list}
    return {"trade_date": format_date(trade_date), "count": 0}


def build_north_money_payload(trade_date: str, north_money: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if north_money:
        return {"trade_date": format_date(trade_date), **north_money}
    return {"trade_date": format_date(trade_date), "message": "无数据"}


def build_indices_payload(trade_date: str, summary: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "trade_date": format_date(trade_date),
        "indices": summary.get("index_data", []),
    }


def build_industry_ranking_payload(trade_date: str, summary: Dict[str, Any], limit: int) -> Dict[str, Any]:
    ranking = summary.get("industry_ranking", [])
    return {
        "trade_date": format_date(trade_date),
        "industries": ranking[:limit],
    }


def build_industry_flow_payload(trade_date: str, summary: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "trade_date": format_date(trade_date),
        "industries": summary.get("industry_stats", []),
    }


def build_limit_stats_payload(trade_date: str, summary: Dict[str, Any]) -> Dict[str, Any]:
    limit_stats = summary.get("limit_stats")
    if limit_stats:
        return {"trade_date": format_date(trade_date), **limit_stats}
    return {
        "trade_date": format_date(trade_date),
        "limit_up": summary.get("limit_up", 0),
        "limit_down": summary.get("limit_down", 0),
    }


def build_amount_trend_rows(rows: list) -> list:
    return [
        {"trade_date": format_date(row[0]), "total_amount": round(float(row[1] or 0), 2)}
        for row in reversed(list(rows))
    ]


def build_limit_trend_rows(rows: list) -> list:
    return [
        {
            "trade_date": format_date(row[0]),
            "limit_up": int(row[1] or 0),
            "limit_down": int(row[2] or 0),
        }
        for row in reversed(list(rows))
    ]


def build_north_money_trend_rows(rows: list) -> list:
    return [
        {
            "trade_date": format_date(row[0]),
            "north_total": round(_to_float(row[1]), 2),
            "hgt": round(_to_float(row[2]), 2),
            "sgt": round(_to_float(row[3]), 2),
        }
        for row in reversed(list(rows))
    ]


def build_top_list_rows(rows: list) -> list:
    return [
        {
            "ts_code": row[0],
            "name": row[1],
            "pct_chg": round(_to_float(row[2]), 2),
            "buy": round(_to_float(row[3]), 2),
            "sell": round(_to_float(row[4]), 2),
            "net": round(_to_float(row[5]), 2),
            "reason": row[6],
        }
        for row in rows
    ]


def build_sectors_enhanced_payload(trade_date: str, rows: list, top: int, filter_type: str) -> Dict[str, Any]:
    sectors = [
        {
            "sector": row[0],
            "avg_pct_chg": round(float(row[1] or 0), 3),
            "total_amount": round(float(row[2] or 0), 2),
            "stock_count": int(row[3] or 0),
            "up_count": int(row[4] or 0),
            "down_count": int(row[5] or 0),
            "flat_count": int(row[6] or 0),
            "limit_up": int(row[7] or 0),
            "limit_down": int(row[8] or 0),
            "up_ratio": round(int(row[4] or 0) / max(int(row[3] or 1), 1) * 100, 1),
        }
        for row in rows
        if row[0] != "其他"
    ]

    if filter_type == "up":
        sectors = sorted(sectors, key=lambda item: item["avg_pct_chg"], reverse=True)
    elif filter_type == "down":
        sectors = sorted(sectors, key=lambda item: item["avg_pct_chg"])

    return {"trade_date": format_date(trade_date), "sectors": sectors[:top]}


def build_industries_enhanced_payload(trade_date: str, rows: list, order: str) -> Dict[str, Any]:
    industries = [
        {
            "name": row[0],
            "pct_chg": round(float(row[1] or 0), 3),
            "total_amount": round(float(row[2] or 0), 2),
            "stock_count": int(row[3] or 0),
            "up_count": int(row[4] or 0),
            "down_count": int(row[5] or 0),
            "up_ratio": round(int(row[4] or 0) / max(int(row[3] or 1), 1) * 100, 1),
        }
        for row in rows
    ]

    return {"trade_date": format_date(trade_date), "order": order, "industries": industries}
