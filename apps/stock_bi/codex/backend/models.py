"""
数据库模型定义
"""
from sqlalchemy import Column, String, Float, Date, DateTime, Integer, Text
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

from .infrastructure.database import Base


# ==================== SQLAlchemy 模型 ====================

class DailyKline(Base):
    """日K线数据模型"""
    __tablename__ = "daily_kline"
    
    ts_code = Column(String(10), primary_key=True)
    trade_date = Column(Date, primary_key=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    change_val = Column(Float)
    pct_chg = Column(Float)
    vol = Column(Float)
    amount = Column(Float)


class StockBasic(Base):
    """股票基础信息模型"""
    __tablename__ = "stock_basic"
    
    ts_code = Column(String(10), primary_key=True)
    symbol = Column(String(10))
    name = Column(String(50))
    area = Column(String(20))
    industry = Column(String(50))
    market = Column(String(20))
    list_date = Column(Date)
    exchange = Column(String(10))
    is_hs = Column(String(5))
    update_time = Column(DateTime, default=func.now())


# ==================== Pydantic 响应模型 ====================

class StockKlineResponse(BaseModel):
    """K线数据响应"""
    ts_code: str
    trade_date: date
    open: float
    high: float
    low: float
    close: float
    change_val: Optional[float]
    pct_chg: Optional[float]
    vol: Optional[float]
    amount: Optional[float]
    
    class Config:
        from_attributes = True


class StockBasicResponse(BaseModel):
    """股票基础信息响应"""
    ts_code: str
    symbol: Optional[str]
    name: Optional[str]
    area: Optional[str]
    industry: Optional[str]
    market: Optional[str]
    
    class Config:
        from_attributes = True


class MarketOverviewResponse(BaseModel):
    """市场概览响应"""
    trade_date: date
    total_stocks: int
    up_count: int
    down_count: int
    flat_count: int
    limit_up: int
    limit_down: int
    total_amount: float
    avg_pct_chg: float


class RankingItem(BaseModel):
    """排行榜项"""
    ts_code: str
    name: Optional[str]
    industry: Optional[str]
    market: Optional[str]
    pct_chg: float
    close: float
    amount: float
    vol: float


class SectorStatsResponse(BaseModel):
    """板块统计响应"""
    sector: str
    avg_pct_chg: float
    total_amount: float
    stock_count: int
    up_count: int
    down_count: int


class PctChgDistribution(BaseModel):
    """涨跌幅分布"""
    range_start: float
    range_end: float
    count: int


class ChatRequest(BaseModel):
    """Chat 请求"""
    message: str
    context: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    """Chat 响应"""
    reply: str
    chart_config: Optional[dict] = None
    data: Optional[List[dict]] = None
    sql: Optional[str] = None
