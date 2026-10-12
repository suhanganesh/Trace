from __future__ import annotations

from typing import Any, Literal

from fastapi import HTTPException
from pymongo.collection import Collection

from app.analytics.common import safe_divide
from app.database.mongodb import aggregate_list
from app.schemas.responses import (
    ProductDetailResponse,
    ProductListResponse,
    ProductOpportunity,
    ProductRow,
)

MetricType = Literal["views", "addtocart", "transactions"]

METRIC_SORT_FIELD = {
    "views": "views",
    "addtocart": "add_to_cart",
    "transactions": "transactions",
}


def _rows_to_products(rows: list[dict[str, Any]]) -> list[ProductRow]:
    products: list[ProductRow] = []
    for rank, row in enumerate(rows, start=1):
        views = row["views"]
        transactions = row["transactions"]
        products.append(
            ProductRow(
                rank=rank,
                item_id=row["item_id"],
                views=views,
                add_to_cart=row["add_to_cart"],
                transactions=transactions,
                conversion_rate=round(safe_divide(transactions, views), 6),
            )
        )
    return products


def fetch_product_rankings(
    product_metrics: Collection,
    metric: MetricType,
    limit: int,
) -> ProductListResponse:
    sort_field = METRIC_SORT_FIELD[metric]
    pipeline: list[dict[str, Any]] = [
        {"$sort": {sort_field: -1}},
        {"$limit": limit},
    ]
    rows = aggregate_list(product_metrics, pipeline)
    return ProductListResponse(
        metric=metric,
        limit=limit,
        products=_rows_to_products(rows),
    )


def fetch_product_detail(
    product_metrics: Collection,
    product_metadata: Collection,
    item_id: int,
) -> ProductDetailResponse:
    row = product_metrics.find_one({"item_id": item_id})
    if not row:
        raise HTTPException(status_code=404, detail=f"Product {item_id} not found in events.")

    views = row["views"]
    meta_doc = product_metadata.find_one({"item_id": item_id}, {"_id": 0, "properties": 1})
    properties = meta_doc.get("properties", {}) if meta_doc else {}

    return ProductDetailResponse(
        item_id=item_id,
        views=views,
        add_to_cart=row["add_to_cart"],
        transactions=row["transactions"],
        conversion_rate=round(safe_divide(row["transactions"], views), 6),
        properties=properties,
    )


HIGH_VIEW_LOW_CONVERSION_METHODOLOGY = (
    "Among products with at least 50 views, select items in the top quartile by view "
    "count whose conversion rate (transactions/views) is below the median conversion "
    "rate of that same cohort. This highlights high-traffic products with comparatively "
    "low purchase activity using objective thresholds only."
)


def _linear_percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    k = (len(sorted_values) - 1) * p
    lower = int(k)
    upper = min(lower + 1, len(sorted_values) - 1)
    if lower == upper:
        return sorted_values[lower]
    weight = k - lower
    return sorted_values[lower] + weight * (sorted_values[upper] - sorted_values[lower])


def fetch_high_view_low_conversion(
    product_metrics: Collection,
    limit: int = 10,
) -> tuple[list[ProductOpportunity], float, str]:
    pipeline: list[dict[str, Any]] = [
        {"$match": {"views": {"$gte": 50}}},
        {
            "$project": {
                "_id": 0,
                "item_id": 1,
                "views": 1,
                "transactions": 1,
                "conversion_rate": {
                    "$cond": [
                        {"$eq": ["$views", 0]},
                        0,
                        {"$divide": ["$transactions", "$views"]},
                    ]
                },
            }
        },
    ]
    cohort = aggregate_list(product_metrics, pipeline)
    if not cohort:
        return [], 0.0, HIGH_VIEW_LOW_CONVERSION_METHODOLOGY

    views_sorted = sorted(row["views"] for row in cohort)
    conversions_sorted = sorted(row["conversion_rate"] for row in cohort)
    views_p75 = _linear_percentile([float(v) for v in views_sorted], 0.75)
    median_ref = _linear_percentile(conversions_sorted, 0.5)

    selected = [
        row
        for row in cohort
        if row["views"] >= views_p75 and row["conversion_rate"] < median_ref
    ]
    selected.sort(key=lambda row: row["views"], reverse=True)
    selected = selected[:limit]

    opportunities = [
        ProductOpportunity(
            item_id=row["item_id"],
            views=row["views"],
            transactions=row["transactions"],
            conversion_rate=round(row["conversion_rate"], 6),
            median_conversion_reference=round(median_ref, 6),
        )
        for row in selected
    ]
    return opportunities, median_ref, HIGH_VIEW_LOW_CONVERSION_METHODOLOGY
