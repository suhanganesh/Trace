from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException

from app.database.mongodb import (
    get_analytics_global_collection,
    get_category_tree_collection,
    get_product_metadata_collection,
    get_product_metrics_collection,
    get_time_series_daily_collection,
    get_time_series_hourly_collection,
    is_compact_deployment,
    ping_database,
)
from app.dependencies import require_mongodb
from app.schemas.responses import DatasetInfoResponse, DateRange
from app.utils.config import get_settings

router = APIRouter(tags=["Dataset"])


@router.get(
    "/dataset-info",
    response_model=DatasetInfoResponse,
    summary="Dataset metadata and processing summary",
)
def get_dataset_info(_: None = Depends(require_mongodb)) -> DatasetInfoResponse:
    settings = get_settings()
    if not settings.processing_summary_path.is_file():
        raise HTTPException(
            status_code=503,
            detail="processing_summary.json not found. Run process_dataset.py first.",
        )

    summary = json.loads(settings.processing_summary_path.read_text(encoding="utf-8"))
    processed_counts = summary.get("processed_row_counts", {})
    event_counts = summary.get("event_counts", {})

    date_range = None
    if ping_database() and get_analytics_global_collection().estimated_document_count():
        global_doc = get_analytics_global_collection().find_one({}, {"overview.date_range": 1})
        if global_doc:
            dr = global_doc.get("overview", {}).get("date_range", {})
            date_range = DateRange(start=dr.get("start", ""), end=dr.get("end", ""))

    db_status = "connected" if ping_database() else "disconnected"

    mongodb_analytical_storage = {
        "deployment_mode": settings.mongodb_deployment_mode,
        "collections": {
            "analytics_global": get_analytics_global_collection().estimated_document_count(),
            "product_metrics": get_product_metrics_collection().estimated_document_count(),
            "product_metadata": get_product_metadata_collection().estimated_document_count(),
            "time_series_daily": get_time_series_daily_collection().estimated_document_count(),
            "time_series_hourly": get_time_series_hourly_collection().estimated_document_count(),
            "category_tree": get_category_tree_collection().estimated_document_count(),
        },
    }

    processing_information = {
        "processing_timestamp_utc": summary.get("processing_timestamp_utc"),
        "processing_duration_seconds": summary.get("processing_duration_seconds"),
        "duplicate_rows_removed": summary.get("duplicate_rows_removed"),
        "source_files": summary.get("source_files"),
        "full_processed_dataset": processed_counts,
        "mongodb_analytical_storage": mongodb_analytical_storage,
        "note": (
            "Full dataset row counts come from the local processed CSV pipeline. "
            "MongoDB stores compact analytical rollups for Atlas free-tier deployment."
        ),
    }

    if not is_compact_deployment():
        processing_information["warning"] = (
            "MONGODB_DEPLOYMENT_MODE is not compact; ensure analytics collections are populated."
        )

    return DatasetInfoResponse(
        dataset_name="RetailRocket",
        processed_event_count=processed_counts.get("events", 0),
        item_property_count=processed_counts.get("item_properties", 0),
        category_count=processed_counts.get("category_tree", 0),
        unique_visitors=summary.get("unique_visitors"),
        unique_products=summary.get("unique_products_in_events"),
        event_counts={str(k): int(v) for k, v in event_counts.items()},
        transaction_count=summary.get("transaction_event_count"),
        date_range=date_range,
        processing_information=processing_information,
        database_status=db_status,
    )
