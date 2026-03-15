from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from apps.stock_backtest.backend.engine.strategy_loader import get_strategy_template, list_strategy_templates
from apps.stock_backtest.backend.models.api_models import StrategyCreateRequest, StrategyUpdateRequest
from apps.stock_backtest.backend.models.db_models import StrategySourceType

from .repository import StrategyRepository


def list_template_payloads() -> list[dict]:
    return [
        {
            "template_id": template.template_id,
            "name": template.name,
            "description": template.description,
            "required_feeds": template.required_feeds,
            "parameters": template.parameters,
            "source_code": template.source_code,
        }
        for template in list_strategy_templates()
    ]


def get_template_payload(template_id: str) -> dict:
    template = get_strategy_template(template_id)
    return {
        "template_id": template.template_id,
        "name": template.name,
        "description": template.description,
        "required_feeds": template.required_feeds,
        "parameters": template.parameters,
        "source_code": template.source_code,
    }


def create_strategy(session: Session, payload: StrategyCreateRequest):
    repository = StrategyRepository(session)
    strategy_payload = payload.model_dump()

    if payload.source_type == StrategySourceType.TEMPLATE:
        if not payload.template_id:
            raise HTTPException(status_code=400, detail="template_id is required for template strategies")
        template = get_strategy_template(payload.template_id)
        strategy_payload["required_feeds"] = payload.required_feeds or template.required_feeds
        strategy_payload["code"] = None
    else:
        if not payload.code:
            raise HTTPException(status_code=400, detail="code is required for custom strategies")

    return repository.create(strategy_payload)


def update_strategy(session: Session, strategy_id: int, payload: StrategyUpdateRequest):
    repository = StrategyRepository(session)
    strategy = repository.get(strategy_id)
    if strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    update_payload = {key: value for key, value in payload.model_dump().items() if value is not None}
    return repository.update(strategy, update_payload)


def get_strategy_or_404(session: Session, strategy_id: int):
    repository = StrategyRepository(session)
    strategy = repository.get(strategy_id)
    if strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


def ensure_default_strategies(session: Session) -> None:
    repository = StrategyRepository(session)

    for template in list_strategy_templates():
        if repository.get_by_template_id(template.template_id) is not None:
            continue
        repository.create(
            {
                "name": template.name,
                "description": template.description,
                "source_type": StrategySourceType.TEMPLATE,
                "template_id": template.template_id,
                "code": None,
                "default_params": {key: value.get("default") for key, value in template.parameters.items()},
                "required_feeds": template.required_feeds,
                "author": "system",
            }
        )
