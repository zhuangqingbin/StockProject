from sqlalchemy import text


class MarketSummaryQueryRepository:
    def __init__(self, engine):
        self.engine = engine

    def load_north_money_trend_rows(self, days: int):
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT trade_date, north_money, hgt, sgt
                    FROM moneyflow_hsgt
                    ORDER BY trade_date DESC
                    LIMIT :days
                    """
                ),
                {"days": days},
            ).fetchall()
        return list(rows)

    def load_top_list_rows(self, trade_date: str, limit: int):
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT ts_code, name, pct_change, l_buy / 10000 as buy_wan,
                           l_sell / 10000 as sell_wan, net_amount / 10000 as net_wan, reason
                    FROM top_list
                    WHERE trade_date = :trade_date
                    ORDER BY net_amount DESC
                    LIMIT :limit
                    """
                ),
                {"trade_date": trade_date, "limit": limit},
            ).fetchall()
        return list(rows)

    def load_amount_trend_rows(self, days: int):
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT trade_date, SUM(amount) / 100000000 as total_amount
                    FROM daily_kline
                    GROUP BY trade_date
                    ORDER BY trade_date DESC
                    LIMIT :days
                    """
                ),
                {"days": days},
            ).fetchall()
        return list(rows)

    def load_limit_trend_rows(self, days: int):
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT trade_date,
                           SUM(CASE WHEN pct_chg >= 9.9 THEN 1 ELSE 0 END) as limit_up,
                           SUM(CASE WHEN pct_chg <= -9.9 THEN 1 ELSE 0 END) as limit_down
                    FROM daily_kline
                    GROUP BY trade_date
                    ORDER BY trade_date DESC
                    LIMIT :days
                    """
                ),
                {"days": days},
            ).fetchall()
        return list(rows)

    def load_sectors_enhanced_rows(self, trade_date: str):
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT
                        CASE
                            WHEN ts_code LIKE '68%' THEN '科创板'
                            WHEN ts_code LIKE '60%' THEN '沪市主板'
                            WHEN ts_code LIKE '00%' THEN '深市主板'
                            WHEN ts_code LIKE '30%' THEN '创业板'
                            WHEN ts_code LIKE '4%' OR ts_code LIKE '8%' THEN '北交所'
                            ELSE '其他'
                        END as sector,
                        AVG(pct_chg) as avg_pct_chg,
                        SUM(amount) / 100000000 as total_amount,
                        COUNT(*) as stock_count,
                        SUM(CASE WHEN pct_chg > 0 THEN 1 ELSE 0 END) as up_count,
                        SUM(CASE WHEN pct_chg < 0 THEN 1 ELSE 0 END) as down_count,
                        SUM(CASE WHEN pct_chg = 0 OR pct_chg IS NULL THEN 1 ELSE 0 END) as flat_count,
                        SUM(CASE WHEN pct_chg >= 9.9 THEN 1 ELSE 0 END) as limit_up,
                        SUM(CASE WHEN pct_chg <= -9.9 THEN 1 ELSE 0 END) as limit_down
                    FROM daily_kline
                    WHERE trade_date = :trade_date
                    GROUP BY sector
                    ORDER BY avg_pct_chg DESC
                    """
                ),
                {"trade_date": trade_date},
            ).fetchall()
        return list(rows)

    def load_industries_enhanced_rows(self, trade_date: str, top: int, order: str):
        order_dir = "DESC" if order == "desc" else "ASC"
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT
                        b.industry,
                        AVG(k.pct_chg) as avg_pct_chg,
                        SUM(k.amount) / 100000000 as total_amount,
                        COUNT(*) as stock_count,
                        SUM(CASE WHEN k.pct_chg > 0 THEN 1 ELSE 0 END) as up_count,
                        SUM(CASE WHEN k.pct_chg < 0 THEN 1 ELSE 0 END) as down_count
                    FROM daily_kline k
                    JOIN stock_basic b ON k.ts_code = b.ts_code
                    WHERE k.trade_date = :trade_date
                      AND b.industry IS NOT NULL
                      AND b.industry != ''
                    GROUP BY b.industry
                    ORDER BY avg_pct_chg """
                    + order_dir
                    + """
                    LIMIT :limit
                    """
                ),
                {"trade_date": trade_date, "limit": top},
            ).fetchall()
        return list(rows)
