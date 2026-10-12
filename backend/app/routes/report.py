from fastapi import APIRouter, Depends

from app.analytics.report import fetch_report
from app.database.mongodb import get_product_metrics_collection
from app.dependencies import require_compact_analytics
from app.schemas.responses import ReportResponse

router = APIRouter(tags=["Report"])


@router.get(
    "/report",
    response_model=ReportResponse,
    summary="Full aggregated analytics report",
)
def get_report(_: None = Depends(require_compact_analytics)) -> ReportResponse:
    return fetch_report(get_product_metrics_collection())
