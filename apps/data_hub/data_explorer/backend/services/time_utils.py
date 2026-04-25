from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

UTC = timezone.utc
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")
UTC_MIN = datetime.min.replace(tzinfo=UTC)
TIMESTAMP_PATTERNS = (
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
)


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def parse_timestamp(raw_value: object) -> datetime | None:
    if raw_value in {None, ""}:
        return None
    if isinstance(raw_value, datetime):
        return _to_utc(raw_value)

    value = str(raw_value).strip()
    if not value:
        return None
    if value.endswith("Z"):
        value = f"{value[:-1]}+00:00"

    try:
        return _to_utc(datetime.fromisoformat(value))
    except ValueError:
        pass

    for pattern in TIMESTAMP_PATTERNS:
        try:
            return _to_utc(datetime.strptime(value, pattern))
        except ValueError:
            continue
    return None


def format_shanghai_timestamp(raw_value: object) -> str | None:
    parsed = parse_timestamp(raw_value)
    if parsed is None:
        return None
    return parsed.astimezone(SHANGHAI_TZ).isoformat(timespec="seconds")
