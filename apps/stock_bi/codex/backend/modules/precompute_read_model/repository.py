import json
from typing import Any, Dict, Optional

from sqlalchemy import text


SUMMARY_JSON_FIELDS = (
    "sector_stats",
    "industry_stats",
    "pct_distribution",
    "top_gainers",
    "top_losers",
    "top_amount",
    "top_turnover",
    "north_money",
    "top_list_summary",
    "limit_stats",
    "industry_ranking",
    "index_data",
)

SUMMARY_JSON_FIELD_INDEXES = {
    10: "sector_stats",
    11: "industry_stats",
    12: "pct_distribution",
    13: "top_gainers",
    14: "top_losers",
    15: "top_amount",
    16: "top_turnover",
    17: "north_money",
    18: "top_list_summary",
    19: "limit_stats",
    20: "industry_ranking",
    21: "index_data",
}


def build_summary_cache_key(trade_date: str) -> str:
    return f"summary:{trade_date}"


def decode_json_field(value: Any) -> Any:
    if not value:
        return None
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except Exception:
        return value


def decode_summary_row(row: Any) -> Dict[str, Any]:
    summary = {
        "trade_date": row[0],
        "total_stocks": row[1],
        "up_count": row[2],
        "down_count": row[3],
        "flat_count": row[4],
        "limit_up": row[5],
        "limit_down": row[6],
        "avg_pct_chg": row[7],
        "total_amount": row[8],
        "total_vol": row[9],
    }

    for index, field_name in SUMMARY_JSON_FIELD_INDEXES.items():
        summary[field_name] = decode_json_field(row[index])

    return summary


class MarketSummaryRepository:
    def __init__(self, engine: Any, cache_backend: Any):
        self._engine = engine
        self._cache = cache_backend

    def save(self, summary: Dict[str, Any]) -> None:
        insert_data = dict(summary)
        for field_name in SUMMARY_JSON_FIELDS:
            value = insert_data.get(field_name)
            insert_data[field_name] = json.dumps(value, ensure_ascii=False) if value is not None else None

        sql = text(
            """
            REPLACE INTO market_daily_summary (
                trade_date, total_stocks, up_count, down_count, flat_count,
                limit_up, limit_down, avg_pct_chg, total_amount, total_vol,
                sector_stats, industry_stats, pct_distribution, top_gainers,
                top_losers, top_amount, top_turnover, north_money,
                top_list_summary, limit_stats, industry_ranking, index_data
            ) VALUES (
                :trade_date, :total_stocks, :up_count, :down_count, :flat_count,
                :limit_up, :limit_down, :avg_pct_chg, :total_amount, :total_vol,
                :sector_stats, :industry_stats, :pct_distribution, :top_gainers,
                :top_losers, :top_amount, :top_turnover, :north_money,
                :top_list_summary, :limit_stats, :industry_ranking, :index_data
            )
            """
        )

        with self._engine.connect() as conn:
            conn.execute(sql, insert_data)
            conn.commit()

        self._cache.set(build_summary_cache_key(summary["trade_date"]), summary, ttl=600)

    def load(self, trade_date: str) -> Optional[Dict[str, Any]]:
        cache_key = build_summary_cache_key(trade_date)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        sql = text(
            """
            SELECT trade_date, total_stocks, up_count, down_count, flat_count,
                   limit_up, limit_down, avg_pct_chg, total_amount, total_vol,
                   sector_stats, industry_stats, pct_distribution, top_gainers,
                   top_losers, top_amount, top_turnover, north_money,
                   top_list_summary, limit_stats, industry_ranking, index_data
            FROM market_daily_summary
            WHERE trade_date = :trade_date
            """
        )

        with self._engine.connect() as conn:
            row = conn.execute(sql, {"trade_date": trade_date}).fetchone()

        if not row:
            return None

        summary = decode_summary_row(row)
        self._cache.set(cache_key, summary, ttl=600)
        return summary
