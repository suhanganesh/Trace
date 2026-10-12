"""Shared paths and helpers for Trace dataset scripts."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

RAW_EVENTS = RAW_DIR / "events.csv"
RAW_ITEM_PART1 = RAW_DIR / "item_properties_part1.csv"
RAW_ITEM_PART2 = RAW_DIR / "item_properties_part2.csv"
RAW_CATEGORY = RAW_DIR / "category_tree.csv"

PROCESSED_EVENTS = PROCESSED_DIR / "events.csv"
PROCESSED_ITEM_PROPERTIES = PROCESSED_DIR / "item_properties.csv"
PROCESSED_CATEGORY = PROCESSED_DIR / "category_tree.csv"
PROCESSING_SUMMARY = PROCESSED_DIR / "processing_summary.json"
DATA_QUALITY_REPORT = PROCESSED_DIR / "data_quality_report.json"
MONGODB_IMPORT_REPORT = PROCESSED_DIR / "mongodb_import_report.json"

ROLLUP_DIR = PROJECT_ROOT / "data" / "mongodb_free_tier"
ROLLUP_ANALYTICS_GLOBAL = ROLLUP_DIR / "analytics_global.json"
ROLLUP_PRODUCT_METRICS = ROLLUP_DIR / "product_metrics.jsonl"
ROLLUP_PRODUCT_METADATA = ROLLUP_DIR / "product_metadata.jsonl"
ROLLUP_TIME_DAILY = ROLLUP_DIR / "time_series_daily.jsonl"
ROLLUP_TIME_HOURLY = ROLLUP_DIR / "time_series_hourly.jsonl"
ROLLUP_CATEGORY = ROLLUP_DIR / "category_tree.jsonl"
ROLLUP_MANIFEST = ROLLUP_DIR / "rollup_manifest.json"
ROLLUP_VALIDATION = ROLLUP_DIR / "rollup_validation.json"
ANALYTICS_IMPORT_REPORT = ROLLUP_DIR / "analytics_import_report.json"

ACTIVITY_BOUNDARIES = [1, 2, 5, 10, 20, 50, 100, 250, 500, 1000, 10000]

EVENT_TYPES = frozenset({"view", "addtocart", "transaction"})

EVENTS_OUTPUT_FIELDS = [
    "timestamp",
    "visitorid",
    "event",
    "itemid",
    "transactionid",
    "datetime",
    "date",
    "year",
    "month",
    "day",
    "hour",
    "day_of_week",
]

ITEM_PROPERTIES_OUTPUT_FIELDS = [
    "timestamp",
    "itemid",
    "property",
    "value",
    "datetime",
    "date",
]

CATEGORY_OUTPUT_FIELDS = ["categoryid", "parentid"]


def file_size_bytes(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0


def ms_to_derived(ms: int) -> dict[str, str | int]:
    """Convert epoch milliseconds to UTC-derived fields."""
    dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    return {
        "datetime": dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "date": dt.strftime("%Y-%m-%d"),
        "year": dt.year,
        "month": dt.month,
        "day": dt.day,
        "hour": dt.hour,
        "day_of_week": dt.strftime("%A"),
    }


def event_row_key(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    return (
        row.get("timestamp", "").strip(),
        row.get("visitorid", "").strip(),
        row.get("event", "").strip(),
        row.get("itemid", "").strip(),
        row.get("transactionid", "").strip(),
    )
