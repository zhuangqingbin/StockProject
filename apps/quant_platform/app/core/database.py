from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Index
from datetime import datetime

from .config import DATABASE_URL, DEBUG

engine = create_async_engine(DATABASE_URL, echo=DEBUG)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class StockBasic(Base):
    __tablename__ = "stock_basic"
    ts_code = Column(String(20), primary_key=True)
    symbol = Column(String(10))
    name = Column(String(50))
    area = Column(String(20))
    industry = Column(String(50))
    market = Column(String(20))
    list_date = Column(String(10))
    list_status = Column(String(2))


class StockDaily(Base):
    __tablename__ = "stock_daily"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), index=True)
    trade_date = Column(String(10), index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    pre_close = Column(Float)
    change = Column(Float)
    pct_chg = Column(Float)
    vol = Column(Float)
    amount = Column(Float)

    __table_args__ = (
        Index("ix_daily_code_date", "ts_code", "trade_date", unique=True),
    )


class StockDailyBasic(Base):
    __tablename__ = "stock_daily_basic"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), index=True)
    trade_date = Column(String(10), index=True)
    turnover_rate = Column(Float)
    volume_ratio = Column(Float)
    pe = Column(Float)
    pe_ttm = Column(Float)
    pb = Column(Float)
    ps = Column(Float)
    ps_ttm = Column(Float)
    dv_ratio = Column(Float)
    dv_ttm = Column(Float)
    total_share = Column(Float)
    float_share = Column(Float)
    total_mv = Column(Float)
    circ_mv = Column(Float)

    __table_args__ = (
        Index("ix_basic_code_date", "ts_code", "trade_date", unique=True),
    )


class BacktestResult(Base):
    __tablename__ = "backtest_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    strategy = Column(String(50))
    params = Column(Text)
    ts_code = Column(String(20))
    start_date = Column(String(10))
    end_date = Column(String(10))
    initial_capital = Column(Float)
    final_capital = Column(Float)
    total_return = Column(Float)
    annual_return = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)
    trade_count = Column(Integer)
    result_data = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
