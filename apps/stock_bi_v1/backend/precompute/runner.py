from __future__ import annotations

from collections import defaultdict

from apps.stock_bi_v1.backend.infrastructure.cache import clear_all_caches
from apps.stock_bi_v1.backend.precompute import repository


def _empty_distribution() -> dict[str, int]:
    return {
        "-10~-7": 0,
        "-7~-5": 0,
        "-5~-3": 0,
        "-3~0": 0,
        "0": 0,
        "0~3": 0,
        "3~5": 0,
        "5~7": 0,
        "7~10": 0,
    }


def _build_distribution(rows: list[dict[str, object]]) -> dict[str, int]:
    distribution = _empty_distribution()
    for row in rows:
        value = float(row["pct_chg"])
        if value <= -7:
            distribution["-10~-7"] += 1
            continue
        if value <= -5:
            distribution["-7~-5"] += 1
            continue
        if value <= -3:
            distribution["-5~-3"] += 1
            continue
        if value < 0:
            distribution["-3~0"] += 1
            continue
        if value == 0:
            distribution["0"] += 1
            continue
        if value < 3:
            distribution["0~3"] += 1
            continue
        if value <= 5:
            distribution["3~5"] += 1
            continue
        if value <= 7:
            distribution["5~7"] += 1
            continue
        distribution["7~10"] += 1
    return distribution


def _rank_market_rows(
    rows: list[dict[str, object]],
    key: str,
    reverse: bool,
    include_turnover: bool = False,
) -> list[dict[str, object]]:
    sorted_rows = sorted(rows, key=lambda row: (float(row[key]), row["ts_code"]), reverse=reverse)
    items: list[dict[str, object]] = []
    for row in sorted_rows[:20]:
        item = {
            "ts_code": row["ts_code"],
            "name": row["name"],
            "pct_chg": float(row["pct_chg"]),
            "close": float(row["close"]),
            "amount": float(row["amount"]),
        }
        if include_turnover:
            item["turnover_rate"] = float(row["turnover_rate"])
        items.append(item)
    return items


def _build_market_payload(rows: list[dict[str, object]]) -> dict[str, object]:
    flat_count = sum(1 for row in rows if float(row["pct_chg"]) == 0)
    return {
        "distribution": _build_distribution(rows),
        "up_limit_count": 0,
        "down_limit_count": 0,
        "flat_count": flat_count,
        "total_amount": round(sum(float(row["amount"]) for row in rows), 2),
        "top_gainers": _rank_market_rows(rows, "pct_chg", reverse=True),
        "top_losers": _rank_market_rows(rows, "pct_chg", reverse=False),
        "top_amount": _rank_market_rows(rows, "amount", reverse=True),
        "top_turnover": _rank_market_rows(rows, "turnover_rate", reverse=True, include_turnover=True),
    }


def _build_industry_payloads(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["industry"])].append(row)

    payloads: list[dict[str, object]] = []
    for industry, industry_rows in grouped.items():
        stock_count = len(industry_rows)
        payloads.append(
            {
                "industry": industry,
                "avg_pct_chg": round(sum(float(row["pct_chg"]) for row in industry_rows) / stock_count, 4),
                "total_amount": round(sum(float(row["amount"]) for row in industry_rows), 2),
                "up_count": sum(1 for row in industry_rows if float(row["pct_chg"]) > 0),
                "down_count": sum(1 for row in industry_rows if float(row["pct_chg"]) < 0),
                "net_mf_amount": round(sum(float(row["net_mf_amount"]) for row in industry_rows), 2),
                "stock_count": stock_count,
            }
        )
    payloads.sort(key=lambda item: (-float(item["avg_pct_chg"]), str(item["industry"])))
    return payloads


def _calculate_consecutive_days(history_rows: list[dict[str, object]]) -> int:
    consecutive_days = 0
    for row in history_rows:
        if not row["is_up_limit"]:
            break
        consecutive_days += 1
    return consecutive_days


def _build_limit_payload(trade_date: str, rows: list[dict[str, object]]) -> dict[str, object]:
    up_limit_rows = [row for row in rows if float(row["close"]) >= float(row["up_limit"])]
    down_limit_rows = [row for row in rows if float(row["close"]) <= float(row["down_limit"])]
    broken_count = sum(1 for row in rows if float(row["high"]) >= float(row["up_limit"]) and float(row["close"]) < float(row["up_limit"]))

    history = repository.get_limit_up_history([str(row["ts_code"]) for row in up_limit_rows], trade_date)
    tier_stats: dict[str, int] = {}
    up_limit_stocks: list[dict[str, object]] = []

    for row in sorted(up_limit_rows, key=lambda item: (-float(item["pct_chg"]), str(item["ts_code"]))):
        consecutive_days = _calculate_consecutive_days(history.get(str(row["ts_code"]), []))
        tier_key = str(consecutive_days or 1)
        tier_stats[tier_key] = tier_stats.get(tier_key, 0) + 1
        up_limit_stocks.append(
            {
                "ts_code": row["ts_code"],
                "name": row["name"],
                "pct_chg": float(row["pct_chg"]),
                "close": float(row["close"]),
                "amount": float(row["amount"]),
                "industry": row["industry"],
                "consecutive_days": consecutive_days,
            }
        )

    down_limit_stocks = [
        {
            "ts_code": row["ts_code"],
            "name": row["name"],
            "pct_chg": float(row["pct_chg"]),
            "close": float(row["close"]),
            "amount": float(row["amount"]),
            "industry": row["industry"],
        }
        for row in sorted(down_limit_rows, key=lambda item: (float(item["pct_chg"]), str(item["ts_code"])))
    ]

    attempt_count = len(up_limit_rows) + broken_count
    return {
        "up_limit_stocks": up_limit_stocks,
        "down_limit_stocks": down_limit_stocks,
        "up_count": len(up_limit_rows),
        "down_count": len(down_limit_rows),
        "broken_count": broken_count,
        "broken_rate": round(broken_count / attempt_count, 4) if attempt_count else 0.0,
        "tier_stats": tier_stats,
    }


def run_precompute(trade_date: str) -> dict[str, object]:
    snapshot_rows = repository.get_equity_snapshot_rows(trade_date)
    if not snapshot_rows:
        clear_all_caches()
        return {"status": "skipped", "trade_date": trade_date, "reason": "no_snapshot_rows"}

    limit_rows = repository.get_limit_snapshot_rows(trade_date)
    market_payload = _build_market_payload(snapshot_rows)
    limit_payload = _build_limit_payload(trade_date, limit_rows)
    market_payload["up_limit_count"] = int(limit_payload["up_count"])
    market_payload["down_limit_count"] = int(limit_payload["down_count"])
    industry_payloads = _build_industry_payloads(snapshot_rows)

    repository.replace_precomputed_rows(trade_date, market_payload, industry_payloads, limit_payload)
    clear_all_caches()
    return {
        "status": "completed",
        "trade_date": trade_date,
        "industry_count": len(industry_payloads),
        "up_limit_count": int(limit_payload["up_count"]),
        "down_limit_count": int(limit_payload["down_count"]),
    }
