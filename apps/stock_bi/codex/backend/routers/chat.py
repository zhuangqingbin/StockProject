"""
Chat API 路由 - 处理自然语言查询
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import json
import asyncio

from ..infrastructure.cache import cache
from ..infrastructure.database import get_db
from ..modules.chat_query.application import resolve_intent
from ..models import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])


def get_latest_trade_date(db: Session):
    """获取最新交易日期（带缓存）"""
    cached = cache.get("latest_trade_date")
    if cached:
        return cached
    
    result = db.execute(text("SELECT MAX(trade_date) FROM daily_kline")).scalar()
    if result is None:
        return None
    if isinstance(result, str):
        date_str = result
    elif hasattr(result, 'strftime'):
        date_str = result.strftime('%Y%m%d')
    else:
        date_str = str(result)
    
    cache.set("latest_trade_date", date_str, ttl=600)
    return date_str


def format_date(d):
    """格式化日期为 YYYY-MM-DD"""
    if d is None:
        return None
    if isinstance(d, str):
        if len(d) == 8:
            return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
        return d
    if hasattr(d, 'strftime'):
        return d.strftime('%Y-%m-%d')
    return str(d)


@router.post("/query")
async def chat_query(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    处理自然语言查询
    """
    # 解析用户意图
    intent = await resolve_intent(request.message, request.context)
    
    action = intent.get("action", "overview")
    params = intent.get("params", {})
    reply = intent.get("reply", "")
    
    # 根据 action 执行相应查询
    data = None
    chart_config = None
    
    try:
        if action == "overview":
            data, chart_config = await _get_overview_data(db, params)
        elif action == "ranking":
            data, chart_config = await _get_ranking_data(db, params)
        elif action == "sector_stats":
            data, chart_config = await _get_sector_data(db, params)
        elif action == "distribution":
            data, chart_config = await _get_distribution_data(db, params)
        elif action == "kline":
            data, chart_config = await _get_kline_data(db, params)
        elif action == "amount_trend":
            data, chart_config = await _get_amount_trend_data(db, params)
        elif action == "limit_trend":
            data, chart_config = await _get_limit_trend_data(db, params)
    except Exception as e:
        reply = f"查询出错: {str(e)}"
    
    return {
        "reply": reply,
        "chart_config": chart_config,
        "data": data
    }


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    流式响应的 Chat 接口（模拟 ChatGPT 效果）
    """
    async def generate():
        # 解析用户意图
        intent = await resolve_intent(request.message, request.context)
        
        action = intent.get("action", "overview")
        params = intent.get("params", {})
        reply = intent.get("reply", "")
        
        # 模拟打字效果
        for char in reply:
            yield f"data: {json.dumps({'type': 'text', 'content': char})}\n\n"
            await asyncio.sleep(0.02)
        
        # 执行查询
        data = None
        chart_config = None
        
        try:
            if action == "overview":
                data, chart_config = await _get_overview_data(db, params)
            elif action == "ranking":
                data, chart_config = await _get_ranking_data(db, params)
            elif action == "sector_stats":
                data, chart_config = await _get_sector_data(db, params)
            elif action == "distribution":
                data, chart_config = await _get_distribution_data(db, params)
            elif action == "kline":
                data, chart_config = await _get_kline_data(db, params)
            elif action == "amount_trend":
                data, chart_config = await _get_amount_trend_data(db, params)
            elif action == "limit_trend":
                data, chart_config = await _get_limit_trend_data(db, params)
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            return
        
        # 发送数据和图表配置
        yield f"data: {json.dumps({'type': 'data', 'data': data, 'chart_config': chart_config})}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


async def _get_overview_data(db: Session, params: dict):
    """获取市场概览数据"""
    trade_date = params.get("trade_date")
    
    if not trade_date:
        trade_date = get_latest_trade_date(db)
    else:
        trade_date = trade_date.replace("-", "")
    
    sql = text("""
        SELECT 
            COUNT(*) as total_stocks,
            SUM(CASE WHEN pct_chg > 0 THEN 1 ELSE 0 END) as up_count,
            SUM(CASE WHEN pct_chg < 0 THEN 1 ELSE 0 END) as down_count,
            SUM(CASE WHEN pct_chg = 0 OR pct_chg IS NULL THEN 1 ELSE 0 END) as flat_count,
            SUM(CASE WHEN pct_chg >= 9.9 THEN 1 ELSE 0 END) as limit_up,
            SUM(CASE WHEN pct_chg <= -9.9 THEN 1 ELSE 0 END) as limit_down,
            SUM(amount) / 10000 as total_amount,
            AVG(pct_chg) as avg_pct_chg
        FROM daily_kline
        WHERE trade_date = :trade_date
    """)
    
    result = db.execute(sql, {"trade_date": trade_date}).fetchone()
    
    data = [{
        "trade_date": format_date(trade_date),
        "total_stocks": result[0] or 0,
        "up_count": result[1] or 0,
        "down_count": result[2] or 0,
        "flat_count": result[3] or 0,
        "limit_up": result[4] or 0,
        "limit_down": result[5] or 0,
        "total_amount": round(result[6] or 0, 2),
        "avg_pct_chg": round(result[7] or 0, 3)
    }]
    
    chart_config = {
        "type": "overview",
        "title": f"市场概览 - {format_date(trade_date)}"
    }
    
    return data, chart_config


async def _get_ranking_data(db: Session, params: dict):
    """获取排行榜数据"""
    sort_by = params.get("sort_by", "pct_chg")
    order = params.get("order", "desc")
    limit = params.get("limit", 20)
    market = params.get("market")
    
    trade_date = get_latest_trade_date(db)
    order_dir = "DESC" if order == "desc" else "ASC"
    
    where_conditions = ["trade_date = :trade_date"]
    query_params = {"trade_date": trade_date, "limit": limit}
    
    if market:
        if market == "科创板":
            where_conditions.append("ts_code LIKE '68%'")
        elif market == "创业板":
            where_conditions.append("ts_code LIKE '30%'")
        elif market in ["沪市主板", "上海主板"]:
            where_conditions.append("ts_code LIKE '60%' AND ts_code NOT LIKE '68%'")
        elif market in ["深市主板", "深圳主板"]:
            where_conditions.append("ts_code LIKE '00%'")
        elif market == "北交所":
            where_conditions.append("(ts_code LIKE '4%' OR ts_code LIKE '8%')")
    
    where_clause = " AND ".join(where_conditions)
    
    sql = text(f"""
        SELECT ts_code, pct_chg, close, amount, vol
        FROM daily_kline
        WHERE {where_clause}
        ORDER BY {sort_by} {order_dir}
        LIMIT :limit
    """)
    
    results = db.execute(sql, query_params).fetchall()
    
    data = [
        {
            "ts_code": row[0],
            "pct_chg": round(row[1] or 0, 2),
            "close": round(row[2] or 0, 2),
            "amount": round(row[3] or 0, 2),
            "vol": round(row[4] or 0, 2)
        }
        for row in results
    ]
    
    title_map = {
        "pct_chg": "涨跌幅榜",
        "amount": "成交额榜",
        "vol": "成交量榜"
    }
    
    chart_config = {
        "type": "table",
        "title": f"{market or '全市场'} {title_map.get(sort_by, '排行榜')} Top {limit}",
        "columns": [
            {"field": "ts_code", "label": "代码"},
            {"field": "pct_chg", "label": "涨跌幅%", "color": True},
            {"field": "close", "label": "收盘价"},
            {"field": "amount", "label": "成交额(千)"},
            {"field": "vol", "label": "成交量(手)"}
        ]
    }
    
    return data, chart_config


async def _get_sector_data(db: Session, params: dict):
    """获取板块统计数据"""
    trade_date = get_latest_trade_date(db)
    
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
            SUM(amount) / 10000 as total_amount,
            COUNT(*) as stock_count,
            SUM(CASE WHEN pct_chg > 0 THEN 1 ELSE 0 END) as up_count,
            SUM(CASE WHEN pct_chg < 0 THEN 1 ELSE 0 END) as down_count
        FROM daily_kline
        WHERE trade_date = :trade_date
        GROUP BY sector
        ORDER BY avg_pct_chg DESC
    """)
    
    results = db.execute(sql, {"trade_date": trade_date}).fetchall()
    
    data = [
        {
            "sector": row[0],
            "avg_pct_chg": round(row[1] or 0, 3),
            "total_amount": round(row[2] or 0, 2),
            "stock_count": row[3],
            "up_count": row[4],
            "down_count": row[5],
            "up_ratio": round(row[4] / row[3] * 100, 1) if row[3] > 0 else 0
        }
        for row in results
    ]
    
    chart_config = {
        "type": "bar",
        "title": "各板块涨跌统计",
        "xField": "sector",
        "yField": "avg_pct_chg"
    }
    
    return data, chart_config


async def _get_distribution_data(db: Session, params: dict):
    """获取涨跌分布数据"""
    trade_date = get_latest_trade_date(db)
    
    sql = text("""
        SELECT 
            FLOOR(pct_chg) as range_start,
            COUNT(*) as count
        FROM daily_kline
        WHERE trade_date = :trade_date
          AND pct_chg IS NOT NULL
          AND pct_chg BETWEEN -11 AND 21
        GROUP BY FLOOR(pct_chg)
        ORDER BY range_start
    """)
    
    results = db.execute(sql, {"trade_date": trade_date}).fetchall()
    
    data = [
        {
            "range": f"{int(row[0])}%~{int(row[0])+1}%",
            "range_start": int(row[0]),
            "count": row[1]
        }
        for row in results
    ]
    
    chart_config = {
        "type": "histogram",
        "title": "涨跌幅分布",
        "xField": "range",
        "yField": "count"
    }
    
    return data, chart_config


async def _get_kline_data(db: Session, params: dict):
    """获取K线数据"""
    ts_code = params.get("ts_code", "")
    days = params.get("days", 60)
    
    if not ts_code:
        return None, {"type": "error", "message": "请提供股票代码"}
    
    sql = text("""
        SELECT trade_date, open, high, low, close, vol, amount
        FROM daily_kline
        WHERE ts_code = :ts_code
        ORDER BY trade_date DESC
        LIMIT :limit
    """)
    
    results = db.execute(sql, {"ts_code": ts_code, "limit": days}).fetchall()
    
    data = [
        {
            "date": format_date(row[0]),
            "open": row[1],
            "high": row[2],
            "low": row[3],
            "close": row[4],
            "vol": row[5],
            "amount": row[6]
        }
        for row in reversed(list(results))
    ]
    
    chart_config = {
        "type": "kline",
        "title": f"{ts_code} K线图",
        "ts_code": ts_code
    }
    
    return data, chart_config


async def _get_amount_trend_data(db: Session, params: dict):
    """获取成交额趋势数据"""
    days = params.get("days", 30)
    
    sql = text("""
        SELECT 
            trade_date,
            SUM(amount) / 10000 as total_amount
        FROM daily_kline
        GROUP BY trade_date
        ORDER BY trade_date DESC
        LIMIT :days
    """)
    
    results = db.execute(sql, {"days": days}).fetchall()
    
    data = [
        {
            "date": format_date(row[0]),
            "amount": round(row[1], 2)
        }
        for row in reversed(list(results))
    ]
    
    chart_config = {
        "type": "line",
        "title": f"近{days}日成交额趋势",
        "xField": "date",
        "yField": "amount",
        "unit": "亿元"
    }
    
    return data, chart_config


async def _get_limit_trend_data(db: Session, params: dict):
    """获取涨停趋势数据"""
    days = params.get("days", 30)
    
    sql = text("""
        SELECT 
            trade_date,
            SUM(CASE WHEN pct_chg >= 9.9 THEN 1 ELSE 0 END) as limit_up,
            SUM(CASE WHEN pct_chg <= -9.9 THEN 1 ELSE 0 END) as limit_down
        FROM daily_kline
        GROUP BY trade_date
        ORDER BY trade_date DESC
        LIMIT :days
    """)
    
    results = db.execute(sql, {"days": days}).fetchall()
    
    data = [
        {
            "date": format_date(row[0]),
            "limit_up": row[1],
            "limit_down": row[2]
        }
        for row in reversed(list(results))
    ]
    
    chart_config = {
        "type": "line",
        "title": f"近{days}日涨跌停趋势",
        "xField": "date",
        "series": [
            {"field": "limit_up", "name": "涨停", "color": "#ef4444"},
            {"field": "limit_down", "name": "跌停", "color": "#22c55e"}
        ]
    }
    
    return data, chart_config


@router.get("/suggestions")
async def get_suggestions():
    """获取命令建议"""
    return {
        "suggestions": [
            {"text": "市场概览", "description": "查看今日市场整体情况"},
            {"text": "显示涨幅前20", "description": "涨幅排行榜"},
            {"text": "显示跌幅前20", "description": "跌幅排行榜"},
            {"text": "成交额前20", "description": "成交额排行榜"},
            {"text": "各板块表现", "description": "板块涨跌对比"},
            {"text": "涨跌分布", "description": "涨跌幅分布直方图"},
            {"text": "科创板涨幅榜", "description": "科创板排行"},
            {"text": "创业板涨幅榜", "description": "创业板排行"},
            {"text": "成交额趋势", "description": "近30日成交额走势"},
            {"text": "涨停趋势", "description": "近30日涨停家数走势"}
        ]
    }
