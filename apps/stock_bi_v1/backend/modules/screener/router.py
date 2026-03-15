from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from apps.stock_bi_v1.backend.models.api_models import ScreenerRequest
from apps.stock_bi_v1.backend.modules.screener import service


router = APIRouter(prefix="/api/screener", tags=["screener"])


@router.get("/filters")
def screener_filters():
    return service.get_filters()


@router.post("/query")
def screener_query(request: ScreenerRequest):
    return service.query(request)


@router.post("/export")
def screener_export(request: ScreenerRequest):
    payload = service.export_csv(request)
    return StreamingResponse(
        iter([payload.encode("utf-8")]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=stock-bi-v1-screener.csv"},
    )
