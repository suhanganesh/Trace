from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.analytics.common import parse_optional_date
from app.analytics.time_series import fetch_time_series
from app.dependencies import require_compact_analytics
from app.schemas.responses import TimeSeriesResponse

router = APIRouter(tags=["Time Series"])

GranularityParam = Literal["daily", "hourly"]


@router.get(
    "/time-series",
    response_model=TimeSeriesResponse,
    summary="Event activity over time",
)
def get_time_series(
    granularity: GranularityParam = Query("daily"),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    _: None = Depends(require_compact_analytics),
) -> TimeSeriesResponse:
    start = parse_optional_date(start_date, "start_date")
    end = parse_optional_date(end_date, "end_date")
    if start and end and start > end:
        raise HTTPException(status_code=422, detail="start_date must be on or before end_date.")
    return fetch_time_series(None, granularity, start, end)
