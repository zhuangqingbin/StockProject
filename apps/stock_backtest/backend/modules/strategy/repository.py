from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional

from apps.stock_backtest.backend.models.db_models import StrategyModel


class StrategyRepository:
    def __init__(self, session: Session):
        self.session = session

    def list(self, author: Optional[str] = None) -> list[StrategyModel]:
        statement = select(StrategyModel).order_by(StrategyModel.updated_at.desc(), StrategyModel.id.desc())
        if author:
            statement = statement.where(StrategyModel.author == author)
        return list(self.session.execute(statement).scalars().all())

    def exists_any(self) -> bool:
        statement = select(StrategyModel.id).limit(1)
        return self.session.execute(statement).scalar_one_or_none() is not None

    def get(self, strategy_id: int) -> Optional[StrategyModel]:
        return self.session.get(StrategyModel, strategy_id)

    def get_by_template_id(self, template_id: str) -> Optional[StrategyModel]:
        statement = select(StrategyModel).where(StrategyModel.template_id == template_id).limit(1)
        return self.session.execute(statement).scalar_one_or_none()

    def create(self, payload: dict) -> StrategyModel:
        strategy = StrategyModel(**payload)
        self.session.add(strategy)
        self.session.commit()
        self.session.refresh(strategy)
        return strategy

    def update(self, strategy: StrategyModel, payload: dict) -> StrategyModel:
        for key, value in payload.items():
            setattr(strategy, key, value)
        self.session.add(strategy)
        self.session.commit()
        self.session.refresh(strategy)
        return strategy

    def delete(self, strategy: StrategyModel) -> None:
        self.session.delete(strategy)
        self.session.commit()
