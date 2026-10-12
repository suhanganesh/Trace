from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    database: str
    database_name: str


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None


class EventDistributionItem(BaseModel):
    event: str
    count: int
    percentage: float


class DateRange(BaseModel):
    start: str
    end: str


class OverviewResponse(BaseModel):
    total_events: int
    unique_visitors: int
    unique_products: int
    total_views: int
    total_add_to_cart: int
    total_transactions: int
    visitor_conversion_rate: float
    date_range: DateRange
    event_distribution: list[EventDistributionItem]


class FunnelStage(BaseModel):
    stage: str
    count: int
    percentage: float
    dropoff_from_previous: float | None = None


class FunnelResponse(BaseModel):
    methodology: str
    funnel_type: str
    stages: list[FunnelStage]


class BehaviorSummary(BaseModel):
    total_visitors: int
    total_events: int
    avg_events_per_visitor: float
    avg_views_per_visitor: float
    visitors_with_add_to_cart: int
    visitors_with_transaction: int
    repeat_visitors: int


class ActivityBucket(BaseModel):
    label: str
    min_events: int
    max_events: int | None
    visitor_count: int


class TopVisitor(BaseModel):
    visitor_id: int
    total_events: int
    views: int
    add_to_cart: int
    transactions: int


class EngagementMetrics(BaseModel):
    single_event_visitors: int
    multi_event_visitors: int
    pct_visitors_with_purchase: float


class BehaviorResponse(BaseModel):
    summary: BehaviorSummary
    activity_distribution: list[ActivityBucket]
    top_visitors: list[TopVisitor]
    engagement_metrics: EngagementMetrics


class ProductRow(BaseModel):
    rank: int
    item_id: int
    views: int
    add_to_cart: int
    transactions: int
    conversion_rate: float


class ProductListResponse(BaseModel):
    metric: str
    limit: int
    products: list[ProductRow]


class ProductOpportunity(BaseModel):
    item_id: int
    views: int
    transactions: int
    conversion_rate: float
    median_conversion_reference: float


class ProductDetailResponse(BaseModel):
    item_id: int
    views: int
    add_to_cart: int
    transactions: int
    conversion_rate: float
    properties: dict[str, Any] = Field(default_factory=dict)


class TimeSeriesPoint(BaseModel):
    timestamp: str
    views: int
    addtocart: int
    transactions: int
    total_events: int


class TimeSeriesResponse(BaseModel):
    granularity: str
    start_date: str | None
    end_date: str | None
    series: list[TimeSeriesPoint]


class KeyFinding(BaseModel):
    metric: str
    value: str
    interpretation: str


class ReportResponse(BaseModel):
    dataset_summary: dict[str, Any]
    engagement: dict[str, Any]
    conversion: dict[str, Any]
    product_performance: dict[str, Any]
    time_trends: dict[str, Any]
    key_findings: list[KeyFinding]


class DatasetInfoResponse(BaseModel):
    dataset_name: str
    processed_event_count: int
    item_property_count: int
    category_count: int
    unique_visitors: int | None
    unique_products: int | None
    event_counts: dict[str, int]
    transaction_count: int | None
    date_range: DateRange | None
    processing_information: dict[str, Any]
    database_status: str
