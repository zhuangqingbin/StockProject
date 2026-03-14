from ...infrastructure.database import engine
from .application import (
    build_amount_trend_rows,
    build_industries_enhanced_payload,
    build_limit_trend_rows,
    build_north_money_trend_rows,
    build_sectors_enhanced_payload,
    build_top_list_rows,
)
from .repository import MarketSummaryQueryRepository


repository = MarketSummaryQueryRepository(engine=engine)


def build_north_money_trend_response(repository: MarketSummaryQueryRepository, days: int) -> list:
    return build_north_money_trend_rows(repository.load_north_money_trend_rows(days))


def build_top_list_response(repository: MarketSummaryQueryRepository, trade_date: str, limit: int) -> list:
    return build_top_list_rows(repository.load_top_list_rows(trade_date, limit))


def build_amount_trend_response(repository: MarketSummaryQueryRepository, days: int) -> list:
    return build_amount_trend_rows(repository.load_amount_trend_rows(days))


def build_limit_trend_response(repository: MarketSummaryQueryRepository, days: int) -> list:
    return build_limit_trend_rows(repository.load_limit_trend_rows(days))


def build_sectors_enhanced_response(
    repository: MarketSummaryQueryRepository,
    trade_date: str,
    top: int,
    filter_type: str,
) -> dict:
    rows = repository.load_sectors_enhanced_rows(trade_date)
    return build_sectors_enhanced_payload(trade_date, rows, top=top, filter_type=filter_type)


def build_industries_enhanced_response(
    repository: MarketSummaryQueryRepository,
    trade_date: str,
    top: int,
    order: str,
) -> dict:
    rows = repository.load_industries_enhanced_rows(trade_date, top, order)
    return build_industries_enhanced_payload(trade_date, rows, order=order)


def get_north_money_trend(days: int) -> list:
    return build_north_money_trend_response(repository, days)


def get_top_list(trade_date: str, limit: int) -> list:
    return build_top_list_response(repository, trade_date, limit)


def get_amount_trend(days: int) -> list:
    return build_amount_trend_response(repository, days)


def get_limit_trend(days: int) -> list:
    return build_limit_trend_response(repository, days)


def get_sectors_enhanced(trade_date: str, top: int, filter_type: str) -> dict:
    return build_sectors_enhanced_response(repository, trade_date, top, filter_type)


def get_industries_enhanced(trade_date: str, top: int, order: str) -> dict:
    return build_industries_enhanced_response(repository, trade_date, top, order)
