#!/usr/bin/env python3
"""
Import processed Trace CSV files into MongoDB (retailrocket_analytics).

Reads configuration from environment variables. Does not modify raw or processed CSV files.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from dataset_utils import (
    EVENT_TYPES,
    MONGODB_IMPORT_REPORT,
    PROCESSED_CATEGORY,
    PROCESSED_DIR,
    PROCESSED_EVENTS,
    PROCESSED_ITEM_PROPERTIES,
    PROCESSING_SUMMARY,
    PROJECT_ROOT,
)

COLLECTION_EVENTS = "events"
COLLECTION_ITEM_PROPERTIES = "item_properties"
COLLECTION_CATEGORY = "category_tree"

TARGET_COLLECTIONS = (
    COLLECTION_EVENTS,
    COLLECTION_ITEM_PROPERTIES,
    COLLECTION_CATEGORY,
)

PROGRESS_LOG_EVERY = 500_000


def load_dotenv(path: Path) -> None:
    """Load KEY=VALUE lines into os.environ (does not override existing vars)."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def parse_int(value: str, field: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid integer for {field}: {value!r}") from exc


def event_row_to_document(row: dict[str, str]) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "timestamp": parse_int(row["timestamp"], "timestamp"),
        "visitorid": parse_int(row["visitorid"], "visitorid"),
        "event": row["event"].strip(),
        "itemid": parse_int(row["itemid"], "itemid"),
        "datetime": row["datetime"].strip(),
        "date": row["date"].strip(),
        "year": parse_int(row["year"], "year"),
        "month": parse_int(row["month"], "month"),
        "day": parse_int(row["day"], "day"),
        "hour": parse_int(row["hour"], "hour"),
        "day_of_week": row["day_of_week"].strip(),
    }
    tid = row.get("transactionid", "").strip()
    if tid:
        doc["transactionid"] = tid
    return doc


def item_property_row_to_document(row: dict[str, str]) -> dict[str, Any]:
    return {
        "timestamp": parse_int(row["timestamp"], "timestamp"),
        "itemid": parse_int(row["itemid"], "itemid"),
        "property": row["property"].strip(),
        "value": row["value"].strip(),
        "datetime": row["datetime"].strip(),
        "date": row["date"].strip(),
    }


def category_row_to_document(row: dict[str, str]) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "categoryid": parse_int(row["categoryid"], "categoryid"),
    }
    parent = row.get("parentid", "").strip()
    if parent:
        doc["parentid"] = parse_int(parent, "parentid")
    return doc


def iter_csv_rows(path: Path) -> Iterable[dict[str, str]]:
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        yield from csv.DictReader(handle)


def bulk_insert_batches(
    collection: Any,
    documents: list[dict[str, Any]],
    batch_size: int,
    ordered: bool = False,
) -> tuple[int, list[str]]:
    if not documents:
        return 0, []
    from pymongo.errors import BulkWriteError

    errors: list[str] = []
    inserted = 0
    for start in range(0, len(documents), batch_size):
        chunk = documents[start : start + batch_size]
        try:
            result = collection.insert_many(chunk, ordered=ordered)
            inserted += len(result.inserted_ids)
        except BulkWriteError as exc:
            details = exc.details or {}
            inserted += details.get("nInserted", 0)
            write_errors = details.get("writeErrors", [])
            for item in write_errors[:5]:
                errors.append(str(item))
            if len(write_errors) > 5:
                errors.append(f"... and {len(write_errors) - 5} more write errors")
        except Exception as exc:  # noqa: BLE001 — surface import failures in report
            errors.append(str(exc))
            break
    return inserted, errors


def import_csv_streaming(
    collection: Any,
    path: Path,
    row_to_doc: Any,
    batch_size: int,
    label: str,
    expected_rows: int | None,
) -> dict[str, Any]:
    batch: list[dict[str, Any]] = []
    rows_read = 0
    documents_inserted = 0
    errors: list[str] = []
    started = time.perf_counter()

    for row in iter_csv_rows(path):
        rows_read += 1
        try:
            batch.append(row_to_doc(row))
        except ValueError as exc:
            errors.append(f"Row {rows_read}: {exc}")
            continue

        if len(batch) >= batch_size:
            inserted, batch_errors = bulk_insert_batches(collection, batch, batch_size)
            documents_inserted += inserted
            errors.extend(batch_errors)
            batch.clear()

        if rows_read % PROGRESS_LOG_EVERY == 0:
            expected_display = f" / {expected_rows:,}" if expected_rows else ""
            print(f"{label}: {rows_read:,}{expected_display} rows read...", file=sys.stderr)

    if batch:
        inserted, batch_errors = bulk_insert_batches(collection, batch, batch_size)
        documents_inserted += inserted
        errors.extend(batch_errors)

    duration = round(time.perf_counter() - started, 3)
    return {
        "source_file": str(path.relative_to(PROJECT_ROOT)),
        "rows_read": rows_read,
        "documents_inserted": documents_inserted,
        "duration_seconds": duration,
        "errors": errors,
    }


def import_category_tree(
    collection: Any,
    path: Path,
    batch_size: int,
) -> dict[str, Any]:
    documents = []
    errors: list[str] = []
    rows_read = 0
    for row in iter_csv_rows(path):
        rows_read += 1
        try:
            documents.append(category_row_to_document(row))
        except ValueError as exc:
            errors.append(f"Row {rows_read}: {exc}")

    started = time.perf_counter()
    inserted, insert_errors = bulk_insert_batches(collection, documents, batch_size)
    errors.extend(insert_errors)
    duration = round(time.perf_counter() - started, 3)

    return {
        "source_file": str(path.relative_to(PROJECT_ROOT)),
        "rows_read": rows_read,
        "documents_inserted": inserted,
        "duration_seconds": duration,
        "errors": errors,
    }


def collection_counts(db: Any) -> dict[str, int]:
    return {name: db[name].estimated_document_count() for name in TARGET_COLLECTIONS}


def create_indexes(db: Any) -> list[dict[str, Any]]:
    """Create indexes after import (import → indexes → validate)."""
    events = db[COLLECTION_EVENTS]
    item_props = db[COLLECTION_ITEM_PROPERTIES]
    categories = db[COLLECTION_CATEGORY]

    index_plan: list[tuple[Any, str, dict[str, Any], str]] = [
        (
            events,
            "idx_event",
            {"event": 1},
            "Filter and group by event type (views, addtocart, transaction).",
        ),
        (
            events,
            "idx_timestamp",
            {"timestamp": 1},
            "Time-series aggregations (daily/hourly activity, date-range filters).",
        ),
        (
            events,
            "idx_visitorid",
            {"visitorid": 1},
            "Visitor behavior and conversion (per-visitor event history).",
        ),
        (
            events,
            "idx_itemid",
            {"itemid": 1},
            "Product rankings and product-level funnel metrics.",
        ),
        (
            events,
            "idx_transactionid_sparse",
            {"transactionid": 1},
            "Order-level analysis; sparse because only transaction events carry an ID.",
        ),
        (
            events,
            "idx_event_timestamp",
            {"event": 1, "timestamp": 1},
            "Event-type trends over time (e.g. transactions by day).",
        ),
        (
            events,
            "idx_visitorid_timestamp",
            {"visitorid": 1, "timestamp": 1},
            "Visitor timelines and repeat engagement within a period.",
        ),
        (
            events,
            "idx_itemid_event",
            {"itemid": 1, "event": 1},
            "Product conversion (views vs addtocart vs transaction per item).",
        ),
        (
            item_props,
            "idx_itemid",
            {"itemid": 1},
            "Lookup properties for a product ($match / $lookup on itemid).",
        ),
        (
            item_props,
            "idx_property",
            {"property": 1},
            "Filter by property name (e.g. categoryid, available).",
        ),
        (
            item_props,
            "idx_timestamp",
            {"timestamp": 1},
            "Time-ordered property history when needed.",
        ),
        (
            item_props,
            "idx_itemid_property_timestamp",
            {"itemid": 1, "property": 1, "timestamp": 1},
            "Latest or chronological property values for an item.",
        ),
        (
            categories,
            "idx_categoryid_unique",
            {"categoryid": 1},
            "Unique category lookup.",
        ),
        (
            categories,
            "idx_parentid",
            {"parentid": 1},
            "Traverse parent → child category relationships.",
        ),
    ]

    created: list[dict[str, Any]] = []
    for collection, name, keys, purpose in index_plan:
        options: dict[str, Any] = {"name": name}
        if name == "idx_categoryid_unique":
            options["unique"] = True
        if name == "idx_transactionid_sparse":
            options["sparse"] = True

        started = time.perf_counter()
        result_name = collection.create_index(list(keys.items()), **options)
        duration = round(time.perf_counter() - started, 3)
        created.append(
            {
                "collection": collection.name,
                "index_name": result_name,
                "keys": keys,
                "options": {k: v for k, v in options.items() if k != "name"},
                "purpose": purpose,
                "duration_seconds": duration,
            }
        )
    return created


def validate_import(db: Any, processing_summary: dict[str, Any]) -> dict[str, Any]:
    expected_counts = processing_summary.get("processed_row_counts", {})
    expected_events = expected_counts.get("events")
    expected_item_props = expected_counts.get("item_properties")
    expected_categories = expected_counts.get("category_tree")

    actual_counts = {
        COLLECTION_EVENTS: db[COLLECTION_EVENTS].count_documents({}),
        COLLECTION_ITEM_PROPERTIES: db[COLLECTION_ITEM_PROPERTIES].count_documents({}),
        COLLECTION_CATEGORY: db[COLLECTION_CATEGORY].count_documents({}),
    }

    count_checks = {
        COLLECTION_EVENTS: {
            "expected": expected_events,
            "actual": actual_counts[COLLECTION_EVENTS],
            "match": actual_counts[COLLECTION_EVENTS] == expected_events,
        },
        COLLECTION_ITEM_PROPERTIES: {
            "expected": expected_item_props,
            "actual": actual_counts[COLLECTION_ITEM_PROPERTIES],
            "match": actual_counts[COLLECTION_ITEM_PROPERTIES] == expected_item_props,
        },
        COLLECTION_CATEGORY: {
            "expected": expected_categories,
            "actual": actual_counts[COLLECTION_CATEGORY],
            "match": actual_counts[COLLECTION_CATEGORY] == expected_categories,
        },
    }

    events_col = db[COLLECTION_EVENTS]
    event_distribution = {
        row["_id"]: row["count"]
        for row in events_col.aggregate([{"$group": {"_id": "$event", "count": {"$sum": 1}}}])
    }
    event_types_valid = set(event_distribution) <= EVENT_TYPES and len(event_distribution) > 0

    unique_visitors = len(events_col.distinct("visitorid"))
    unique_products = len(events_col.distinct("itemid"))
    transaction_events = events_col.count_documents({"event": "transaction"})
    distinct_transaction_ids = len(events_col.distinct("transactionid", {"event": "transaction"}))

    expected = processing_summary
    comparison = {
        "event_distribution": {
            "mongodb": event_distribution,
            "processing_summary": expected.get("event_counts", {}),
            "match": event_distribution == expected.get("event_counts", {}),
        },
        "unique_visitors": {
            "mongodb": unique_visitors,
            "processing_summary": expected.get("unique_visitors"),
            "match": unique_visitors == expected.get("unique_visitors"),
        },
        "unique_products_in_events": {
            "mongodb": unique_products,
            "processing_summary": expected.get("unique_products_in_events"),
            "match": unique_products == expected.get("unique_products_in_events"),
        },
        "transaction_event_count": {
            "mongodb": transaction_events,
            "processing_summary": expected.get("transaction_event_count"),
            "match": transaction_events == expected.get("transaction_event_count"),
        },
        "distinct_transaction_ids": {
            "mongodb": distinct_transaction_ids,
            "processing_summary": expected.get("distinct_transaction_ids"),
            "match": distinct_transaction_ids == expected.get("distinct_transaction_ids"),
        },
    }

    warnings: list[str] = []
    if not all(check["match"] for check in count_checks.values()):
        warnings.append("Document counts do not match processing_summary.json")
    if not event_types_valid:
        warnings.append("Unexpected event types found in events collection")
    if not all(section.get("match") for section in comparison.values()):
        warnings.append("One or more metric comparisons differ from processing_summary.json")

    return {
        "document_counts": count_checks,
        "event_distribution": event_distribution,
        "event_types_valid": event_types_valid,
        "metrics_comparison": comparison,
        "validation_passed": not warnings,
        "warnings": warnings,
    }


def ensure_processed_files() -> dict[str, Any]:
    required = {
        "events": PROCESSED_EVENTS,
        "item_properties": PROCESSED_ITEM_PROPERTIES,
        "category_tree": PROCESSED_CATEGORY,
        "processing_summary": PROCESSING_SUMMARY,
    }
    missing = [name for name, path in required.items() if not path.is_file()]
    if missing:
        raise SystemExit(
            "Missing processed files: "
            + ", ".join(missing)
            + ". Run: python scripts/process_dataset.py"
        )
    return json.loads(PROCESSING_SUMMARY.read_text(encoding="utf-8"))


def check_existing_data(db: Any) -> dict[str, int]:
    return {name: db[name].estimated_document_count() for name in TARGET_COLLECTIONS}


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")

    parser = argparse.ArgumentParser(description="Import Trace processed CSV data into MongoDB.")
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop target collections before import (use for a clean re-import).",
    )
    args = parser.parse_args()

    mongodb_uri = os.environ.get("MONGODB_URI", "").strip()
    database_name = os.environ.get("MONGODB_DATABASE", "retailrocket_analytics").strip()
    batch_size = int(os.environ.get("MONGODB_BATCH_SIZE", "10000"))

    if not mongodb_uri:
        raise SystemExit("MONGODB_URI is not set. Copy .env.example to .env and configure it.")

    if batch_size < 100 or batch_size > 50_000:
        raise SystemExit("MONGODB_BATCH_SIZE must be between 100 and 50000.")

    processing_summary = ensure_processed_files()
    expected_counts = processing_summary.get("processed_row_counts", {})

    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    except ImportError as exc:
        raise SystemExit("PyMongo is required. Install with: pip install pymongo") from exc

    report: dict[str, Any] = {
        "database": database_name,
        "collections": list(TARGET_COLLECTIONS),
        "source_files": {
            COLLECTION_EVENTS: str(PROCESSED_EVENTS.relative_to(PROJECT_ROOT)),
            COLLECTION_ITEM_PROPERTIES: str(PROCESSED_ITEM_PROPERTIES.relative_to(PROJECT_ROOT)),
            COLLECTION_CATEGORY: str(PROCESSED_CATEGORY.relative_to(PROJECT_ROOT)),
        },
        "batch_size": batch_size,
        "indexes_created": [],
        "imports": {},
        "validation": {},
        "errors": [],
        "warnings": [],
    }

    import_started = datetime.now(timezone.utc)
    report["import_started_at_utc"] = import_started.strftime("%Y-%m-%dT%H:%M:%SZ")
    wall_start = time.perf_counter()

    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10_000)
    try:
        client.admin.command("ping")
    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        raise SystemExit(f"MongoDB is not reachable: {exc}") from exc

    db = client[database_name]
    report["mongodb_reachable"] = True

    existing = check_existing_data(db)
    if any(count > 0 for count in existing.values()):
        if not args.drop:
            raise SystemExit(
                "Target collections already contain data: "
                f"{existing}. Re-run with --drop to replace collections, "
                "or drop them manually in MongoDB."
            )
        print(f"Dropping collections: {', '.join(TARGET_COLLECTIONS)}", file=sys.stderr)
        for name in TARGET_COLLECTIONS:
            db[name].drop()

    print("Importing events...", file=sys.stderr)
    report["imports"][COLLECTION_EVENTS] = import_csv_streaming(
        db[COLLECTION_EVENTS],
        PROCESSED_EVENTS,
        event_row_to_document,
        batch_size,
        "Events",
        expected_counts.get("events"),
    )

    print("Importing item properties...", file=sys.stderr)
    report["imports"][COLLECTION_ITEM_PROPERTIES] = import_csv_streaming(
        db[COLLECTION_ITEM_PROPERTIES],
        PROCESSED_ITEM_PROPERTIES,
        item_property_row_to_document,
        batch_size,
        "Item properties",
        expected_counts.get("item_properties"),
    )

    print("Importing category tree...", file=sys.stderr)
    report["imports"][COLLECTION_CATEGORY] = import_category_tree(
        db[COLLECTION_CATEGORY],
        PROCESSED_CATEGORY,
        batch_size,
    )

    print("Creating indexes...", file=sys.stderr)
    report["indexes_created"] = create_indexes(db)

    print("Validating import...", file=sys.stderr)
    report["validation"] = validate_import(db, processing_summary)
    report["warnings"].extend(report["validation"].get("warnings", []))

    for section in report["imports"].values():
        report["errors"].extend(section.get("errors", []))

    import_finished = datetime.now(timezone.utc)
    report["import_finished_at_utc"] = import_finished.strftime("%Y-%m-%dT%H:%M:%SZ")
    report["duration_seconds"] = round(time.perf_counter() - wall_start, 3)
    report["documents_imported"] = {
        name: report["imports"][name]["documents_inserted"] for name in TARGET_COLLECTIONS
    }

    MONGODB_IMPORT_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nWrote import report to {MONGODB_IMPORT_REPORT}", file=sys.stderr)

    if not report["validation"].get("validation_passed", False):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
