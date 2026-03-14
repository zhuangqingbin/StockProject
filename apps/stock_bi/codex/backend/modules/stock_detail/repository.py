from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy import text


@dataclass(frozen=True)
class StockDetailRows:
    daily_row: Optional[tuple]
    basic_row: Optional[tuple]
    kline_rows: List[tuple]
    company_row: Optional[tuple]


@dataclass(frozen=True)
class CompanyInfoRows:
    base_row: Optional[tuple]
    detail_row: Optional[tuple]


@dataclass(frozen=True)
class IndustryDetailRows:
    index_row: Optional[tuple]
    sw_kline_rows: List[tuple]
    sw_today_row: Optional[tuple]
    aggregate_kline_rows: List[tuple]
    stats_row: Optional[tuple]


class StockDetailRepository:
    def __init__(self, engine):
        self.engine = engine

    def load_stock_detail_rows(self, ts_code: str, trade_date: str) -> StockDetailRows:
        with self.engine.connect() as conn:
            daily_row = conn.execute(
                text(
                    """
                    SELECT k.ts_code, k.trade_date, k.open, k.high, k.low, k.close,
                           k.pre_close, k.pct_chg, k.vol, k.amount, b.name
                    FROM daily_kline k
                    LEFT JOIN stock_basic b ON k.ts_code = b.ts_code
                    WHERE k.ts_code = :ts_code AND k.trade_date = :trade_date
                    """
                ),
                {"ts_code": ts_code, "trade_date": trade_date},
            ).fetchone()
            basic_row = conn.execute(
                text(
                    """
                    SELECT ts_code, trade_date, turnover_rate, pe, pe_ttm, pb,
                           total_mv, circ_mv, volume_ratio
                    FROM daily_basic
                    WHERE ts_code = :ts_code AND trade_date = :trade_date
                    """
                ),
                {"ts_code": ts_code, "trade_date": trade_date},
            ).fetchone()
            kline_rows = conn.execute(
                text(
                    """
                    SELECT trade_date, open, high, low, close, vol, amount, pct_chg
                    FROM daily_kline
                    WHERE ts_code = :ts_code
                    ORDER BY trade_date DESC
                    LIMIT 60
                    """
                ),
                {"ts_code": ts_code},
            ).fetchall()
            company_row = conn.execute(
                text(
                    """
                    SELECT ts_code, name, area, industry, market, list_date
                    FROM stock_basic
                    WHERE ts_code = :ts_code
                    """
                ),
                {"ts_code": ts_code},
            ).fetchone()

        return StockDetailRows(
            daily_row=daily_row,
            basic_row=basic_row,
            kline_rows=list(kline_rows),
            company_row=company_row,
        )

    def load_company_info_rows(self, ts_code: str) -> CompanyInfoRows:
        with self.engine.connect() as conn:
            base_row = conn.execute(
                text(
                    """
                    SELECT ts_code, symbol, name, area, industry, market, exchange, list_date
                    FROM stock_basic
                    WHERE ts_code = :ts_code
                    """
                ),
                {"ts_code": ts_code},
            ).fetchone()
            detail_row = None
            if base_row:
                detail_row = conn.execute(
                    text(
                        """
                        SELECT chairman, manager, secretary, reg_capital, province, city,
                               introduction, website, employees, main_business
                        FROM stock_company
                        WHERE ts_code = :ts_code
                        """
                    ),
                    {"ts_code": ts_code},
                ).fetchone()

        return CompanyInfoRows(base_row=base_row, detail_row=detail_row)

    def load_industry_detail_rows(self, industry: str, trade_date: str, kline_limit: int) -> IndustryDetailRows:
        with self.engine.connect() as conn:
            index_row = None
            sw_kline_rows: List[tuple] = []
            sw_today_row = None

            try:
                index_row = conn.execute(
                    text(
                        """
                        SELECT DISTINCT ts_code, name FROM index_sw_daily
                        WHERE name LIKE :pattern1
                           OR name LIKE :pattern2
                           OR name = :exact
                        ORDER BY trade_date DESC LIMIT 1
                        """
                    ),
                    {
                        "pattern1": f"{industry}%",
                        "pattern2": f"%{industry}%",
                        "exact": industry,
                    },
                ).fetchone()

                if index_row:
                    sw_kline_rows = list(
                        conn.execute(
                            text(
                                """
                                SELECT trade_date, open, high, low, close, vol, amount, pct_change
                                FROM index_sw_daily
                                WHERE ts_code = :ts_code
                                ORDER BY trade_date DESC
                                LIMIT :limit
                                """
                            ),
                            {"ts_code": index_row[0], "limit": kline_limit},
                        ).fetchall()
                    )
                    if sw_kline_rows:
                        sw_today_row = conn.execute(
                            text(
                                """
                                SELECT open, high, low, close, pct_change, vol, amount, pe, pb
                                FROM index_sw_daily
                                WHERE ts_code = :ts_code AND trade_date = :trade_date
                                """
                            ),
                            {"ts_code": index_row[0], "trade_date": trade_date},
                        ).fetchone()
            except Exception:
                index_row = None
                sw_kline_rows = []
                sw_today_row = None

            aggregate_kline_rows: List[tuple] = []
            if not sw_kline_rows:
                try:
                    aggregate_kline_rows = list(
                        conn.execute(
                            text(
                                """
                                SELECT
                                    k.trade_date,
                                    AVG(k.open) as avg_open,
                                    MAX(k.high) as max_high,
                                    MIN(k.low) as min_low,
                                    AVG(k.close) as avg_close,
                                    SUM(k.vol) as total_vol,
                                    SUM(k.amount) as total_amount,
                                    AVG(k.pct_chg) as avg_pct_chg
                                FROM daily_kline k
                                JOIN stock_basic b ON k.ts_code = b.ts_code
                                WHERE b.industry = :industry
                                GROUP BY k.trade_date
                                ORDER BY k.trade_date DESC
                                LIMIT :limit
                                """
                            ),
                            {"industry": industry, "limit": kline_limit},
                        ).fetchall()
                    )
                except Exception:
                    aggregate_kline_rows = []

            stats_row = conn.execute(
                text(
                    """
                    SELECT
                        COUNT(*) as stock_count,
                        SUM(CASE WHEN k.pct_chg > 0 THEN 1 ELSE 0 END) as up_count,
                        SUM(CASE WHEN k.pct_chg < 0 THEN 1 ELSE 0 END) as down_count,
                        AVG(k.pct_chg) as avg_pct_chg,
                        SUM(k.amount) / 100000000 as total_amount
                    FROM daily_kline k
                    JOIN stock_basic b ON k.ts_code = b.ts_code
                    WHERE k.trade_date = :trade_date AND b.industry = :industry
                    """
                ),
                {"trade_date": trade_date, "industry": industry},
            ).fetchone()

        return IndustryDetailRows(
            index_row=index_row,
            sw_kline_rows=sw_kline_rows,
            sw_today_row=sw_today_row,
            aggregate_kline_rows=aggregate_kline_rows,
            stats_row=stats_row,
        )
