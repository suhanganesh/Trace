#!/usr/bin/env python3
"""
Build compact MongoDB rollup artifacts from processed CSV files (Atlas free tier).

Reads only from data/processed/ — never modifies source CSVs.
"""

from __future__ import annotations

import csv
import heapq
import json
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from dataset_utils import (
    ACTIVITY_BOUNDARIES,
    EVENT_TYPES,
    PROCESSED_CATEGORY,
    PROCESSED_EVENTS,
    PROCESSED_ITEM_PROPERTIES,
    PROCESSING_SUMMARY,
    ROLLUP_ANALYTICS_GLOBAL,
    ROLLUP_CATEGORY,
    ROLLUP_DIR,
    ROLLUP_MANIFEST,
    ROLLUP_PRODUCT_METADATA,
    ROLLUP_PRODUCT_METRICS,
    ROLLUP_TIME_DAILY,
    ROLLUP_TIME_HOURLY,
    ROLLUP_VALIDATION,
)

PROGRESS_EVERY = 500_000


@dataclass
class VisitorRollup:
    total_events: int = 0
    views: int = 0
    add_to_cart: int = 0
    transactions: int = 0
    has_view: bool = False
    has_add_to_cart: bool = False
    has_transaction: bool = False


@dataclass
class ProductRollup:
    views: int = 0
    add_to_cart: int = 0
    transactions: int = 0


@dataclass
class TimeBucket:
    views: int = 0
    addtocart: int = 0
    transactions: int = 0
    total_events: int = 0


def safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def pct(part: float, whole: float) -> float:
    return round(safe_divide(part, whole) * 100, 4)


def bucket_label(index: int, bucket_id: Any) -> tuple[str, int, int | None]:
    if bucket_id == "10000+":
        return "10000+ events", 10000, None
    next_boundary = ACTIVITY_BOUNDARIES[index + 1] if index + 1 < len(ACTIVITY_BOUNDARIES) else None
    min_events = int(bucket_id)
    max_events = (next_boundary - 1) if next_boundary else None
    label = (
        f"{min_events}-{max_events} events"
        if max_events is not None
        else f"{min_events}+ events"
    )
    return label, min_events, max_events


def assign_activity_bucket(total: int) -> Any:
    for idx in range(len(ACTIVITY_BOUNDARIES) - 1):
        low = ACTIVITY_BOUNDARIES[idx]
        high = ACTIVITY_BOUNDARIES[idx + 1]
        if low <= total < high:
            return low
    if total >= ACTIVITY_BOUNDARIES[-1]:
        return "10000+"
    return ACTIVITY_BOUNDARIES[0]


def build_activity_distribution(visitors: dict[int, VisitorRollup]) -> list[dict[str, Any]]:
    bucket_counts: dict[Any, int] = defaultdict(int)
    for visitor in visitors.values():
        bucket_counts[assign_activity_bucket(visitor.total_events)] += 1

    distribution: list[dict[str, Any]] = []
    for index, boundary in enumerate(ACTIVITY_BOUNDARIES):
        if boundary not in bucket_counts:
            continue
        label, min_events, max_events = bucket_label(index, boundary)
        distribution.append(
            {
                "label": label,
                "min_events": min_events,
                "max_events": max_events,
                "visitor_count": bucket_counts[boundary],
            }
        )
    if "10000+" in bucket_counts:
        distribution.append(
            {
                "label": "10000+ events",
                "min_events": 10000,
                "max_events": None,
                "visitor_count": bucket_counts["10000+"],
            }
        )
    return distribution


def stream_events() -> tuple[dict[str, Any], dict[int, ProductRollup], set[int]]:
    visitors: dict[int, VisitorRollup] = defaultdict(VisitorRollup)
    products: dict[int, ProductRollup] = defaultdict(ProductRollup)
    daily: dict[str, TimeBucket] = defaultdict(TimeBucket)
    hourly: dict[tuple[str, int], TimeBucket] = defaultdict(TimeBucket)
    hour_totals: dict[int, int] = defaultdict(int)
    event_counts: dict[str, int] = defaultdict(int)
    min_date: str | None = None
    max_date: str | None = None
    total_events = 0

    with PROCESSED_EVENTS.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            total_events += 1
            if total_events % PROGRESS_EVERY == 0:
                print(f"  events: {total_events:,} rows processed...", file=sys.stderr)

            event = row["event"].strip()
            if event not in EVENT_TYPES:
                continue
            event_counts[event] += 1

            visitor_id = int(row["visitorid"])
            item_id = int(row["itemid"])
            date = row["date"].strip()
            hour = int(row["hour"])

            min_date = date if min_date is None else min(min_date, date)
            max_date = date if max_date is None else max(max_date, date)

            visitor = visitors[visitor_id]
            visitor.total_events += 1
            if event == "view":
                visitor.views += 1
                visitor.has_view = True
            elif event == "addtocart":
                visitor.add_to_cart += 1
                visitor.has_add_to_cart = True
            elif event == "transaction":
                visitor.transactions += 1
                visitor.has_transaction = True

            product = products[item_id]
            if event == "view":
                product.views += 1
            elif event == "addtocart":
                product.add_to_cart += 1
            elif event == "transaction":
                product.transactions += 1

            day_bucket = daily[date]
            hour_bucket = hourly[(date, hour)]
            hour_totals[hour] += 1
            for bucket in (day_bucket, hour_bucket):
                bucket.total_events += 1
                if event == "view":
                    bucket.views += 1
                elif event == "addtocart":
                    bucket.addtocart += 1
                elif event == "transaction":
                    bucket.transactions += 1

    unique_visitors = len(visitors)
    converting = sum(1 for v in visitors.values() if v.has_transaction)
    view_visitors = sum(1 for v in visitors.values() if v.has_view)
    cart_visitors = sum(1 for v in visitors.values() if v.has_add_to_cart)
    tx_visitors = sum(1 for v in visitors.values() if v.has_transaction)

    total_views = event_counts.get("view", 0)
    total_add_to_cart = event_counts.get("addtocart", 0)
    total_transactions = event_counts.get("transaction", 0)

    visitors_with_cart = sum(1 for v in visitors.values() if v.add_to_cart > 0)
    visitors_with_tx = sum(1 for v in visitors.values() if v.transactions > 0)
    repeat_visitors = sum(1 for v in visitors.values() if v.total_events > 1)
    single_event = sum(1 for v in visitors.values() if v.total_events == 1)
    total_visitor_events = sum(v.total_events for v in visitors.values())
    total_visitor_views = sum(v.views for v in visitors.values())

    top_visitors = heapq.nlargest(
        15,
        visitors.items(),
        key=lambda item: item[1].total_events,
    )
    top_visitor_rows = [
        {
            "visitor_id": vid,
            "total_events": data.total_events,
            "views": data.views,
            "add_to_cart": data.add_to_cart,
            "transactions": data.transactions,
        }
        for vid, data in top_visitors
    ]

    peak_day = max(daily.items(), key=lambda x: x[1].total_events)
    peak_tx_day = max(daily.items(), key=lambda x: x[1].transactions)
    peak_hour = max(hour_totals.items(), key=lambda x: x[1])

    event_distribution = []
    for name in ("view", "addtocart", "transaction"):
        count = event_counts.get(name, 0)
        event_distribution.append(
            {"event": name, "count": count, "percentage": pct(count, total_events)}
        )

    analytics_global = {
        "overview": {
            "total_events": total_events,
            "unique_visitors": unique_visitors,
            "unique_products": len(products),
            "total_views": total_views,
            "total_add_to_cart": total_add_to_cart,
            "total_transactions": total_transactions,
            "visitor_conversion_rate": round(safe_divide(converting, unique_visitors), 6),
            "date_range": {"start": min_date or "", "end": max_date or ""},
            "event_distribution": event_distribution,
        },
        "funnel": {
            "view_visitors": view_visitors,
            "addtocart_visitors": cart_visitors,
            "transaction_visitors": tx_visitors,
        },
        "behavior": {
            "summary": {
                "total_visitors": unique_visitors,
                "total_events": total_visitor_events,
                "avg_events_per_visitor": round(safe_divide(total_visitor_events, unique_visitors), 4),
                "avg_views_per_visitor": round(safe_divide(total_visitor_views, unique_visitors), 4),
                "visitors_with_add_to_cart": visitors_with_cart,
                "visitors_with_transaction": visitors_with_tx,
                "repeat_visitors": repeat_visitors,
            },
            "activity_distribution": build_activity_distribution(visitors),
            "top_visitors": top_visitor_rows,
            "engagement_metrics": {
                "single_event_visitors": single_event,
                "multi_event_visitors": unique_visitors - single_event,
                "pct_visitors_with_purchase": round(
                    safe_divide(visitors_with_tx, unique_visitors) * 100,
                    4,
                ),
            },
        },
        "report_meta": {
            "peak_activity_day": {"date": peak_day[0], "events": peak_day[1].total_events},
            "peak_transaction_day": {
                "date": peak_tx_day[0],
                "transactions": peak_tx_day[1].transactions,
            },
            "peak_activity_hour_utc": {"hour": peak_hour[0], "events": peak_hour[1]},
            "daily_series_points": len(daily),
        },
        "built_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    aggregates = {
        "analytics_global": analytics_global,
        "products": products,
        "daily": daily,
        "hourly": hourly,
        "event_counts": dict(event_counts),
        "total_events": total_events,
        "unique_visitors": unique_visitors,
        "unique_products": len(products),
        "min_date": min_date,
        "max_date": max_date,
    }
    return aggregates, products.keys()


def write_jsonl(path: Path, rows: list[dict[str, Any]] | Any) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


def stream_product_metadata(product_ids: set[int]) -> int:
    latest: dict[int, dict[str, Any]] = {}
    rows_read = 0
    with PROCESSED_ITEM_PROPERTIES.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows_read += 1
            if rows_read % 2_000_000 == 0:
                print(f"  item_properties: {rows_read:,} rows scanned...", file=sys.stderr)
            prop = row["property"].strip()
            if prop not in ("categoryid", "available"):
                continue
            item_id = int(row["itemid"])
            if item_id not in product_ids:
                continue
            ts = int(row["timestamp"])
            current = latest.get(item_id, {}).get(prop)
            if current is None or ts > current["timestamp"]:
                if item_id not in latest:
                    latest[item_id] = {}
                latest[item_id][prop] = {
                    "timestamp": ts,
                    "value": row["value"].strip(),
                    "datetime": row["datetime"].strip(),
                }

    count = 0
    with ROLLUP_PRODUCT_METADATA.open("w", encoding="utf-8") as handle:
        for item_id in sorted(latest):
            props = latest[item_id]
            doc: dict[str, Any] = {"item_id": item_id, "properties": {}}
            for prop_name, meta in props.items():
                doc["properties"][prop_name] = {
                    "value": meta["value"],
                    "recorded_at": meta["datetime"],
                }
            handle.write(json.dumps(doc, ensure_ascii=False) + "\n")
            count += 1
    return count


def load_category_tree_jsonl() -> int:
    count = 0
    with PROCESSED_CATEGORY.open(newline="", encoding="utf-8") as src, ROLLUP_CATEGORY.open(
        "w", encoding="utf-8"
    ) as dst:
        reader = csv.DictReader(src)
        for row in reader:
            doc: dict[str, Any] = {"categoryid": int(row["categoryid"])}
            parent = row.get("parentid", "").strip()
            if parent:
                doc["parentid"] = int(parent)
            dst.write(json.dumps(doc) + "\n")
            count += 1
    return count


def validate_rollups(
    analytics_global: dict[str, Any],
    *,
    category_count: int,
) -> dict[str, Any]:
    summary = json.loads(PROCESSING_SUMMARY.read_text(encoding="utf-8"))
    overview = analytics_global["overview"]
    checks = {
        "total_events": {
            "rollup": overview["total_events"],
            "summary": summary.get("processed_row_counts", {}).get("events"),
            "match": overview["total_events"]
            == summary.get("processed_row_counts", {}).get("events"),
        },
        "unique_visitors": {
            "rollup": overview["unique_visitors"],
            "summary": summary.get("unique_visitors"),
            "match": overview["unique_visitors"] == summary.get("unique_visitors"),
        },
        "unique_products_in_events": {
            "rollup": overview["unique_products"],
            "summary": summary.get("unique_products_in_events"),
            "match": overview["unique_products"]
            == summary.get("unique_products_in_events"),
        },
        "transaction_event_count": {
            "rollup": overview["total_transactions"],
            "summary": summary.get("transaction_event_count"),
            "match": overview["total_transactions"] == summary.get("transaction_event_count"),
        },
        "view_count": {
            "rollup": overview["total_views"],
            "summary": summary.get("event_counts", {}).get("view"),
            "match": overview["total_views"] == summary.get("event_counts", {}).get("view"),
        },
        "addtocart_count": {
            "rollup": overview["total_add_to_cart"],
            "summary": summary.get("event_counts", {}).get("addtocart"),
            "match": overview["total_add_to_cart"]
            == summary.get("event_counts", {}).get("addtocart"),
        },
        "date_range_start": {
            "rollup": overview["date_range"]["start"],
            "summary": summary.get("event_date_range", {}).get("min_date"),
            "match": (
                summary.get("event_date_range", {}).get("min_date") is None
                or overview["date_range"]["start"]
                == summary.get("event_date_range", {}).get("min_date")
            ),
        },
        "date_range_end": {
            "rollup": overview["date_range"]["end"],
            "summary": summary.get("event_date_range", {}).get("max_date"),
            "match": (
                summary.get("event_date_range", {}).get("max_date") is None
                or overview["date_range"]["end"]
                == summary.get("event_date_range", {}).get("max_date")
            ),
        },
        "category_count": {
            "rollup": category_count,
            "summary": summary.get("category_count")
            or summary.get("processed_row_counts", {}).get("category_tree"),
            "match": category_count
            == (
                summary.get("category_count")
                or summary.get("processed_row_counts", {}).get("category_tree")
            ),
        },
    }
    event_counts = summary.get("event_counts", {})
    for key in ("view", "addtocart", "transaction"):
        dist = next((d for d in overview["event_distribution"] if d["event"] == key), None)
        if dist:
            checks[f"event_{key}"] = {
                "rollup": dist["count"],
                "summary": event_counts.get(key),
                "match": dist["count"] == event_counts.get(key),
            }

    passed = all(item.get("match") for item in checks.values())
    return {"validation_passed": passed, "checks": checks}


def main() -> None:
    started = time.perf_counter()
    for path in (PROCESSED_EVENTS, PROCESSED_ITEM_PROPERTIES, PROCESSED_CATEGORY, PROCESSING_SUMMARY):
        if not path.is_file():
            raise SystemExit(f"Missing required file: {path}")

    ROLLUP_DIR.mkdir(parents=True, exist_ok=True)

    print("Streaming processed events...", file=sys.stderr)
    aggregates, product_ids = stream_events()
    analytics_global = aggregates["analytics_global"]
    products: dict[int, ProductRollup] = aggregates["products"]
    daily: dict[str, TimeBucket] = aggregates["daily"]
    hourly: dict[tuple[str, int], TimeBucket] = aggregates["hourly"]

    ROLLUP_ANALYTICS_GLOBAL.write_text(json.dumps(analytics_global, indent=2), encoding="utf-8")

    print("Writing product_metrics.jsonl...", file=sys.stderr)
    product_count = 0
    with ROLLUP_PRODUCT_METRICS.open("w", encoding="utf-8") as handle:
        for item_id in sorted(products):
            p = products[item_id]
            doc = {
                "item_id": item_id,
                "views": p.views,
                "add_to_cart": p.add_to_cart,
                "transactions": p.transactions,
            }
            handle.write(json.dumps(doc) + "\n")
            product_count += 1

    print("Writing time series JSONL...", file=sys.stderr)
    daily_count = write_jsonl(
        ROLLUP_TIME_DAILY,
        [
            {
                "date": date,
                "views": bucket.views,
                "addtocart": bucket.addtocart,
                "transactions": bucket.transactions,
                "total_events": bucket.total_events,
            }
            for date, bucket in sorted(daily.items())
        ],
    )
    hourly_count = write_jsonl(
        ROLLUP_TIME_HOURLY,
        [
            {
                "date": date,
                "hour": hour,
                "views": bucket.views,
                "addtocart": bucket.addtocart,
                "transactions": bucket.transactions,
                "total_events": bucket.total_events,
            }
            for (date, hour), bucket in sorted(hourly.items())
        ],
    )

    print("Streaming item properties for product metadata...", file=sys.stderr)
    metadata_count = stream_product_metadata(set(product_ids))

    print("Writing category_tree.jsonl...", file=sys.stderr)
    category_count = load_category_tree_jsonl()

    validation = validate_rollups(analytics_global, category_count=category_count)
    ROLLUP_VALIDATION.write_text(json.dumps(validation, indent=2), encoding="utf-8")

    manifest = {
        "built_at_utc": analytics_global["built_at_utc"],
        "duration_seconds": round(time.perf_counter() - started, 3),
        "sources": {
            "events": str(PROCESSED_EVENTS.name),
            "item_properties": str(PROCESSED_ITEM_PROPERTIES.name),
            "category_tree": str(PROCESSED_CATEGORY.name),
        },
        "artifact_counts": {
            "analytics_global_documents": 1,
            "product_metrics": product_count,
            "product_metadata": metadata_count,
            "time_series_daily": daily_count,
            "time_series_hourly": hourly_count,
            "category_tree": category_count,
        },
        "validation_passed": validation["validation_passed"],
    }
    ROLLUP_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(json.dumps(manifest, indent=2))
    if not validation["validation_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
