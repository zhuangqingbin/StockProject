"""
市场数据 API 路由 - 优化版本（使用预计算）
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from ..infrastructure.cache import cache
from ..modules.market_summary.application import (
    build_latest_date_payload,
    build_indices_payload,
    build_industry_flow_payload,
    build_industry_ranking_payload,
    build_limit_stats_payload,
    build_north_money_payload,
    build_overview_payload,
    build_summary_payload,
    build_top_list_summary_payload,
    normalize_trade_date,
)
from ..modules.market_summary.service import (
    get_amount_trend,
    get_industries_enhanced,
    get_limit_trend,
    get_north_money_trend,
    get_sectors_enhanced,
    get_top_list,
)
from ..modules.ranking_kline.application import filter_market_rows, select_ranking_rows
from ..modules.ranking_kline.service import (
    get_industry_stocks,
    get_kline,
    get_moneyflow,
    get_ranking_enhanced,
    search_stocks,
)
from ..modules.stock_detail.service import (
    get_company_info,
    get_industry_detail,
    get_stock_detail,
)
from ..modules.realtime_updates.service import sync_market_data_update
from ..precompute import check_data_consistency, get_latest_trade_date, get_summary, precompute_and_save

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/latest-date")
async def api_latest_date():
    """获取最新交易日期"""
    latest = get_latest_trade_date()
    return build_latest_date_payload(latest)


@router.get("/summary")
async def api_summary(trade_date: Optional[str] = None):
    """
    获取完整市场汇总（核心 API，前端一次请求获取所有数据）
    包含数据一致性检查
    """
    target_date = normalize_trade_date(trade_date, latest_trade_date=get_latest_trade_date())
    
    if target_date is None:
        raise HTTPException(status_code=404, detail="No data available")
    
    summary = get_summary(target_date)
    consistency = check_data_consistency()
    return build_summary_payload(target_date, summary, consistency)


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
    target_date = normalize_trade_date(trade_date, latest_trade_date=get_latest_trade_date())
    
    if target_date is None:
        raise HTTPException(status_code=404, detail="No data available")
    
    summary = get_summary(target_date)
    return build_overview_payload(target_date, summary)


@router.get("/sectors")
async def api_sectors(trade_date: Optional[str] = None):
    """获取板块统计"""
    target_date = normalize_trade_date(trade_date, latest_trade_date=get_latest_trade_date())
    
    summary = get_summary(target_date)
    return summary.get("sector_stats", [])


@router.get("/distribution")
async def api_distribution(trade_date: Optional[str] = None):
    """获取涨跌幅分布"""
    target_date = normalize_trade_date(trade_date, latest_trade_date=get_latest_trade_date())
    
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
    target_date = normalize_trade_date(trade_date, latest_trade_date=get_latest_trade_date())
    
    summary = get_summary(target_date)
    data = select_ranking_rows(summary, sort_by=sort_by, order=order)
    data = filter_market_rows(data, market)
    return data[:limit]


@router.get("/north-money")
async def api_north_money(trade_date: Optional[str] = None):
    """获取北向资金数据"""
    target_date = normalize_trade_date(trade_date, latest_trade_date=get_latest_trade_date())
    summary = get_summary(target_date)
    north_money = summary.get("north_money")
    return build_north_money_payload(target_date, north_money)


@router.get("/north-money-trend")
async def api_north_money_trend(days: int = Query(30, ge=7, le=90)):
    """获取北向资金趋势"""
    cache_key = f"north_trend:{days}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    result = get_north_money_trend(days)
    
    cache.set(cache_key, result, ttl=300)
    return result


@router.get("/top-list")
async def api_top_list(trade_date: Optional[str] = None, limit: int = Query(20, ge=1, le=50)):
    """获取龙虎榜数据"""
    target_date = normalize_trade_date(trade_date, latest_trade_date=get_latest_trade_date())
    
    cache_key = f"toplist:{target_date}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    result = get_top_list(target_date, limit)
    
    cache.set(cache_key, result, ttl=300)
    return result


@router.get("/top-list-summary")
async def api_top_list_summary(trade_date: Optional[str] = None):
    """获取龙虎榜汇总"""
    target_date = normalize_trade_date(trade_date, latest_trade_date=get_latest_trade_date())
    
    summary = get_summary(target_date)
    return build_top_list_summary_payload(target_date, summary)


@router.get("/indices")
async def api_indices(trade_date: Optional[str] = None):
    """获取主要指数数据"""
    target_date = normalize_trade_date(trade_date, latest_trade_date=get_latest_trade_date())
    
    summary = get_summary(target_date)
    return build_indices_payload(target_date, summary)


@router.get("/industries")
async def api_industries(trade_date: Optional[str] = None, limit: int = Query(31, ge=1, le=50)):
    """获取申万行业排名"""
    target_date = normalize_trade_date(trade_date, latest_trade_date=get_latest_trade_date())
    
    summary = get_summary(target_date)
    return build_industry_ranking_payload(target_date, summary, limit=limit)


@router.get("/industry-flow")
async def api_industry_flow(trade_date: Optional[str] = None):
    """获取行业资金流向"""
    target_date = normalize_trade_date(trade_date, latest_trade_date=get_latest_trade_date())
    
    summary = get_summary(target_date)
    return build_industry_flow_payload(target_date, summary)


@router.get("/limit-stats")
async def api_limit_stats(trade_date: Optional[str] = None):
    """获取涨跌停统计"""
    target_date = normalize_trade_date(trade_date, latest_trade_date=get_latest_trade_date())
    
    summary = get_summary(target_date)
    return build_limit_stats_payload(target_date, summary)


@router.get("/amount-trend")
async def api_amount_trend(days: int = Query(30, ge=7, le=90)):
    """获取成交额趋势"""
    cache_key = f"amount_trend:{days}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    result = get_amount_trend(days)
    
    cache.set(cache_key, result, ttl=300)
    return result


@router.get("/limit-trend")
async def api_limit_trend(days: int = Query(30, ge=7, le=90)):
    """获取涨停趋势"""
    cache_key = f"limit_trend:{days}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    result = get_limit_trend(days)
    
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
    
    result = get_kline(ts_code, limit)
    
    cache.set(cache_key, result, ttl=300)
    return result


@router.get("/search")
async def api_search(
    keyword: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50)
):
    """搜索股票"""
    return search_stocks(keyword, limit)


@router.post("/precompute/{trade_date}")
async def api_precompute(trade_date: str):
    """手动触发预计算"""
    target_date = trade_date.replace("-", "")
    try:
        precompute_and_save(target_date)
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


@router.post("/sync-update/{trade_date}")
async def api_sync_update(trade_date: str):
    """预计算最新交易日并通知前端刷新"""
    try:
        return await sync_market_data_update(trade_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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

    result = get_stock_detail(ts_code, target_date)
    
    cache.set(cache_key, result, ttl=300)
    return result


@router.get("/company/{ts_code}")
async def api_company_info(ts_code: str):
    """获取公司基础信息"""
    cache_key = f"company:{ts_code}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    result = get_company_info(ts_code)
    if not result:
        raise HTTPException(status_code=404, detail="Stock not found")
    
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
    target_date = normalize_trade_date(trade_date, latest_trade_date=get_latest_trade_date())
    if target_date is None:
        raise HTTPException(status_code=404, detail="No data available")
    
    cache_key = f"sectors_enhanced:{target_date}:{top}:{filter_type}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    result = get_sectors_enhanced(target_date, top=top, filter_type=filter_type)
    
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
    target_date = normalize_trade_date(trade_date, latest_trade_date=get_latest_trade_date())
    if target_date is None:
        raise HTTPException(status_code=404, detail="No data available")
    
    cache_key = f"industries_enhanced:{target_date}:{top}:{order}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    result = get_industries_enhanced(target_date, top=top, order=order)
    
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
    target_date = normalize_trade_date(trade_date, latest_trade_date=get_latest_trade_date())
    if target_date is None:
        raise HTTPException(status_code=404, detail="No data available")
    
    cache_key = f"ranking_enhanced:{target_date}:{sort_by}:{order}:{market}:{industry}:{top}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    result = get_ranking_enhanced(target_date, sort_by, order, market, industry, top)
    
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
    
    result = get_industry_detail(industry, target_date, kline_limit)
    
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
    
    result = get_industry_stocks(industry, target_date, order, limit)
    
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
    
    result = get_moneyflow(ts_code, target_date)
    
    cache.set(cache_key, result, ttl=300)
    return result
