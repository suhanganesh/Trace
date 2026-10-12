from __future__ import annotations

from pymongo.collection import Collection

from app.database.mongodb import get_analytics_global_document
from app.schemas.responses import (
    ActivityBucket,
    BehaviorResponse,
    BehaviorSummary,
    EngagementMetrics,
    TopVisitor,
)


def fetch_behavior(_events: Collection | None = None) -> BehaviorResponse:
    behavior = get_analytics_global_document()["behavior"]
    summary = behavior["summary"]
    return BehaviorResponse(
        summary=BehaviorSummary(**summary),
        activity_distribution=[ActivityBucket(**row) for row in behavior["activity_distribution"]],
        top_visitors=[TopVisitor(**row) for row in behavior["top_visitors"]],
        engagement_metrics=EngagementMetrics(**behavior["engagement_metrics"]),
    )
