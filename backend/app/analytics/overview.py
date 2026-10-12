from __future__ import annotations

from app.database.mongodb import get_analytics_global_document
from app.schemas.responses import (
    DateRange,
    EventDistributionItem,
    OverviewResponse,
)


def fetch_overview(_events_unused=None) -> OverviewResponse:
    overview = get_analytics_global_document()["overview"]
    distribution = [
        EventDistributionItem(
            event=item["event"],
            count=item["count"],
            percentage=item["percentage"],
        )
        for item in overview["event_distribution"]
    ]
    date_range = overview["date_range"]
    return OverviewResponse(
        total_events=overview["total_events"],
        unique_visitors=overview["unique_visitors"],
        unique_products=overview["unique_products"],
        total_views=overview["total_views"],
        total_add_to_cart=overview["total_add_to_cart"],
        total_transactions=overview["total_transactions"],
        visitor_conversion_rate=overview["visitor_conversion_rate"],
        date_range=DateRange(start=date_range["start"], end=date_range["end"]),
        event_distribution=distribution,
    )
