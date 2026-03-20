from __future__ import annotations

from fastapi import APIRouter

from apps.data_hub.data_explorer.backend.services.monitor_service import (
    get_monitor_overview,
    list_pipeline_run_rows,
    list_job_monitor_rows,
    list_table_monitor_rows,
)


router = APIRouter(prefix="/api/monitor", tags=["monitor"])


@router.get("/overview")
def get_overview() -> dict[str, object]:
    return get_monitor_overview()


@router.get("/tables")
def get_table_monitor() -> list[dict[str, object]]:
    return list_table_monitor_rows()


@router.get("/jobs")
def get_job_monitor() -> list[dict[str, object]]:
    return list_job_monitor_rows()


@router.get("/runs")
def get_pipeline_runs() -> list[dict[str, object]]:
    return list_pipeline_run_rows()
