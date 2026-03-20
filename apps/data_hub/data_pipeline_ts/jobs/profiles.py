from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class ProfileId(StrEnum):
    TRADE_DAY_PRE_OPEN = "trade_day_pre_open"
    TRADE_DAY_POST_CLOSE_CORE = "trade_day_post_close_core"
    TRADE_DAY_POST_CLOSE_EXTENDED = "trade_day_post_close_extended"
    REFERENCE_TRADE_DAY_POST_CLOSE = "reference_trade_day_post_close"
    FINANCIAL_CALENDAR_NIGHTLY = "financial_calendar_nightly"
    REFERENCE_CALENDAR_NIGHTLY = "reference_calendar_nightly"
    MANUAL = "manual"


@dataclass(frozen=True)
class ProfileSpec:
    id: ProfileId
    cron: str | None
    execution_mode: Literal["parallel", "serial"] = "parallel"
    backfill_mode: Literal["trade_day", "calendar_day", "manual"] = "trade_day"


PROFILE_SPECS = {
    ProfileId.TRADE_DAY_PRE_OPEN: ProfileSpec(
        id=ProfileId.TRADE_DAY_PRE_OPEN,
        cron="25 9 * * *",
        execution_mode="parallel",
        backfill_mode="trade_day",
    ),
    ProfileId.TRADE_DAY_POST_CLOSE_CORE: ProfileSpec(
        id=ProfileId.TRADE_DAY_POST_CLOSE_CORE,
        cron="0 18 * * *",
        execution_mode="parallel",
        backfill_mode="trade_day",
    ),
    ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED: ProfileSpec(
        id=ProfileId.TRADE_DAY_POST_CLOSE_EXTENDED,
        cron="35 18 * * *",
        execution_mode="parallel",
        backfill_mode="trade_day",
    ),
    ProfileId.REFERENCE_TRADE_DAY_POST_CLOSE: ProfileSpec(
        id=ProfileId.REFERENCE_TRADE_DAY_POST_CLOSE,
        cron="40 18 * * *",
        execution_mode="parallel",
        backfill_mode="trade_day",
    ),
    ProfileId.FINANCIAL_CALENDAR_NIGHTLY: ProfileSpec(
        id=ProfileId.FINANCIAL_CALENDAR_NIGHTLY,
        cron="30 21 * * *",
        execution_mode="parallel",
        backfill_mode="calendar_day",
    ),
    ProfileId.REFERENCE_CALENDAR_NIGHTLY: ProfileSpec(
        id=ProfileId.REFERENCE_CALENDAR_NIGHTLY,
        cron="45 21 * * *",
        execution_mode="parallel",
        backfill_mode="calendar_day",
    ),
    ProfileId.MANUAL: ProfileSpec(
        id=ProfileId.MANUAL,
        cron=None,
        execution_mode="serial",
        backfill_mode="manual",
    ),
}

SCHEDULED_PROFILES = tuple(
    PROFILE_SPECS[profile]
    for profile in ProfileId
    if PROFILE_SPECS[profile].cron is not None
)
PROFILE_NAMES = tuple(profile.value for profile in ProfileId)
