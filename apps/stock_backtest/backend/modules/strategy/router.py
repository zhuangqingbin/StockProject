from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session
from typing import Optional

from apps.stock_backtest.backend.infrastructure.database import get_db_session
from apps.stock_backtest.backend.models.api_models import StrategyCreateRequest, StrategyResponse, StrategyTemplateResponse, StrategyUpdateRequest

from .repository import StrategyRepository
from .service import create_strategy, get_strategy_or_404, get_template_payload, list_template_payloads, update_strategy


router = APIRouter(prefix="/api/strategies", tags=["strategies"])


@router.get("", response_model=list[StrategyResponse])
def list_strategies(author: Optional[str] = Query(default=None), session: Session = Depends(get_db_session)):
    repository = StrategyRepository(session)
    return repository.list(author=author)


@router.get("/templates", response_model=list[StrategyTemplateResponse])
def list_strategy_templates():
    return list_template_payloads()


@router.get("/templates/{template_id}", response_model=StrategyTemplateResponse)
def get_strategy_template_detail(template_id: str):
    return get_template_payload(template_id)


@router.get("/{strategy_id}", response_model=StrategyResponse)
def get_strategy(strategy_id: int, session: Session = Depends(get_db_session)):
    return get_strategy_or_404(session, strategy_id)


@router.post("", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
def create_strategy_route(payload: StrategyCreateRequest, session: Session = Depends(get_db_session)):
    return create_strategy(session, payload)


@router.put("/{strategy_id}", response_model=StrategyResponse)
def update_strategy_route(strategy_id: int, payload: StrategyUpdateRequest, session: Session = Depends(get_db_session)):
    return update_strategy(session, strategy_id, payload)


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy(strategy_id: int, session: Session = Depends(get_db_session)):
    repository = StrategyRepository(session)
    strategy = get_strategy_or_404(session, strategy_id)
    repository.delete(strategy)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
