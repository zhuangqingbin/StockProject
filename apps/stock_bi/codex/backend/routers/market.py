"""
市场数据 API 路由 - 优化版本（使用预计算）
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from ..database import get_db, engine
from ..cache import cache
from ..precompute import get_summary, get_latest_trade_date, ensure_summary_table, check_data_consistency


def to_float(val):
    """Convert Decimal or other numeric types to float"""
    if val is None:
        return 0.0
    if isinstance(val, Decimal):
        return float(val)
    return float(val)

router = APIRouter(prefix="/api/market", tags=["market"])


def format_date(d):
    """格式化日期为 YYYY-MM-DD"""
    if d is None:
        return None
    if isinstance(d, str) and len(d) == 8:
        return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    if hasattr(d, 'strftime'):
        return d.strftime('%Y-%m-%d')
    return str(d)


@router.get("/latest-date")
async def api_latest_date():
    """获取最新交易日期"""
    latest = get_latest_trade_date()
    if latest is None:
        return {"latest_date": None}
    return {"latest_date": format_date(latest), "raw_date": latest}


@router.get("/summary")
async def api_summary(trade_date: Optional[str] = None):
    """
    获取完整市场汇总（核心 API，前端一次请求获取所有数据）
    包含数据一致性检查
    """
    if trade_date is None:
        target_date = get_latest_trade_date()
    else:
        target_date = trade_date.replace("-", "")
    
    if target_date is None:
        raise HTTPException(status_code=404, detail="No data available")
    
    summary = get_summary(target_date)
    summary["trade_date_fmt"] = format_date(target_date)
    
    # 添加数据一致性检查
    consistency = check_data_consistency()
    summary["data_consistency"] = {
        "consistent": consistency["consistent"],
        "primary_date": consistency["primary_date"],
        "warnings": consistency["warnings"]
    }
    
    return summary


@router.get("/data-consistency")
async def api_data_consistency():
    """
    检查各数据表的最新日期一致性
    确保所有看板数据日期统一，避免可视化误导
    """
    consistency = check_data_consistency()
    return consistency


@router.get("/overview")
async def api_overview(trade_date: Optional[str] = None):
    """获取市场概览数据"""
    if trade_date is None:
        target_date = get_latest_trade_date()
    else:
        target_date = trade_date.replace("-", "")
    
    if target_date is None:
        raise HTTPException(status_code=404, detail="No data available")
    
    summary = get_summary(target_date)
    return {
        "trade_date": format_date(target_date),
        "total_stocks": summary.get("total_stocks", 0),
        "up_count": summary.get("up_count", 0),
        "down_count": summary.get("down_count", 0),
        "flat_count": summary.get("flat_count", 0),
        "limit_up": summary.get("limit_up", 0),
        "limit_down": summary.get("limit_down", 0),
        "total_amount": summary.get("total_amount", 0),
        "avg_pct_chg": summary.get("avg_pct_chg", 0)
    }


@router.get("/sectors")
async def api_sectors(trade_date: Optional[str] = None):
    """获取板块统计"""
    if trade_date is None:
        target_date = get_latest_trade_date()
    else:
        target_date = trade_date.replace("-", "")
    
    summary = get_summary(target_date)
    return summary.get("sector_stats", [])


@router.get("/distribution")
async def api_distribution(trade_date: Optional[str] = None):
    """获取涨跌幅分布"""
    if trade_date is None:
        target_date = get_latest_trade_date()
    else:
        target_date = trade_date.replace("-", "")
    
    summary = get_summary(target_date)
    return summary.get("pct_distribution", [])


@router.get("/ranking")
async def api_ranking(
    trade_date: Optional[str] = None,
    sort_by: str = Query("pct_chg", description="排序字段: pct_chg/amount/turnover"),
    order: str = Query("desc", description="排序方向: desc/asc"),
    market: Optional[str] = Query(None, description="市场筛选"),
    limit: int = Query(20, ge=1, le=100)
):
    """获取股票排行榜"""
    if trade_date is None:
        target_date = get_latest_trade_date()
    else:
        target_date = trade_date.replace("-", "")
    
    summary = get_summary(target_date)
    
    # 根据排序方式选择预计算数据
    if sort_by == "amount":
        data = summary.get("top_amount", [])
    elif sort_by == "turnover":
        data = summary.get("top_turnover", [])
    elif order == "asc":
        data = summary.get("top_losers", [])
    else:
        data = summary.get("top_gainers", [])
    
    # 市场筛选
    if market:
        market_filters = {
            "科创板": lambda x: x["ts_code"].startswith("68"),
            "创业板": lambda x: x["ts_code"].startswith("30"),
            "沪市主板": lambda x: x["ts_code"].startswith("60") and not x["ts_code"].startswith("68"),
            "深市主板": lambda x: x["ts_code"].startswith("00"),
            "北交所": lambda x: x["ts_code"].startswith("4") or x["ts_code"].startswith("8")
        }
        if market in market_filters:
            data = [d for d in data if market_filters[market](d)]
    
    return data[:limit]


@router.get("/north-money")
async def api_north_money(trade_date: Optional[str] = None):
    """获取北向资金数据"""
    if trade_date is None:
        target_date = get_latest_trade_date()
    else:
        target_date = trade_date.replace("-", "")
    
    summary = get_summary(target_date)
    north_money = summary.get("north_money")
    
    if north_money:
        return {
            "trade_date": format_date(target_date),
            **north_money
        }
    return {"trade_date": format_date(target_date), "message": "无数据"}


@router.get("/north-money-trend")
async def api_north_money_trend(days: int = Query(30, ge=7, le=90)):
    """获取北向资金趋势"""
    cache_key = f"north_trend:{days}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    with engine.connect() as conn:
        sql = text("""
            SELECT trade_date, north_money, hgt, sgt
            FROM moneyflow_hsgt
            ORDER BY trade_date DESC
            LIMIT :days
        """)
        rows = conn.execute(sql, {"days": days}).fetchall()
    
    result = [
        {
            "trade_date": format_date(row[0]),
            "north_total": round(to_float(row[1]), 2),
            "hgt": round(to_float(row[2]), 2),
            "sgt": round(to_float(row[3]), 2)
        }
        for row in reversed(list(rows))
    ]
    
    cache.set(cache_key, result, ttl=300)
    return result


@router.get("/top-list")
async def api_top_list(trade_date: Optional[str] = None, limit: int = Query(20, ge=1, le=50)):
    """获取龙虎榜数据"""
    if trade_date is None:
        target_date = get_latest_trade_date()
    else:
        target_date = trade_date.replace("-", "")
    
    cache_key = f"toplist:{target_date}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    with engine.connect() as conn:
        sql = text("""
            SELECT ts_code, name, pct_change, l_buy / 10000 as buy_wan, 
                   l_sell / 10000 as sell_wan, net_amount / 10000 as net_wan, reason
            FROM top_list
            WHERE trade_date = :trade_date
            ORDER BY net_amount DESC
            LIMIT :limit
        """)
        rows = conn.execute(sql, {"trade_date": target_date, "limit": limit}).fetchall()
    
    result = [
        {
            "ts_code": row[0], "name": row[1], "pct_chg": round(to_float(row[2]), 2),
            "buy": round(to_float(row[3]), 2), "sell": round(to_float(row[4]), 2),
            "net": round(to_float(row[5]), 2), "reason": row[6]
        }
        for row in rows
    ]
    
    cache.set(cache_key, result, ttl=300)
    return result


@router.get("/top-list-summary")
async def api_top_list_summary(trade_date: Optional[str] = None):
    """获取龙虎榜汇总"""
    if trade_date is None:
        target_date = get_latest_trade_date()
    else:
        target_date = trade_date.replace("-", "")
    
    summary = get_summary(target_date)
    top_list = summary.get("top_list_summary")
    
    if top_list:
        return {"trade_date": format_date(target_date), **top_list}
    return {"trade_date": format_date(target_date), "count": 0}


@router.get("/indices")
async def api_indices(trade_date: Optional[str] = None):
    """获取主要指数数据"""
    if trade_date is None:
        target_date = get_latest_trade_date()
    else:
        target_date = trade_date.replace("-", "")
    
    summary = get_summary(target_date)
    return {
        "trade_date": format_date(target_date),
        "indices": summary.get("index_data", [])
    }


@router.get("/industries")
async def api_industries(trade_date: Optional[str] = None, limit: int = Query(31, ge=1, le=50)):
    """获取申万行业排名"""
    if trade_date is None:
        target_date = get_latest_trade_date()
    else:
        target_date = trade_date.replace("-", "")
    
    summary = get_summary(target_date)
    ranking = summary.get("industry_ranking", [])
    return {
        "trade_date": format_date(target_date),
        "industries": ranking[:limit]
    }


@router.get("/industry-flow")
async def api_industry_flow(trade_date: Optional[str] = None):
    """获取行业资金流向"""
    if trade_date is None:
        target_date = get_latest_trade_date()
    else:
        target_date = trade_date.replace("-", "")
    
    summary = get_summary(target_date)
    return {
        "trade_date": format_date(target_date),
        "industries": summary.get("industry_stats", [])
    }


@router.get("/limit-stats")
async def api_limit_stats(trade_date: Optional[str] = None):
    """获取涨跌停统计"""
    if trade_date is None:
        target_date = get_latest_trade_date()
    else:
        target_date = trade_date.replace("-", "")
    
    summary = get_summary(target_date)
    limit_stats = summary.get("limit_stats")
    
    if limit_stats:
        return {"trade_date": format_date(target_date), **limit_stats}
    return {
        "trade_date": format_date(target_date),
        "limit_up": summary.get("limit_up", 0),
        "limit_down": summary.get("limit_down", 0)
    }


@router.get("/amount-trend")
async def api_amount_trend(days: int = Query(30, ge=7, le=90)):
    """获取成交额趋势"""
    cache_key = f"amount_trend:{days}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    with engine.connect() as conn:
        sql = text("""
            SELECT trade_date, SUM(amount) / 100000000 as total_amount
            FROM daily_kline
            GROUP BY trade_date
            ORDER BY trade_date DESC
            LIMIT :days
        """)
        rows = conn.execute(sql, {"days": days}).fetchall()
    
    result = [
        {"trade_date": format_date(row[0]), "total_amount": round(to_float(row[1]), 2)}
        for row in reversed(list(rows))
    ]
    
    cache.set(cache_key, result, ttl=300)
    return result


@router.get("/limit-trend")
async def api_limit_trend(days: int = Query(30, ge=7, le=90)):
    """获取涨停趋势"""
    cache_key = f"limit_trend:{days}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    with engine.connect() as conn:
        sql = text("""
            SELECT trade_date,
                   SUM(CASE WHEN pct_chg >= 9.9 THEN 1 ELSE 0 END) as limit_up,
                   SUM(CASE WHEN pct_chg <= -9.9 THEN 1 ELSE 0 END) as limit_down
            FROM daily_kline
            GROUP BY trade_date
            ORDER BY trade_date DESC
            LIMIT :days
        """)
        rows = conn.execute(sql, {"days": days}).fetchall()
    
    result = [
        {"trade_date": format_date(row[0]), "limit_up": int(row[1] or 0), "limit_down": int(row[2] or 0)}
        for row in reversed(list(rows))
    ]
    
    cache.set(cache_key, result, ttl=300)
    return result


@router.get("/kline/{ts_code}")
async def api_kline(
    ts_code: str,
    limit: int = Query(60, ge=1, le=500)
):
    """获取个股K线"""
    cache_key = f"kline:{ts_code}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    with engine.connect() as conn:
        sql = text("""
            SELECT ts_code, trade_date, open, high, low, close, pct_chg, vol, amount
            FROM daily_kline
            WHERE ts_code = :ts_code
            ORDER BY trade_date DESC
            LIMIT :limit
        """)
        rows = conn.execute(sql, {"ts_code": ts_code, "limit": limit}).fetchall()
    
    result = [
        {
            "ts_code": row[0], "date": format_date(row[1]),
            "open": to_float(row[2]), "high": to_float(row[3]), "low": to_float(row[4]), "close": to_float(row[5]),
            "pct_chg": to_float(row[6]), "vol": to_float(row[7]), "amount": to_float(row[8])
        }
        for row in reversed(list(rows))
    ]
    
    cache.set(cache_key, result, ttl=300)
    return result


@router.get("/search")
async def api_search(
    keyword: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50)
):
    """搜索股票"""
    with engine.connect() as conn:
        sql = text("""
            SELECT ts_code, name
            FROM stock_basic
            WHERE ts_code LIKE :keyword OR name LIKE :keyword
            ORDER BY ts_code
            LIMIT :limit
        """)
        rows = conn.execute(sql, {"keyword": f"%{keyword}%", "limit": limit}).fetchall()
    
    if not rows:
        # 如果 stock_basic 表没数据，从 daily_kline 查
        with engine.connect() as conn:
            sql = text("""
                SELECT DISTINCT ts_code, ts_code as name
                FROM daily_kline
                WHERE ts_code LIKE :keyword
                LIMIT :limit
            """)
            rows = conn.execute(sql, {"keyword": f"%{keyword}%", "limit": limit}).fetchall()
    
    return [{"ts_code": row[0], "name": row[1] or row[0]} for row in rows]


@router.post("/precompute/{trade_date}")
async def api_precompute(trade_date: str):
    """手动触发预计算"""
    from ..precompute import precompute_and_save
    target_date = trade_date.replace("-", "")
    try:
        summary = precompute_and_save(target_date)
        return {"status": "success", "trade_date": target_date}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-cache")
async def api_clear_cache():
    """清空缓存"""
    cache.clear()
    return {"message": "Cache cleared"}


@router.post("/notify-update")
async def api_notify_update():
    """手动触发数据更新通知"""
    from .websocket import notify_data_update
    result = await notify_data_update()
    return result


@router.get("/stock/{ts_code}")
async def api_stock_detail(ts_code: str, trade_date: Optional[str] = None):
    """
    获取股票详情（K线、今日数据、估值指标）
    """
    if trade_date is None:
        target_date = get_latest_trade_date()
    else:
        target_date = trade_date.replace("-", "")
    
    if target_date is None:
        raise HTTPException(status_code=404, detail="No data available")
    
    cache_key = f"stock_detail:{ts_code}:{target_date}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    result = {
        "ts_code": ts_code,
        "trade_date": format_date(target_date),
        "daily": None,
        "basic": None,
        "kline": [],
        "company": None
    }
    
    with engine.connect() as conn:
        # 1. 今日行情
        sql = text("""
            SELECT k.ts_code, k.trade_date, k.open, k.high, k.low, k.close, 
                   k.pre_close, k.pct_chg, k.vol, k.amount, b.name
            FROM daily_kline k
            LEFT JOIN stock_basic b ON k.ts_code = b.ts_code
            WHERE k.ts_code = :ts_code AND k.trade_date = :trade_date
        """)
        row = conn.execute(sql, {"ts_code": ts_code, "trade_date": target_date}).fetchone()
        if row:
            result["daily"] = {
                "ts_code": row[0], "trade_date": format_date(row[1]),
                "open": to_float(row[2]), "high": to_float(row[3]),
                "low": to_float(row[4]), "close": to_float(row[5]),
                "pre_close": to_float(row[6]), "pct_chg": to_float(row[7]),
                "vol": to_float(row[8]), "amount": to_float(row[9]),
                "name": row[10] or ts_code[:6]
            }
        
        # 2. 估值指标
        sql = text("""
            SELECT ts_code, trade_date, turnover_rate, pe, pe_ttm, pb, 
                   total_mv, circ_mv, volume_ratio
            FROM daily_basic
            WHERE ts_code = :ts_code AND trade_date = :trade_date
        """)
        row = conn.execute(sql, {"ts_code": ts_code, "trade_date": target_date}).fetchone()
        if row:
            result["basic"] = {
                "turnover_rate": to_float(row[2]),
                "pe": to_float(row[3]), "pe_ttm": to_float(row[4]),
                "pb": to_float(row[5]),
                "total_mv": round(to_float(row[6]) / 10000, 2),  # 万元 -> 亿
                "circ_mv": round(to_float(row[7]) / 10000, 2),
                "volume_ratio": to_float(row[8])
            }
        
        # 3. 60日K线
        sql = text("""
            SELECT trade_date, open, high, low, close, vol, amount, pct_chg
            FROM daily_kline
            WHERE ts_code = :ts_code
            ORDER BY trade_date DESC
            LIMIT 60
        """)
        rows = conn.execute(sql, {"ts_code": ts_code}).fetchall()
        result["kline"] = [
            {
                "date": format_date(r[0]), "open": to_float(r[1]), "high": to_float(r[2]),
                "low": to_float(r[3]), "close": to_float(r[4]), "vol": to_float(r[5]),
                "amount": to_float(r[6]), "pct_chg": to_float(r[7])
            }
            for r in reversed(list(rows))
        ]
        
        # 4. 公司信息
        sql = text("""
            SELECT ts_code, name, area, industry, market, list_date
            FROM stock_basic
            WHERE ts_code = :ts_code
        """)
        row = conn.execute(sql, {"ts_code": ts_code}).fetchone()
        if row:
            result["company"] = {
                "ts_code": row[0], "name": row[1], "area": row[2],
                "industry": row[3], "market": row[4], "list_date": row[5]
            }
    
    cache.set(cache_key, result, ttl=300)
    return result


@router.get("/company/{ts_code}")
async def api_company_info(ts_code: str):
    """获取公司基础信息"""
    cache_key = f"company:{ts_code}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    with engine.connect() as conn:
        # 基础信息
        sql = text("""
            SELECT ts_code, symbol, name, area, industry, market, exchange, list_date
            FROM stock_basic
            WHERE ts_code = :ts_code
        """)
        row = conn.execute(sql, {"ts_code": ts_code}).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        result = {
            "ts_code": row[0], "symbol": row[1], "name": row[2],
            "area": row[3], "industry": row[4], "market": row[5],
            "exchange": row[6], "list_date": row[7]
        }
        
        # 尝试获取公司详情
        sql = text("""
            SELECT chairman, manager, secretary, reg_capital, province, city, 
                   introduction, website, employees, main_business
            FROM stock_company
            WHERE ts_code = :ts_code
        """)
        detail = conn.execute(sql, {"ts_code": ts_code}).fetchone()
        if detail:
            result.update({
                "chairman": detail[0], "manager": detail[1], "secretary": detail[2],
                "reg_capital": to_float(detail[3]), "province": detail[4], "city": detail[5],
                "introduction": detail[6], "website": detail[7],
                "employees": detail[8], "main_business": detail[9]
            })
    
    cache.set(cache_key, result, ttl=3600)  # 公司信息缓存1小时
    return result


@router.get("/sectors-enhanced")
async def api_sectors_enhanced(
    trade_date: Optional[str] = None,
    top: int = Query(10, ge=1, le=20),
    filter_type: str = Query("all", description="all/up/down")
):
    """
    获取板块统计（含涨跌家数分布）
    """
    if trade_date is None:
        target_date = get_latest_trade_date()
    else:
        target_date = trade_date.replace("-", "")
    
    if target_date is None:
        raise HTTPException(status_code=404, detail="No data available")
    
    cache_key = f"sectors_enhanced:{target_date}:{top}:{filter_type}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    with engine.connect() as conn:
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
                SUM(CASE WHEN pct_chg < 0 THEN 1 ELSE 0 END) as down_count,
                SUM(CASE WHEN pct_chg = 0 OR pct_chg IS NULL THEN 1 ELSE 0 END) as flat_count,
                SUM(CASE WHEN pct_chg >= 9.9 THEN 1 ELSE 0 END) as limit_up,
                SUM(CASE WHEN pct_chg <= -9.9 THEN 1 ELSE 0 END) as limit_down
            FROM daily_kline
            WHERE trade_date = :trade_date
            GROUP BY sector
            ORDER BY avg_pct_chg DESC
        """)
        rows = conn.execute(sql, {"trade_date": target_date}).fetchall()
    
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
            "up_ratio": round(int(row[4] or 0) / max(int(row[3] or 1), 1) * 100, 1)
        }
        for row in rows
        if row[0] != '其他'  # 过滤掉"其他"
    ]
    
    # 根据筛选类型排序
    if filter_type == "up":
        sectors = sorted(sectors, key=lambda x: x["avg_pct_chg"], reverse=True)
    elif filter_type == "down":
        sectors = sorted(sectors, key=lambda x: x["avg_pct_chg"])
    
    result = {
        "trade_date": format_date(target_date),
        "sectors": sectors[:top]
    }
    
    cache.set(cache_key, result, ttl=300)
    return result


@router.get("/industries-enhanced")
async def api_industries_enhanced(
    trade_date: Optional[str] = None,
    top: int = Query(15, ge=1, le=31),
    order: str = Query("desc", description="desc/asc")
):
    """
    获取行业排名（支持涨跌榜切换）
    """
    if trade_date is None:
        target_date = get_latest_trade_date()
    else:
        target_date = trade_date.replace("-", "")
    
    if target_date is None:
        raise HTTPException(status_code=404, detail="No data available")
    
    cache_key = f"industries_enhanced:{target_date}:{top}:{order}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # 尝试从申万行业指数获取
    with engine.connect() as conn:
        # 先从 stock_basic 按行业聚合
        sql = text("""
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
            ORDER BY avg_pct_chg """ + ("DESC" if order == "desc" else "ASC") + """
            LIMIT :limit
        """)
        rows = conn.execute(sql, {"trade_date": target_date, "limit": top}).fetchall()
    
    industries = [
        {
            "name": row[0],
            "pct_chg": round(float(row[1] or 0), 3),
            "total_amount": round(float(row[2] or 0), 2),
            "stock_count": int(row[3] or 0),
            "up_count": int(row[4] or 0),
            "down_count": int(row[5] or 0),
            "up_ratio": round(int(row[4] or 0) / max(int(row[3] or 1), 1) * 100, 1)
        }
        for row in rows
    ]
    
    result = {
        "trade_date": format_date(target_date),
        "order": order,
        "industries": industries
    }
    
    cache.set(cache_key, result, ttl=300)
    return result


@router.get("/ranking-enhanced")
async def api_ranking_enhanced(
    trade_date: Optional[str] = None,
    sort_by: str = Query("pct_chg", description="pct_chg/amount/turnover"),
    order: str = Query("desc", description="desc/asc"),
    market: Optional[str] = Query(None, description="科创板/创业板/沪市主板/深市主板/北交所"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    top: int = Query(20, ge=1, le=100)
):
    """
    增强版排行榜（支持多维筛选）
    """
    if trade_date is None:
        target_date = get_latest_trade_date()
    else:
        target_date = trade_date.replace("-", "")
    
    if target_date is None:
        raise HTTPException(status_code=404, detail="No data available")
    
    cache_key = f"ranking_enhanced:{target_date}:{sort_by}:{order}:{market}:{industry}:{top}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # 构建动态查询
    order_by_map = {
        "pct_chg": "k.pct_chg",
        "amount": "k.amount",
        "turnover": "db.turnover_rate"
    }
    order_col = order_by_map.get(sort_by, "k.pct_chg")
    order_dir = "DESC" if order == "desc" else "ASC"
    
    # 市场筛选条件
    market_conditions = {
        "科创板": "k.ts_code LIKE '68%'",
        "创业板": "k.ts_code LIKE '30%'",
        "沪市主板": "k.ts_code LIKE '60%' AND k.ts_code NOT LIKE '68%'",
        "深市主板": "k.ts_code LIKE '00%'",
        "北交所": "(k.ts_code LIKE '4%' OR k.ts_code LIKE '8%')"
    }
    
    where_clauses = ["k.trade_date = :trade_date"]
    if market and market in market_conditions:
        where_clauses.append(market_conditions[market])
    if industry:
        where_clauses.append("b.industry = :industry")
    
    where_sql = " AND ".join(where_clauses)
    
    with engine.connect() as conn:
        sql = text(f"""
            SELECT k.ts_code, b.name, k.pct_chg, k.close, k.amount / 10000 as amount_wan,
                   k.vol, db.turnover_rate, b.industry, db.pe, db.pb
            FROM daily_kline k
            LEFT JOIN stock_basic b ON k.ts_code = b.ts_code
            LEFT JOIN daily_basic db ON k.ts_code = db.ts_code AND k.trade_date = db.trade_date
            WHERE {where_sql}
            ORDER BY {order_col} {order_dir}
            LIMIT :limit
        """)
        params = {"trade_date": target_date, "limit": top}
        if industry:
            params["industry"] = industry
        
        rows = conn.execute(sql, params).fetchall()
    
    stocks = [
        {
            "ts_code": row[0],
            "name": row[1] or row[0][:6],
            "pct_chg": round(to_float(row[2]), 2),
            "close": round(to_float(row[3]), 2),
            "amount": round(to_float(row[4]), 2),
            "vol": round(to_float(row[5]) / 10000, 2),  # 手 -> 万手
            "turnover_rate": round(to_float(row[6]), 2),
            "industry": row[7],
            "pe": round(to_float(row[8]), 2) if row[8] else None,
            "pb": round(to_float(row[9]), 2) if row[9] else None
        }
        for row in rows
    ]
    
    result = {
        "trade_date": format_date(target_date),
        "sort_by": sort_by,
        "order": order,
        "market": market,
        "industry": industry,
        "stocks": stocks
    }
    
    cache.set(cache_key, result, ttl=300)
    return result


@router.get("/industry-detail/{industry}")
async def api_industry_detail(
    industry: str,
    trade_date: Optional[str] = None,
    kline_limit: int = Query(60, ge=10, le=120)
):
    """
    获取行业详情（包含K线数据 + 今日统计）
    """
    if trade_date is None:
        target_date = get_latest_trade_date()
    else:
        target_date = trade_date.replace("-", "")
    
    if target_date is None:
        raise HTTPException(status_code=404, detail="No data available")
    
    cache_key = f"industry_detail:{industry}:{target_date}:{kline_limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    result = {
        "industry": industry,
        "trade_date": format_date(target_date),
        "kline": [],
        "today": None,
        "index_code": None
    }
    
    with engine.connect() as conn:
        has_sw_index = False
        
        # 1. 尝试从申万行业指数获取K线（通过名称匹配）
        # 申万行业名称格式: "半导体I"、"计算机I" (I表示一级行业)
        # stock_basic.industry 格式: "半导体"、"计算机"
        try:
            # 尝试多种匹配方式
            sql_find_index = text("""
                SELECT DISTINCT ts_code, name FROM index_sw_daily 
                WHERE name LIKE :pattern1 
                   OR name LIKE :pattern2
                   OR name = :exact
                ORDER BY trade_date DESC LIMIT 1
            """)
            index_row = conn.execute(sql_find_index, {
                "pattern1": f"{industry}%",   # "半导体" -> "半导体I"
                "pattern2": f"%{industry}%",  # 模糊匹配
                "exact": industry             # 精确匹配
            }).fetchone()
            
            if index_row:
                index_code = index_row[0]
                result["index_code"] = index_code
                result["index_name"] = index_row[1]
                
                # 获取K线数据
                sql_kline = text("""
                    SELECT trade_date, open, high, low, close, vol, amount, pct_change
                    FROM index_sw_daily
                    WHERE ts_code = :ts_code
                    ORDER BY trade_date DESC
                    LIMIT :limit
                """)
                kline_rows = conn.execute(sql_kline, {"ts_code": index_code, "limit": kline_limit}).fetchall()
                
                if kline_rows:
                    has_sw_index = True
                    result["kline"] = [
                        {
                            "date": row[0],
                            "open": round(to_float(row[1]), 2),
                            "high": round(to_float(row[2]), 2),
                            "low": round(to_float(row[3]), 2),
                            "close": round(to_float(row[4]), 2),
                            "vol": round(to_float(row[5]), 2),
                            "amount": round(to_float(row[6]) / 10000, 2),
                            "pct_chg": round(to_float(row[7]), 2)
                        }
                        for row in reversed(kline_rows)
                    ]
                    
                    # 获取今日数据
                    sql_today = text("""
                        SELECT open, high, low, close, pct_change, vol, amount, pe, pb
                        FROM index_sw_daily
                        WHERE ts_code = :ts_code AND trade_date = :trade_date
                    """)
                    today_row = conn.execute(sql_today, {"ts_code": index_code, "trade_date": target_date}).fetchone()
                    
                    if today_row:
                        result["today"] = {
                            "open": round(to_float(today_row[0]), 2),
                            "high": round(to_float(today_row[1]), 2),
                            "low": round(to_float(today_row[2]), 2),
                            "close": round(to_float(today_row[3]), 2),
                            "pct_chg": round(to_float(today_row[4]), 2),
                            "vol": round(to_float(today_row[5]), 2),
                            "amount": round(to_float(today_row[6]) / 10000, 2),
                            "pe": round(to_float(today_row[7]), 2) if today_row[7] else None,
                            "pb": round(to_float(today_row[8]), 2) if today_row[8] else None
                        }
        except Exception as e:
            print(f"⚠️ 获取申万行业指数失败: {e}")
        
        # 2. 如果没有申万行业指数，从个股数据聚合生成行业K线
        if not has_sw_index:
            try:
                sql_agg_kline = text("""
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
                """)
                agg_rows = conn.execute(sql_agg_kline, {"industry": industry, "limit": kline_limit}).fetchall()
                
                if agg_rows:
                    result["index_name"] = f"{industry}(聚合)"
                    result["kline"] = [
                        {
                            "date": row[0],
                            "open": round(to_float(row[1]), 2),
                            "high": round(to_float(row[2]), 2),
                            "low": round(to_float(row[3]), 2),
                            "close": round(to_float(row[4]), 2),
                            "vol": round(to_float(row[5]) / 10000, 2),  # 转万手
                            "amount": round(to_float(row[6]) / 100000000, 2),  # 转亿元
                            "pct_chg": round(to_float(row[7]), 2)
                        }
                        for row in reversed(agg_rows)
                    ]
            except Exception as e:
                print(f"⚠️ 聚合行业K线失败: {e}")
        
        # 2. 从 stock_basic + daily_kline 聚合行业统计
        sql_stats = text("""
            SELECT 
                COUNT(*) as stock_count,
                SUM(CASE WHEN k.pct_chg > 0 THEN 1 ELSE 0 END) as up_count,
                SUM(CASE WHEN k.pct_chg < 0 THEN 1 ELSE 0 END) as down_count,
                AVG(k.pct_chg) as avg_pct_chg,
                SUM(k.amount) / 100000000 as total_amount
            FROM daily_kline k
            JOIN stock_basic b ON k.ts_code = b.ts_code
            WHERE k.trade_date = :trade_date AND b.industry = :industry
        """)
        stats_row = conn.execute(sql_stats, {"trade_date": target_date, "industry": industry}).fetchone()
        
        if stats_row:
            result["stats"] = {
                "stock_count": int(stats_row[0] or 0),
                "up_count": int(stats_row[1] or 0),
                "down_count": int(stats_row[2] or 0),
                "avg_pct_chg": round(to_float(stats_row[3]), 2),
                "total_amount": round(to_float(stats_row[4]), 2)
            }
    
    cache.set(cache_key, result, ttl=300)
    return result


@router.get("/industry-stocks/{industry}")
async def api_industry_stocks(
    industry: str,
    trade_date: Optional[str] = None,
    order: str = Query("desc", description="desc/asc"),
    limit: int = Query(100, ge=1, le=500)
):
    """
    获取指定行业的所有股票（支持涨跌排序）
    """
    if trade_date is None:
        target_date = get_latest_trade_date()
    else:
        target_date = trade_date.replace("-", "")
    
    if target_date is None:
        raise HTTPException(status_code=404, detail="No data available")
    
    cache_key = f"industry_stocks:{industry}:{target_date}:{order}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    order_dir = "DESC" if order == "desc" else "ASC"
    
    with engine.connect() as conn:
        sql = text(f"""
            SELECT 
                k.ts_code, b.name, k.pct_chg, k.close, k.open, k.high, k.low,
                k.vol / 10000 as vol_wan, k.amount / 10000 as amount_wan,
                db.turnover_rate, db.pe, db.pb, db.total_mv / 10000 as total_mv_yi
            FROM daily_kline k
            JOIN stock_basic b ON k.ts_code = b.ts_code
            LEFT JOIN daily_basic db ON k.ts_code = db.ts_code AND k.trade_date = db.trade_date
            WHERE k.trade_date = :trade_date
              AND b.industry = :industry
            ORDER BY k.pct_chg {order_dir}
            LIMIT :limit
        """)
        rows = conn.execute(sql, {
            "trade_date": target_date,
            "industry": industry,
            "limit": limit
        }).fetchall()
    
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
            "total_mv": round(to_float(row[12]), 2) if row[12] else None
        }
        for row in rows
    ]
    
    # 统计信息
    up_count = sum(1 for s in stocks if s["pct_chg"] > 0)
    down_count = sum(1 for s in stocks if s["pct_chg"] < 0)
    flat_count = len(stocks) - up_count - down_count
    
    result = {
        "trade_date": format_date(target_date),
        "industry": industry,
        "order": order,
        "total": len(stocks),
        "up_count": up_count,
        "down_count": down_count,
        "flat_count": flat_count,
        "stocks": stocks
    }
    
    cache.set(cache_key, result, ttl=300)
    return result


@router.get("/moneyflow/{ts_code}")
async def api_moneyflow(ts_code: str, trade_date: Optional[str] = None):
    """获取个股资金流向"""
    if trade_date is None:
        target_date = get_latest_trade_date()
    else:
        target_date = trade_date.replace("-", "")
    
    cache_key = f"moneyflow:{ts_code}:{target_date}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    with engine.connect() as conn:
        sql = text("""
            SELECT ts_code, trade_date, 
                   buy_sm_vol, buy_sm_amount, sell_sm_vol, sell_sm_amount,
                   buy_md_vol, buy_md_amount, sell_md_vol, sell_md_amount,
                   buy_lg_vol, buy_lg_amount, sell_lg_vol, sell_lg_amount,
                   buy_elg_vol, buy_elg_amount, sell_elg_vol, sell_elg_amount,
                   net_mf_vol, net_mf_amount
            FROM moneyflow
            WHERE ts_code = :ts_code AND trade_date = :trade_date
        """)
        row = conn.execute(sql, {"ts_code": ts_code, "trade_date": target_date}).fetchone()
    
    if not row:
        return {"ts_code": ts_code, "trade_date": format_date(target_date), "message": "无资金流向数据"}
    
    result = {
        "ts_code": row[0],
        "trade_date": format_date(row[1]),
        "small": {
            "buy_vol": to_float(row[2]), "buy_amount": to_float(row[3]),
            "sell_vol": to_float(row[4]), "sell_amount": to_float(row[5]),
            "net_amount": to_float(row[3]) - to_float(row[5])
        },
        "medium": {
            "buy_vol": to_float(row[6]), "buy_amount": to_float(row[7]),
            "sell_vol": to_float(row[8]), "sell_amount": to_float(row[9]),
            "net_amount": to_float(row[7]) - to_float(row[9])
        },
        "large": {
            "buy_vol": to_float(row[10]), "buy_amount": to_float(row[11]),
            "sell_vol": to_float(row[12]), "sell_amount": to_float(row[13]),
            "net_amount": to_float(row[11]) - to_float(row[13])
        },
        "extra_large": {
            "buy_vol": to_float(row[14]), "buy_amount": to_float(row[15]),
            "sell_vol": to_float(row[16]), "sell_amount": to_float(row[17]),
            "net_amount": to_float(row[15]) - to_float(row[17])
        },
        "net_mf_vol": to_float(row[18]),
        "net_mf_amount": to_float(row[19])
    }
    
    cache.set(cache_key, result, ttl=300)
    return result
