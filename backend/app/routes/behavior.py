from fastapi import APIRouter, Depends

from app.analytics.behavior import fetch_behavior
from app.dependencies import require_compact_analytics
from app.schemas.responses import BehaviorResponse

router = APIRouter(tags=["Behavior"])


@router.get(
    "/behavior",
    response_model=BehaviorResponse,
    summary="Aggregated visitor behavior metrics",
)
def get_behavior(_: None = Depends(require_compact_analytics)) -> BehaviorResponse:
    return fetch_behavior()
