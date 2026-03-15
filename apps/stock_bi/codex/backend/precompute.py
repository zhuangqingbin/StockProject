"""
市场数据预计算模块
定时计算并存储每日市场聚合数据，提升前端查询性能
"""
import json
from typing import Optional, Dict, Any, List
from sqlalchemy import text

from .infrastructure.database import engine
from .modules.precompute_read_model.service import (
    build_or_load_summary,
    convert_decimal,
    load_summary,
    save_summary,
)


def ensure_summary_table():
    """确保预计算表存在"""
    ddl = """
    CREATE TABLE IF NOT EXISTS market_daily_summary (
        trade_date          VARCHAR(8)   NOT NULL  COMMENT '交易日期(YYYYMMDD)',
        total_stocks        INT                    COMMENT '股票总数',
        up_count            INT                    COMMENT '上涨家数',
        down_count          INT                    COMMENT '下跌家数',
        flat_count          INT                    COMMENT '平盘家数',
        limit_up            INT                    COMMENT '涨停家数',
        limit_down          INT                    COMMENT '跌停家数',
        avg_pct_chg         FLOAT                  COMMENT '平均涨跌幅(%)',
        total_amount        FLOAT                  COMMENT '总成交额(亿元)',
        total_vol           FLOAT                  COMMENT '总成交量(亿手)',
        sector_stats        JSON                   COMMENT '板块统计',
        industry_stats      JSON                   COMMENT '行业统计',
        pct_distribution    JSON                   COMMENT '涨跌幅分布',
        top_gainers         JSON                   COMMENT '涨幅Top20',
        top_losers          JSON                   COMMENT '跌幅Top20',
        top_amount          JSON                   COMMENT '成交额Top20',
        top_turnover        JSON                   COMMENT '换手率Top20',
        north_money         JSON                   COMMENT '北向资金',
        top_list_summary    JSON                   COMMENT '龙虎榜汇总',
        limit_stats         JSON                   COMMENT '涨跌停统计',
        industry_ranking    JSON                   COMMENT '行业排名',
        index_data          JSON                   COMMENT '指数数据',
        created_at          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
        updated_at          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (trade_date),
        INDEX idx_trade_date (trade_date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='每日市场汇总(预计算)';
    """
    with engine.connect() as conn:
        conn.execute(text(ddl))
        conn.commit()
    print("✅ market_daily_summary 表已就绪")


def get_latest_trade_date() -> Optional[str]:
    """获取最新交易日期"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT MAX(trade_date) FROM daily_kline")).scalar()
        if result:
            return str(result)[:8] if len(str(result)) >= 8 else str(result)
    return None


def check_data_consistency() -> Dict[str, Any]:
    """
    检查各数据表的最新日期一致性
    返回各表的最新日期和一致性状态
    """
    # 需要检查的核心表
    tables_to_check = [
        ("daily_kline", "trade_date", "日K线"),
        ("daily_basic", "trade_date", "每日指标"),
        ("moneyflow_hsgt", "trade_date", "北向资金"),
        ("index_daily", "trade_date", "指数数据"),
    ]
    
    result = {
        "consistent": True,
        "primary_date": None,
        "tables": {},
        "warnings": []
    }
    
    with engine.connect() as conn:
        dates = {}
        for table, date_col, name in tables_to_check:
            try:
                sql = text(f"SELECT MAX({date_col}) FROM {table}")
                max_date = conn.execute(sql).scalar()
                if max_date:
                    date_str = str(max_date)[:8] if len(str(max_date)) >= 8 else str(max_date)
                    dates[table] = date_str
                    result["tables"][table] = {"date": date_str, "name": name}
                else:
                    result["tables"][table] = {"date": None, "name": name}
            except Exception as e:
                # 表可能不存在
                result["tables"][table] = {"date": None, "name": name, "error": str(e)}
        
        # 以 daily_kline 为主日期
        if "daily_kline" in dates:
            result["primary_date"] = dates["daily_kline"]
            
            # 检查其他表是否一致
            for table, date in dates.items():
                if table != "daily_kline" and date != result["primary_date"]:
                    result["consistent"] = False
                    table_name = result["tables"][table]["name"]
                    result["warnings"].append(
                        f"{table_name}({table})最新日期为{date}，与主日期{result['primary_date']}不一致"
                    )
    
    return result


def precompute_daily_summary(trade_date: str) -> Dict[str, Any]:
    """
    预计算指定日期的市场汇总数据
    """
    print(f"🔄 正在计算 {trade_date} 的市场汇总...")
    summary = {"trade_date": trade_date}
    
    with engine.connect() as conn:
        # 1. 基础统计（从 daily_kline）
        sql = text("""
            SELECT 
                COUNT(*) as total_stocks,
                SUM(CASE WHEN pct_chg > 0 THEN 1 ELSE 0 END) as up_count,
                SUM(CASE WHEN pct_chg < 0 THEN 1 ELSE 0 END) as down_count,
                SUM(CASE WHEN pct_chg = 0 OR pct_chg IS NULL THEN 1 ELSE 0 END) as flat_count,
                SUM(CASE WHEN pct_chg >= 9.9 THEN 1 ELSE 0 END) as limit_up,
                SUM(CASE WHEN pct_chg <= -9.9 THEN 1 ELSE 0 END) as limit_down,
                AVG(pct_chg) as avg_pct_chg,
                SUM(amount) / 100000000 as total_amount,
                SUM(vol) / 100000000 as total_vol
            FROM daily_kline
            WHERE trade_date = :trade_date
        """)
        row = conn.execute(sql, {"trade_date": trade_date}).fetchone()
        if row:
            summary.update({
                "total_stocks": int(row[0] or 0),
                "up_count": int(row[1] or 0),
                "down_count": int(row[2] or 0),
                "flat_count": int(row[3] or 0),
                "limit_up": int(row[4] or 0),
                "limit_down": int(row[5] or 0),
                "avg_pct_chg": round(float(row[6] or 0), 3),
                "total_amount": round(float(row[7] or 0), 2),
                "total_vol": round(float(row[8] or 0), 2)
            })
        
        # 2. 板块统计（按交易所/市场分）
        sql = text("""
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
                SUM(CASE WHEN pct_chg < 0 THEN 1 ELSE 0 END) as down_count
            FROM daily_kline
            WHERE trade_date = :trade_date
            GROUP BY sector
            ORDER BY avg_pct_chg DESC
        """)
        rows = conn.execute(sql, {"trade_date": trade_date}).fetchall()
        summary["sector_stats"] = [
            {
                "sector": row[0], "avg_pct_chg": round(float(row[1] or 0), 3),
                "total_amount": round(float(row[2] or 0), 2), "stock_count": int(row[3] or 0),
                "up_count": int(row[4] or 0), "down_count": int(row[5] or 0)
            } for row in rows
        ]
        
        # 3. 涨跌幅分布
        sql = text("""
            SELECT 
                FLOOR(pct_chg) as range_start, COUNT(*) as count
            FROM daily_kline
            WHERE trade_date = :trade_date AND pct_chg IS NOT NULL AND pct_chg BETWEEN -11 AND 21
            GROUP BY FLOOR(pct_chg)
            ORDER BY range_start
        """)
        rows = conn.execute(sql, {"trade_date": trade_date}).fetchall()
        summary["pct_distribution"] = [
            {"range_start": int(row[0]), "range_end": int(row[0]) + 1, "count": row[1]}
            for row in rows
        ]
        
        # 4. 涨幅 Top 20
        sql = text("""
            SELECT k.ts_code, b.name, k.pct_chg, k.close, k.amount / 10000 as amount_wan
            FROM daily_kline k
            LEFT JOIN stock_basic b ON k.ts_code = b.ts_code
            WHERE k.trade_date = :trade_date
            ORDER BY k.pct_chg DESC
            LIMIT 20
        """)
        rows = conn.execute(sql, {"trade_date": trade_date}).fetchall()
        summary["top_gainers"] = [
            {"ts_code": row[0], "name": row[1] or row[0][:6], "pct_chg": round(float(row[2] or 0), 2),
             "close": round(float(row[3] or 0), 2), "amount": round(float(row[4] or 0), 2)}
            for row in rows
        ]
        
        # 5. 跌幅 Top 20
        sql = text("""
            SELECT k.ts_code, b.name, k.pct_chg, k.close, k.amount / 10000 as amount_wan
            FROM daily_kline k
            LEFT JOIN stock_basic b ON k.ts_code = b.ts_code
            WHERE k.trade_date = :trade_date
            ORDER BY k.pct_chg ASC
            LIMIT 20
        """)
        rows = conn.execute(sql, {"trade_date": trade_date}).fetchall()
        summary["top_losers"] = [
            {"ts_code": row[0], "name": row[1] or row[0][:6], "pct_chg": round(float(row[2] or 0), 2),
             "close": round(float(row[3] or 0), 2), "amount": round(float(row[4] or 0), 2)}
            for row in rows
        ]
        
        # 6. 成交额 Top 20
        sql = text("""
            SELECT k.ts_code, b.name, k.pct_chg, k.close, k.amount / 10000 as amount_wan
            FROM daily_kline k
            LEFT JOIN stock_basic b ON k.ts_code = b.ts_code
            WHERE k.trade_date = :trade_date
            ORDER BY k.amount DESC
            LIMIT 20
        """)
        rows = conn.execute(sql, {"trade_date": trade_date}).fetchall()
        summary["top_amount"] = [
            {"ts_code": row[0], "name": row[1] or row[0][:6], "pct_chg": round(float(row[2] or 0), 2),
             "close": round(float(row[3] or 0), 2), "amount": round(float(row[4] or 0), 2)}
            for row in rows
        ]
        
        # 7. 换手率 Top 20（从 daily_basic）
        try:
            sql = text("""
                SELECT k.ts_code, b.name, k.pct_chg, k.close, db.turnover_rate
                FROM daily_kline k
                LEFT JOIN stock_basic b ON k.ts_code = b.ts_code
                LEFT JOIN daily_basic db ON k.ts_code = db.ts_code AND k.trade_date = db.trade_date
                WHERE k.trade_date = :trade_date AND db.turnover_rate IS NOT NULL
                ORDER BY db.turnover_rate DESC
                LIMIT 20
            """)
            rows = conn.execute(sql, {"trade_date": trade_date}).fetchall()
            summary["top_turnover"] = [
                {"ts_code": row[0], "name": row[1] or row[0][:6], "pct_chg": round(float(row[2] or 0), 2),
                 "close": round(float(row[3] or 0), 2), "turnover_rate": round(float(row[4] or 0), 2)}
                for row in rows
            ]
        except:
            summary["top_turnover"] = []
        
        # 8. 北向资金（从 moneyflow_hsgt）
        try:
            sql = text("""
                SELECT hgt, sgt, north_money, ggt_ss, ggt_sz, south_money
                FROM moneyflow_hsgt
                WHERE trade_date = :trade_date
            """)
            row = conn.execute(sql, {"trade_date": trade_date}).fetchone()
            if row:
                summary["north_money"] = {
                    "hgt": round(float(row[0] or 0), 2),      # 沪股通
                    "sgt": round(float(row[1] or 0), 2),      # 深股通
                    "north_total": round(float(row[2] or 0), 2),  # 北向合计
                    "ggt_ss": round(float(row[3] or 0), 2),   # 港股通(沪)
                    "ggt_sz": round(float(row[4] or 0), 2),   # 港股通(深)
                    "south_total": round(float(row[5] or 0), 2)   # 南向合计
                }
            else:
                summary["north_money"] = None
        except:
            summary["north_money"] = None
        
        # 9. 龙虎榜汇总（从 top_list）
        try:
            sql = text("""
                SELECT COUNT(*) as total, SUM(l_buy) as total_buy, SUM(l_sell) as total_sell, SUM(net_amount) as total_net
                FROM top_list
                WHERE trade_date = :trade_date
            """)
            row = conn.execute(sql, {"trade_date": trade_date}).fetchone()
            if row and row[0] > 0:
                summary["top_list_summary"] = {
                    "count": int(row[0]),
                    "total_buy": round(float(row[1] or 0) / 10000, 2),   # 万->亿
                    "total_sell": round(float(row[2] or 0) / 10000, 2),
                    "total_net": round(float(row[3] or 0) / 10000, 2)
                }
            else:
                summary["top_list_summary"] = None
        except:
            summary["top_list_summary"] = None
        
        # 10. 涨跌停统计（从 limit_list）
        try:
            sql = text("""
                SELECT 
                    `limit`,
                    COUNT(*) as count
                FROM limit_list
                WHERE trade_date = :trade_date
                GROUP BY `limit`
            """)
            rows = conn.execute(sql, {"trade_date": trade_date}).fetchall()
            limit_stats = {"U": 0, "D": 0, "Z": 0}
            for row in rows:
                if row[0] in limit_stats:
                    limit_stats[row[0]] = row[1]
            summary["limit_stats"] = {
                "limit_up": limit_stats.get("U", 0),
                "limit_down": limit_stats.get("D", 0),
                "zha_ban": limit_stats.get("Z", 0)  # 炸板
            }
        except:
            summary["limit_stats"] = None
        
        # 11. 行业排名（含涨跌个股数 + 近5日平均涨幅，用于 Treemap）
        try:
            # 11.1 获取最近5个交易日
            sql_dates = text("""
                SELECT DISTINCT trade_date FROM daily_kline 
                WHERE trade_date <= :trade_date 
                ORDER BY trade_date DESC LIMIT 5
            """)
            recent_dates = [row[0] for row in conn.execute(sql_dates, {"trade_date": trade_date}).fetchall()]
            
            # 11.2 计算当日行业数据
            sql = text("""
                SELECT 
                    b.industry,
                    AVG(k.pct_chg) as avg_pct_chg,
                    SUM(k.amount) / 100000000 as total_amount,
                    COUNT(*) as stock_count,
                    SUM(CASE WHEN k.pct_chg > 0 THEN 1 ELSE 0 END) as up_count,
                    SUM(CASE WHEN k.pct_chg < 0 THEN 1 ELSE 0 END) as down_count,
                    SUM(CASE WHEN k.pct_chg = 0 OR k.pct_chg IS NULL THEN 1 ELSE 0 END) as flat_count,
                    SUM(CASE WHEN k.pct_chg >= 9.9 THEN 1 ELSE 0 END) as limit_up,
                    SUM(CASE WHEN k.pct_chg <= -9.9 THEN 1 ELSE 0 END) as limit_down
                FROM daily_kline k
                JOIN stock_basic b ON k.ts_code = b.ts_code
                WHERE k.trade_date = :trade_date
                  AND b.industry IS NOT NULL 
                  AND b.industry != ''
                GROUP BY b.industry
            """)
            rows = conn.execute(sql, {"trade_date": trade_date}).fetchall()
            today_data = {row[0]: row for row in rows}
            
            # 11.3 计算近5日平均涨幅
            avg5_data = {}
            if recent_dates:
                sql_avg5 = text("""
                    SELECT 
                        b.industry,
                        AVG(k.pct_chg) as avg5_pct_chg
                    FROM daily_kline k
                    JOIN stock_basic b ON k.ts_code = b.ts_code
                    WHERE k.trade_date IN :dates
                      AND b.industry IS NOT NULL 
                      AND b.industry != ''
                    GROUP BY b.industry
                """)
                rows_avg5 = conn.execute(sql_avg5, {"dates": tuple(recent_dates)}).fetchall()
                avg5_data = {row[0]: float(row[1] or 0) for row in rows_avg5}
            
            # 11.4 合并数据
            summary["industry_ranking"] = []
            for industry, row in today_data.items():
                avg5 = avg5_data.get(industry, 0)
                summary["industry_ranking"].append({
                    "name": industry,
                    "pct_chg": round(float(row[1] or 0), 3),
                    "avg5_pct_chg": round(avg5, 3),  # 近5日平均涨幅
                    "amount": round(float(row[2] or 0), 2),
                    "stock_count": int(row[3] or 0),
                    "up_count": int(row[4] or 0),
                    "down_count": int(row[5] or 0),
                    "flat_count": int(row[6] or 0),
                    "limit_up": int(row[7] or 0),
                    "limit_down": int(row[8] or 0),
                    "up_ratio": round(int(row[4] or 0) / max(int(row[3] or 1), 1) * 100, 1)
                })
            
            # 按当日涨幅排序
            summary["industry_ranking"].sort(key=lambda x: x["pct_chg"], reverse=True)
            
        except Exception as e:
            print(f"⚠️ 行业排名计算失败: {e}")
            summary["industry_ranking"] = []
        
        # 12. 主要指数数据（从 index_daily）
        try:
            main_indices = ['000001.SH', '399001.SZ', '399006.SZ', '000688.SH', '000300.SH']
            sql = text("""
                SELECT ts_code, close, pct_chg, amount / 10000 as amount_wan
                FROM index_daily
                WHERE trade_date = :trade_date AND ts_code IN :indices
            """)
            rows = conn.execute(sql, {"trade_date": trade_date, "indices": tuple(main_indices)}).fetchall()
            index_map = {
                '000001.SH': '上证指数', '399001.SZ': '深证成指', '399006.SZ': '创业板指',
                '000688.SH': '科创50', '000300.SH': '沪深300'
            }
            summary["index_data"] = [
                {"ts_code": row[0], "name": index_map.get(row[0], row[0]),
                 "close": round(float(row[1] or 0), 2), "pct_chg": round(float(row[2] or 0), 2),
                 "amount": round(float(row[3] or 0), 2)}
                for row in rows
            ]
        except:
            summary["index_data"] = []
        
        # 13. 行业资金流向统计（从 moneyflow + index_member）
        try:
            sql = text("""
                SELECT im.index_name as industry, 
                       SUM(mf.net_mf_amount) / 10000 as net_flow,
                       COUNT(*) as stock_count
                FROM moneyflow mf
                JOIN index_member im ON mf.ts_code = im.con_code
                WHERE mf.trade_date = :trade_date AND im.is_new = 'Y'
                GROUP BY im.index_code, im.index_name
                ORDER BY net_flow DESC
                LIMIT 31
            """)
            rows = conn.execute(sql, {"trade_date": trade_date}).fetchall()
            summary["industry_stats"] = [
                {"industry": row[0], "net_flow": round(float(row[1] or 0), 2), "stock_count": row[2]}
                for row in rows
            ]
        except:
            summary["industry_stats"] = []
    
    # 转换所有 Decimal 类型为 float
    summary = convert_decimal(summary)
    return summary


def get_summary(trade_date: str) -> Dict[str, Any]:
    """
    获取指定日期的市场汇总（优先从缓存/数据库读取，否则实时计算）
    """
    return build_or_load_summary(trade_date, precompute_daily_summary)


def precompute_and_save(trade_date: str):
    """预计算并保存（供定时任务调用）"""
    summary = precompute_daily_summary(trade_date)
    save_summary(summary)
    return summary


# 批量预计算最近N天
def precompute_recent_days(days: int = 30):
    """预计算最近N个交易日的数据"""
    with engine.connect() as conn:
        sql = text("""
            SELECT DISTINCT trade_date 
            FROM daily_kline 
            ORDER BY trade_date DESC 
            LIMIT :days
        """)
        rows = conn.execute(sql, {"days": days}).fetchall()
    
    for row in rows:
        trade_date = str(row[0])[:8]
        try:
            precompute_and_save(trade_date)
        except Exception as e:
            print(f"⚠️ 计算 {trade_date} 失败: {e}")


if __name__ == "__main__":
    # 测试
    ensure_summary_table()
    latest = get_latest_trade_date()
    if latest:
        summary = precompute_and_save(latest)
        print(f"上涨: {summary['up_count']}, 下跌: {summary['down_count']}")
