from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum as SqlEnum, Float, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from apps.stock_backtest.backend.infrastructure.database import Base


JSONType = JSON().with_variant(SQLiteJSON, "sqlite")


class StrategySourceType(str, Enum):
    TEMPLATE = "template"
    CUSTOM = "custom"


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TradeDirection(str, Enum):
    BUY = "buy"
    SELL = "sell"


class StrategyModel(Base):
    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_type: Mapped[StrategySourceType] = mapped_column(SqlEnum(StrategySourceType), nullable=False)
    template_id: Mapped[Optional[str]] = mapped_column(String(50))
    code: Mapped[Optional[str]] = mapped_column(Text)
    default_params: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    required_feeds: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    author: Mapped[str] = mapped_column(String(50), default="system", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    runs: Mapped[list["BacktestRunModel"]] = relationship(back_populates="strategy", cascade="all, delete-orphan")


class BacktestRunModel(Base):
    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategies.id"), nullable=False, index=True)
    params: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    symbols: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    initial_cash: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    commission_rate: Mapped[float] = mapped_column(Numeric(8, 6), nullable=False)
    benchmark: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    data_feeds: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    request_signature: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[RunStatus] = mapped_column(SqlEnum(RunStatus), default=RunStatus.PENDING, nullable=False, index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reused_from_run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("backtest_runs.id"), index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    total_return: Mapped[Optional[float]] = mapped_column(Numeric(12, 6))
    annual_return: Mapped[Optional[float]] = mapped_column(Numeric(12, 6), index=True)
    max_drawdown: Mapped[Optional[float]] = mapped_column(Numeric(12, 6))
    sharpe_ratio: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    win_rate: Mapped[Optional[float]] = mapped_column(Numeric(6, 4))
    profit_loss_ratio: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    metrics: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    diagnostics: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    grid_search_group_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    submitted_by: Mapped[str] = mapped_column(String(50), default="system", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    strategy: Mapped["StrategyModel"] = relationship(back_populates="runs")
    trades: Mapped[list["BacktestTradeModel"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    daily_snapshots: Mapped[list["BacktestDailyModel"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class BacktestTradeModel(Base):
    __tablename__ = "backtest_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("backtest_runs.id"), nullable=False, index=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[TradeDirection] = mapped_column(SqlEnum(TradeDirection), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    commission: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    pnl: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0)

    run: Mapped["BacktestRunModel"] = relationship(back_populates="trades")


class BacktestDailyModel(Base):
    __tablename__ = "backtest_daily"
    __table_args__ = (UniqueConstraint("run_id", "trade_date", name="uq_backtest_daily_run_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("backtest_runs.id"), nullable=False, index=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    portfolio_value: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    cash: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    daily_return: Mapped[float] = mapped_column(Numeric(12, 8), nullable=False, default=0)
    cumulative_return: Mapped[float] = mapped_column(Numeric(12, 8), nullable=False, default=0)
    drawdown: Mapped[float] = mapped_column(Numeric(12, 8), nullable=False, default=0)

    run: Mapped["BacktestRunModel"] = relationship(back_populates="daily_snapshots")


class MarketStockBasicModel(Base):
    __tablename__ = "stock_basic"

    ts_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(100))
    industry: Mapped[Optional[str]] = mapped_column(String(100))
    market: Mapped[Optional[str]] = mapped_column(String(50))


class MarketDailyKlineModel(Base):
    __tablename__ = "daily_kline"

    ts_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    trade_date: Mapped[date] = mapped_column(Date, primary_key=True)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    vol: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    amount: Mapped[Optional[float]] = mapped_column(Float)


class MarketDailyBasicModel(Base):
    __tablename__ = "daily_basic"

    ts_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    trade_date: Mapped[date] = mapped_column(Date, primary_key=True)
    turnover_rate: Mapped[Optional[float]] = mapped_column(Float)
    pe_ttm: Mapped[Optional[float]] = mapped_column(Float)


class MarketMoneyflowModel(Base):
    __tablename__ = "moneyflow"

    ts_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    trade_date: Mapped[date] = mapped_column(Date, primary_key=True)
    net_mf_amount: Mapped[Optional[float]] = mapped_column(Float)


class MarketIndexDailyModel(Base):
    __tablename__ = "index_daily"

    ts_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    trade_date: Mapped[date] = mapped_column(Date, primary_key=True)
    close: Mapped[Optional[float]] = mapped_column(Float)


class MarketTopListModel(Base):
    __tablename__ = "top_list"

    ts_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    trade_date: Mapped[date] = mapped_column(Date, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(100))
    net_amount: Mapped[Optional[float]] = mapped_column(Float)
