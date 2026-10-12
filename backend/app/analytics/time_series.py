from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pymongo.collection import Collection

from app.analytics.common import build_date_match
from app.database.mongodb import (
    get_time_series_daily_collection,
    get_time_series_hourly_collection,
)
from app.schemas.responses import TimeSeriesPoint, TimeSeriesResponse

Granularity = Literal["daily", "hourly"]


def fetch_time_series(
    _events: Collection | None,
    granularity: Granularity,
    start: date | None,
    end: date | None,
) -> TimeSeriesResponse:
    match_stage = build_date_match(start, end)
    pipeline: list[dict[str, Any]] = []
    if match_stage:
        pipeline.append({"$match": match_stage})

    if granularity == "daily":
        collection = get_time_series_daily_collection()
        pipeline.append({"$sort": {"date": 1}})
    else:
        collection = get_time_series_hourly_collection()
        pipeline.append({"$sort": {"date": 1, "hour": 1}})

    rows = list(collection.aggregate(pipeline))
    series: list[TimeSeriesPoint] = []
    for row in rows:
        if granularity == "daily":
            timestamp = row["date"]
        else:
            timestamp = f"{row['date']}T{int(row['hour']):02d}:00:00Z"
        series.append(
            TimeSeriesPoint(
                timestamp=timestamp,
                views=row["views"],
                addtocart=row["addtocart"],
                transactions=row["transactions"],
                total_events=row["total_events"],
            )
        )

    return TimeSeriesResponse(
        granularity=granularity,
        start_date=start.isoformat() if start else None,
        end_date=end.isoformat() if end else None,
        series=series,
    )
