from __future__ import annotations

from datetime import date, datetime
from typing import Any
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from apps.stock_backtest.backend.models.db_models import RunStatus, StrategySourceType, TradeDirection


class StrategyTemplateResponse(BaseModel):
    template_id: str
    name: str
    description: str
    required_feeds: list[str]
    parameters: dict[str, dict[str, Any]]
    source_code: str


class StrategyCreateRequest(BaseModel):
    name: str
    description: str = ""
    source_type: StrategySourceType
    template_id: Optional[str] = None
    code: Optional[str] = None
    default_params: dict[str, Any] = Field(default_factory=dict)
    required_feeds: list[str] = Field(default_factory=list)
    author: str = "system"


class StrategyUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    template_id: Optional[str] = None
    code: Optional[str] = None
    default_params: Optional[dict[str, Any]] = None
    required_feeds: Optional[list[str]] = None


class StrategyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    source_type: StrategySourceType
    template_id: Optional[str]
    code: Optional[str]
    default_params: dict[str, Any]
    required_feeds: list[str]
    author: str
    created_at: datetime
    updated_at: datetime


class BacktestRunCreateRequest(BaseModel):
    strategy_id: int
    params: dict[str, Any] = Field(default_factory=dict)
    symbols: list[str]
    start_date: date
    end_date: date
    initial_cash: float
    commission_rate: float
    benchmark: str = ""
    data_feeds: list[str] = Field(default_factory=list)
    grid_search_group_id: Optional[str] = None
    submitted_by: str = "system"


class BacktestRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    strategy_id: int
    params: dict[str, Any]
    symbols: list[str]
    start_date: date
    end_date: date
    initial_cash: float
    commission_rate: float
    benchmark: str
    data_feeds: list[str]
    request_signature: str
    status: RunStatus
    progress: int
    cache_hit: bool
    reused_from_run_id: Optional[int]
    error_message: Optional[str]
    total_return: Optional[float]
    annual_return: Optional[float]
    max_drawdown: Optional[float]
    sharpe_ratio: Optional[float]
    win_rate: Optional[float]
    profit_loss_ratio: Optional[float]
    metrics: dict[str, Any]
    grid_search_group_id: Optional[str]
    submitted_by: str
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]


class BacktestSubmissionResponse(BaseModel):
    run_id: int
    status: RunStatus
    cache_hit: bool
    reused_from_run_id: Optional[int] = None


class BacktestRunEventResponse(BaseModel):
    timestamp: datetime
    stage: str
    message: str
    progress: Optional[int] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BacktestRunDiagnosticsResponse(BaseModel):
    run_id: int
    status: RunStatus
    request_signature: str
    cache_hit: bool
    reused_from_run_id: Optional[int] = None
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    events: list[BacktestRunEventResponse] = Field(default_factory=list)


class BacktestRuntimeSummaryResponse(BaseModel):
    execution_mode: str
    max_workers: int
    active_run_ids: list[int] = Field(default_factory=list)
    status_counts: dict[str, int] = Field(default_factory=dict)
    cache_hits: int = 0


class BacktestTradeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    trade_date: date
    symbol: str
    direction: TradeDirection
    price: float
    size: int
    commission: float
    pnl: float


class BacktestDailyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    trade_date: date
    portfolio_value: float
    cash: float
    daily_return: float
    cumulative_return: float
    drawdown: float


class FeedCatalogResponse(BaseModel):
    feed_id: str
    label: str
    description: str
    table_name: str
    primary: bool = False


class FeedHealthResponse(FeedCatalogResponse):
    record_count: int
    symbol_count: int
    earliest_trade_date: Optional[date] = None
    latest_trade_date: Optional[date] = None


class IndustryCoverageResponse(BaseModel):
    industry: str
    symbol_count: int


class DataOverviewResponse(BaseModel):
    symbol_count: int
    industry_count: int
    benchmark_count: int
    feed_health: list[FeedHealthResponse] = Field(default_factory=list)
    top_industries: list[IndustryCoverageResponse] = Field(default_factory=list)


class BenchmarkResponse(BaseModel):
    ts_code: str
    name: str
    latest_trade_date: Optional[date] = None


class SymbolSearchResponse(BaseModel):
    ts_code: str
    name: Optional[str] = None
    industry: Optional[str] = None
    market: Optional[str] = None


class SeedSymbolRecord(BaseModel):
    ts_code: str
    name: Optional[str] = None
    industry: Optional[str] = None
    market: Optional[str] = None


class SeedDailyKlineRecord(BaseModel):
    ts_code: str
    trade_date: date
    open: float
    high: float
    low: float
    close: float
    vol: float = 0
    amount: Optional[float] = None


class SeedMarketPayload(BaseModel):
    symbols: list[SeedSymbolRecord] = Field(default_factory=list)
    daily_kline: list[SeedDailyKlineRecord] = Field(default_factory=list)
