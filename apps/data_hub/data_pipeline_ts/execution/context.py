from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Callable, Mapping, Sequence

from apps.data_hub.data_pipeline_ts.execution.calendar import get_trade_cal


TradeCalendarProvider = Callable[[str, str], Sequence[str]]


def _coerce_date(value: str | date | datetime | None) -> date:
    if value is None:
        return date.today()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def _compact(value: date) -> str:
    return value.strftime("%Y%m%d")


def _parse_compact(value: str) -> date:
    return datetime.strptime(value, "%Y%m%d").date()


@dataclass(frozen=True)
class ExecutionContext:
    as_of_date: date
    trade_date: date

    @classmethod
    def for_as_of(
        cls,
        as_of: str | date | datetime | None = None,
        trade_calendar_provider: TradeCalendarProvider = get_trade_cal,
        lookback_days: int = 14,
    ) -> "ExecutionContext":
        as_of_date = _coerce_date(as_of)
        start_date = as_of_date - timedelta(days=lookback_days)
        open_days = list(trade_calendar_provider(_compact(start_date), _compact(as_of_date)))
        eligible_days = [day for day in open_days if day <= _compact(as_of_date)]
        if not eligible_days:
            raise ValueError(f"No open trade date found for as_of={as_of_date.isoformat()}")
        return cls(as_of_date=as_of_date, trade_date=_parse_compact(max(eligible_days)))

    def variables(self) -> dict[str, str]:
        return {
            "current_dt": self.as_of_date.isoformat(),
            "current_date": _compact(self.as_of_date),
            "trade_dt": self.trade_date.isoformat(),
            "trade_date": _compact(self.trade_date),
        }

    def render_value(self, value: Any) -> Any:
        if not isinstance(value, str):
            return value

        rendered = value
        for key, replacement in self.variables().items():
            rendered = rendered.replace(f"{{{{ {key} }}}}", replacement)
            rendered = rendered.replace(f"{{{{{key}}}}}", replacement)
            rendered = rendered.replace(f"{{{key}}}", replacement)
        return rendered

    def render_mapping(self, values: Mapping[str, Any]) -> dict[str, Any]:
        return {key: self.render_value(value) for key, value in values.items()}
