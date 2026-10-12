from __future__ import annotations

from pymongo.collection import Collection

from app.analytics.common import pct, safe_divide
from app.database.mongodb import get_analytics_global_document
from app.schemas.responses import FunnelResponse, FunnelStage

FUNNEL_METHODOLOGY = (
    "Visitor-based funnel: each stage counts unique visitorids with at least one "
    "event of that type (view, addtocart, transaction). Percentages are relative "
    "to visitors with at least one view. Drop-off is the percentage decrease "
    "from the previous stage count to the current stage count."
)


def fetch_funnel(_events: Collection | None = None) -> FunnelResponse:
    funnel = get_analytics_global_document()["funnel"]
    view_count = funnel["view_visitors"]
    cart_count = funnel["addtocart_visitors"]
    tx_count = funnel["transaction_visitors"]
    base = view_count if view_count > 0 else 1

    stages_raw = [
        ("View", view_count),
        ("Add to Cart", cart_count),
        ("Transaction", tx_count),
    ]

    stages: list[FunnelStage] = []
    previous_count: int | None = None
    for name, count in stages_raw:
        dropoff = None
        if previous_count is not None and previous_count > 0:
            dropoff = round(
                safe_divide(previous_count - count, previous_count) * 100,
                4,
            )
        stages.append(
            FunnelStage(
                stage=name,
                count=count,
                percentage=pct(count, base),
                dropoff_from_previous=dropoff,
            )
        )
        previous_count = count

    return FunnelResponse(
        methodology=FUNNEL_METHODOLOGY,
        funnel_type="visitor",
        stages=stages,
    )
