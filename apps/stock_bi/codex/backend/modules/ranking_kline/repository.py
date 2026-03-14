from sqlalchemy import text


class RankingKlineRepository:
    def __init__(self, engine):
        self.engine = engine

    def load_kline_rows(self, ts_code: str, limit: int):
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT ts_code, trade_date, open, high, low, close, pct_chg, vol, amount
                    FROM daily_kline
                    WHERE ts_code = :ts_code
                    ORDER BY trade_date DESC
                    LIMIT :limit
                    """
                ),
                {"ts_code": ts_code, "limit": limit},
            ).fetchall()
        return list(rows)

    def load_search_rows(self, keyword: str, limit: int):
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT ts_code, name
                    FROM stock_basic
                    WHERE ts_code LIKE :keyword OR name LIKE :keyword
                    ORDER BY ts_code
                    LIMIT :limit
                    """
                ),
                {"keyword": f"%{keyword}%", "limit": limit},
            ).fetchall()
        return list(rows)

    def load_fallback_search_rows(self, keyword: str, limit: int):
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT DISTINCT ts_code, ts_code as name
                    FROM daily_kline
                    WHERE ts_code LIKE :keyword
                    LIMIT :limit
                    """
                ),
                {"keyword": f"%{keyword}%", "limit": limit},
            ).fetchall()
        return list(rows)

    def load_ranking_enhanced_rows(
        self,
        trade_date: str,
        sort_by: str,
        order: str,
        market,
        industry,
        top: int,
    ):
        order_by_map = {
            "pct_chg": "k.pct_chg",
            "amount": "k.amount",
            "turnover": "db.turnover_rate",
        }
        order_col = order_by_map.get(sort_by, "k.pct_chg")
        order_dir = "DESC" if order == "desc" else "ASC"
        market_conditions = {
            "科创板": "k.ts_code LIKE '68%'",
            "创业板": "k.ts_code LIKE '30%'",
            "沪市主板": "k.ts_code LIKE '60%' AND k.ts_code NOT LIKE '68%'",
            "深市主板": "k.ts_code LIKE '00%'",
            "北交所": "(k.ts_code LIKE '4%' OR k.ts_code LIKE '8%')",
        }
        where_clauses = ["k.trade_date = :trade_date"]
        if market and market in market_conditions:
            where_clauses.append(market_conditions[market])
        if industry:
            where_clauses.append("b.industry = :industry")
        where_sql = " AND ".join(where_clauses)
        params = {"trade_date": trade_date, "limit": top}
        if industry:
            params["industry"] = industry

        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    f"""
                    SELECT k.ts_code, b.name, k.pct_chg, k.close, k.amount / 10000 as amount_wan,
                           k.vol, db.turnover_rate, b.industry, db.pe, db.pb
                    FROM daily_kline k
                    LEFT JOIN stock_basic b ON k.ts_code = b.ts_code
                    LEFT JOIN daily_basic db ON k.ts_code = db.ts_code AND k.trade_date = db.trade_date
                    WHERE {where_sql}
                    ORDER BY {order_col} {order_dir}
                    LIMIT :limit
                    """
                ),
                params,
            ).fetchall()
        return list(rows)

    def load_industry_stocks_rows(self, industry: str, trade_date: str, order: str, limit: int):
        order_dir = "DESC" if order == "desc" else "ASC"
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    f"""
                    SELECT
                        k.ts_code, b.name, k.pct_chg, k.close, k.open, k.high, k.low,
                        k.vol / 10000 as vol_wan, k.amount / 10000 as amount_wan,
                        db.turnover_rate, db.pe, db.pb, db.total_mv / 10000 as total_mv_yi
                    FROM daily_kline k
                    JOIN stock_basic b ON k.ts_code = b.ts_code
                    LEFT JOIN daily_basic db ON k.ts_code = db.ts_code AND k.trade_date = db.trade_date
                    WHERE k.trade_date = :trade_date
                      AND b.industry = :industry
                    ORDER BY k.pct_chg """
                    + order_dir
                    + """
                    LIMIT :limit
                    """
                ),
                {"trade_date": trade_date, "industry": industry, "limit": limit},
            ).fetchall()
        return list(rows)

    def load_moneyflow_row(self, ts_code: str, trade_date: str):
        with self.engine.connect() as conn:
            return conn.execute(
                text(
                    """
                    SELECT ts_code, trade_date,
                           buy_sm_vol, buy_sm_amount, sell_sm_vol, sell_sm_amount,
                           buy_md_vol, buy_md_amount, sell_md_vol, sell_md_amount,
                           buy_lg_vol, buy_lg_amount, sell_lg_vol, sell_lg_amount,
                           buy_elg_vol, buy_elg_amount, sell_elg_vol, sell_elg_amount,
                           net_mf_vol, net_mf_amount
                    FROM moneyflow
                    WHERE ts_code = :ts_code AND trade_date = :trade_date
                    """
                ),
                {"ts_code": ts_code, "trade_date": trade_date},
            ).fetchone()
