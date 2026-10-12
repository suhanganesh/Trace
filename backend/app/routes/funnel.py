from fastapi import APIRouter, Depends

from app.analytics.funnel import fetch_funnel
from app.dependencies import require_compact_analytics
from app.schemas.responses import FunnelResponse

router = APIRouter(tags=["Funnel"])


@router.get(
    "/funnel",
    response_model=FunnelResponse,
    summary="Visitor-based conversion funnel",
)
def get_funnel(_: None = Depends(require_compact_analytics)) -> FunnelResponse:
    return fetch_funnel()
