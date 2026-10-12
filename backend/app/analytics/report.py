from __future__ import annotations

from typing import Any

from pymongo.collection import Collection

from app.analytics.behavior import fetch_behavior
from app.analytics.funnel import fetch_funnel
from app.analytics.overview import fetch_overview
from app.analytics.products import (
    fetch_high_view_low_conversion,
    fetch_product_rankings,
)
from app.analytics.time_series import fetch_time_series
from app.database.mongodb import get_analytics_global_document
from app.schemas.responses import KeyFinding, ReportResponse


def _build_key_findings(
    overview_metrics: Any,
    peak_day: dict[str, Any],
    peak_tx_day: dict[str, Any],
    peak_hour: dict[str, Any],
    top_viewed: Any,
    top_purchased: Any,
) -> list[KeyFinding]:
    findings: list[KeyFinding] = []

    dominant = max(
        overview_metrics.event_distribution,
        key=lambda item: item.count,
    )
    findings.append(
        KeyFinding(
            metric="dominant_event_type",
            value=f"{dominant.event} ({dominant.percentage:.2f}% of events)",
            interpretation=f"{dominant.event} accounts for the largest share of recorded events.",
        )
    )

    findings.append(
        KeyFinding(
            metric="visitor_conversion_rate",
            value=f"{overview_metrics.visitor_conversion_rate * 100:.4f}%",
            interpretation=(
                "Share of unique visitors with at least one transaction event "
                "relative to all unique visitors."
            ),
        )
    )

    if peak_day["date"]:
        findings.append(
            KeyFinding(
                metric="peak_activity_day",
                value=f"{peak_day['date']} ({peak_day['events']:,} events)",
                interpretation="Day with the highest total event volume in the dataset.",
            )
        )

    if peak_tx_day["date"]:
        findings.append(
            KeyFinding(
                metric="peak_transaction_day",
                value=f"{peak_tx_day['date']} ({peak_tx_day['transactions']:,} transaction events)",
                interpretation="Day with the highest count of transaction line-item events.",
            )
        )

    if peak_hour["hour"] is not None:
        findings.append(
            KeyFinding(
                metric="peak_activity_hour_utc",
                value=f"{peak_hour['hour']:02d}:00 UTC ({peak_hour['events']:,} events)",
                interpretation="Hour of day (UTC) with the highest aggregated event volume.",
            )
        )

    if top_viewed.products:
        top = top_viewed.products[0]
        findings.append(
            KeyFinding(
                metric="top_viewed_product",
                value=f"item {top.item_id} ({top.views:,} views)",
                interpretation="Product with the highest view count in aggregated product metrics.",
            )
        )

    if top_purchased.products:
        top = top_purchased.products[0]
        findings.append(
            KeyFinding(
                metric="top_purchased_product",
                value=f"item {top.item_id} ({top.transactions:,} transaction events)",
                interpretation=(
                    "Product with the highest transaction event count "
                    "(line items, not unique orders)."
                ),
            )
        )

    return findings


def fetch_report(product_metrics: Collection) -> ReportResponse:
    global_doc = get_analytics_global_document()
    report_meta = global_doc["report_meta"]

    overview = fetch_overview()
    funnel = fetch_funnel()
    behavior = fetch_behavior()
    top_viewed = fetch_product_rankings(product_metrics, "views", 5)
    top_purchased = fetch_product_rankings(product_metrics, "transactions", 5)
    opportunities, median_conv, opp_methodology = fetch_high_view_low_conversion(product_metrics, 10)
    daily = fetch_time_series(None, "daily", None, None)

    peak_day = report_meta["peak_activity_day"]
    peak_tx_day = report_meta["peak_transaction_day"]
    peak_hour = report_meta["peak_activity_hour_utc"]

    return ReportResponse(
        dataset_summary={
            "total_events": overview.total_events,
            "unique_visitors": overview.unique_visitors,
            "unique_products": overview.unique_products,
            "date_range": overview.date_range.model_dump(),
        },
        engagement={
            "total_views": overview.total_views,
            "total_add_to_cart": overview.total_add_to_cart,
            "total_transactions": overview.total_transactions,
            "event_distribution": [item.model_dump() for item in overview.event_distribution],
            "avg_events_per_visitor": behavior.summary.avg_events_per_visitor,
        },
        conversion={
            "visitor_conversion_rate": overview.visitor_conversion_rate,
            "funnel": funnel.model_dump(),
        },
        product_performance={
            "top_viewed": [p.model_dump() for p in top_viewed.products],
            "top_purchased": [p.model_dump() for p in top_purchased.products],
            "high_view_low_conversion": {
                "methodology": opp_methodology,
                "median_conversion_reference": round(median_conv, 6),
                "products": [p.model_dump() for p in opportunities],
            },
        },
        time_trends={
            "peak_activity_day": peak_day,
            "peak_transaction_day": peak_tx_day,
            "peak_activity_hour_utc": peak_hour,
            "daily_series_points": len(daily.series),
        },
        key_findings=_build_key_findings(
            overview,
            peak_day,
            peak_tx_day,
            peak_hour,
            top_viewed,
            top_purchased,
        ),
    )
