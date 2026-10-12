from fastapi import APIRouter, Depends

from app.analytics.overview import fetch_overview
from app.dependencies import require_compact_analytics
from app.schemas.responses import OverviewResponse

router = APIRouter(tags=["Overview"])


@router.get(
    "/overview",
    response_model=OverviewResponse,
    summary="Global KPIs and event distribution",
)
def get_overview(_: None = Depends(require_compact_analytics)) -> OverviewResponse:
    return fetch_overview()
