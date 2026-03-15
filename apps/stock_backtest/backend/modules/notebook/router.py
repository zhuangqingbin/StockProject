from __future__ import annotations

from fastapi import APIRouter

from .service import get_notebook_status, list_notebook_templates, start_notebook, stop_notebook


router = APIRouter(prefix="/api/notebook", tags=["notebook"])


@router.post("/start")
def start_notebook_route():
    return start_notebook()


@router.post("/stop")
def stop_notebook_route():
    return stop_notebook()


@router.get("/status")
def get_notebook_status_route():
    return get_notebook_status()


@router.get("/templates")
def list_notebook_templates_route():
    return list_notebook_templates()


@router.get("/recent")
def list_recent_notebooks():
    return []
