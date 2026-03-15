from __future__ import annotations

from datetime import datetime
from typing import Any


def build_run_event(
    stage: str,
    message: str,
    *,
    progress: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat(),
        "stage": stage,
        "message": message,
        "metadata": metadata or {},
    }
    if progress is not None:
        event["progress"] = progress
    return event


def append_run_event(
    run,
    stage: str,
    message: str,
    *,
    progress: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    events = list(run.diagnostics or [])
    events.append(build_run_event(stage, message, progress=progress, metadata=metadata))
    run.diagnostics = events
