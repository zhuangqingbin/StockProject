from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from typing import Optional

from apps.stock_backtest.backend.models.db_models import BacktestRunModel, RunStatus


class BacktestRunRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, payload: dict) -> BacktestRunModel:
        run = BacktestRunModel(**payload)
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def get(self, run_id: int) -> Optional[BacktestRunModel]:
        return self.session.get(BacktestRunModel, run_id)

    def find_completed_by_signature(self, request_signature: str) -> Optional[BacktestRunModel]:
        statement = (
            select(BacktestRunModel)
            .where(
                BacktestRunModel.request_signature == request_signature,
                BacktestRunModel.status == RunStatus.COMPLETED,
            )
            .order_by(BacktestRunModel.cache_hit.asc(), BacktestRunModel.id.asc())
        )
        return self.session.execute(statement).scalars().first()

    def list(self, strategy_id: Optional[int] = None, status: Optional[RunStatus] = None) -> list[BacktestRunModel]:
        statement = select(BacktestRunModel).order_by(BacktestRunModel.created_at.desc(), BacktestRunModel.id.desc())
        if strategy_id is not None:
            statement = statement.where(BacktestRunModel.strategy_id == strategy_id)
        if status is not None:
            statement = statement.where(BacktestRunModel.status == status)
        return list(self.session.execute(statement).scalars().all())

    def build_status_counts(self) -> dict[str, int]:
        counts = {status.value: 0 for status in RunStatus}
        statement = select(BacktestRunModel.status, func.count(BacktestRunModel.id)).group_by(BacktestRunModel.status)
        for status, count in self.session.execute(statement).all():
            counts[status.value] = int(count)
        return counts

    def count_cache_hits(self) -> int:
        statement = select(func.count(BacktestRunModel.id)).where(BacktestRunModel.cache_hit.is_(True))
        return int(self.session.execute(statement).scalar_one())

    def delete(self, run: BacktestRunModel) -> None:
        self.session.delete(run)
        self.session.commit()
