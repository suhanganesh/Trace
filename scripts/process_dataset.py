#!/usr/bin/env python3
"""
Process RetailRocket raw CSV files into cleaned outputs under data/processed/.

Raw files in data/raw/ are never modified.
"""

from __future__ import annotations

import csv
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from dataset_utils import (
    CATEGORY_OUTPUT_FIELDS,
    DATA_QUALITY_REPORT,
    EVENT_TYPES,
    EVENTS_OUTPUT_FIELDS,
    ITEM_PROPERTIES_OUTPUT_FIELDS,
    PROCESSED_CATEGORY,
    PROCESSED_DIR,
    PROCESSED_EVENTS,
    PROCESSED_ITEM_PROPERTIES,
    PROCESSING_SUMMARY,
    RAW_CATEGORY,
    RAW_EVENTS,
    RAW_ITEM_PART1,
    RAW_ITEM_PART2,
    event_row_key,
    file_size_bytes,
    ms_to_derived,
)

EVENTS_LOG_EVERY = 500_000


def validate_event_row(row: dict[str, str]) -> tuple[bool, str | None]:
    event = row.get("event", "").strip()
    if event not in EVENT_TYPES:
        return False, "unknown_event"

    try:
        int(row["timestamp"])
    except (TypeError, ValueError, KeyError):
        return False, "invalid_timestamp"

    try:
        int(row["visitorid"])
    except (TypeError, ValueError, KeyError):
        return False, "invalid_visitorid"

    try:
        int(row["itemid"])
    except (TypeError, ValueError, KeyError):
        return False, "invalid_itemid"

    tid = row.get("transactionid", "").strip()
    if event == "transaction":
        if not tid:
            return False, "transaction_missing_id"
    elif tid:
        return False, "non_transaction_has_transactionid"

    return True, None


def validate_item_property_row(row: dict[str, str]) -> tuple[bool, str | None]:
    try:
        int(row["timestamp"])
    except (TypeError, ValueError, KeyError):
        return False, "invalid_timestamp"

    try:
        int(row["itemid"])
    except (TypeError, ValueError, KeyError):
        return False, "invalid_itemid"

    if not str(row.get("property", "")).strip():
        return False, "missing_property"

    if not str(row.get("value", "")).strip():
        return False, "missing_value"

    return True, None


def process_events() -> dict:
    """Stream events, drop invalid rows and exact duplicates (keep first occurrence)."""
    seen_keys: set[tuple[str, str, str, str, str]] = set()
    original_rows = 0
    processed_rows = 0
    duplicate_rows_detected = 0
    duplicate_rows_removed = 0
    invalid_rows = Counter()
    source_event_counts: Counter[str] = Counter()
    processed_event_counts: Counter[str] = Counter()
    visitors: set[int] = set()
    items: set[int] = set()
    transaction_ids: set[str] = set()
    min_ts: int | None = None
    max_ts: int | None = None
    missing = Counter()

    PROCESSED_EVENTS.parent.mkdir(parents=True, exist_ok=True)

    with RAW_EVENTS.open(newline="", encoding="utf-8", errors="replace") as src, PROCESSED_EVENTS.open(
        "w", newline="", encoding="utf-8"
    ) as dst:
        reader = csv.DictReader(src)
        writer = csv.DictWriter(dst, fieldnames=EVENTS_OUTPUT_FIELDS)
        writer.writeheader()

        for row in reader:
            original_rows += 1
            if original_rows % EVENTS_LOG_EVERY == 0:
                print(f"  events: {original_rows:,} rows read...", file=sys.stderr)

            for field in ("timestamp", "visitorid", "event", "itemid"):
                if field not in row or not str(row.get(field, "")).strip():
                    missing[field] += 1

            source_event_counts[row.get("event", "").strip()] += 1

            key = event_row_key(row)
            if key in seen_keys:
                duplicate_rows_detected += 1
                duplicate_rows_removed += 1
                continue
            seen_keys.add(key)

            valid, reason = validate_event_row(row)
            if not valid:
                invalid_rows[reason or "invalid"] += 1
                continue

            ts = int(row["timestamp"])
            derived = ms_to_derived(ts)
            min_ts = ts if min_ts is None else min(min_ts, ts)
            max_ts = ts if max_ts is None else max(max_ts, ts)

            event = row["event"].strip()
            processed_event_counts[event] += 1
            visitors.add(int(row["visitorid"]))
            items.add(int(row["itemid"]))

            tid = row.get("transactionid", "").strip()
            if tid:
                transaction_ids.add(tid)

            writer.writerow(
                {
                    "timestamp": ts,
                    "visitorid": int(row["visitorid"]),
                    "event": event,
                    "itemid": int(row["itemid"]),
                    "transactionid": tid,
                    **derived,
                }
            )
            processed_rows += 1

    return {
        "source_file": RAW_EVENTS.name,
        "source_size_bytes": file_size_bytes(RAW_EVENTS),
        "original_row_count": original_rows,
        "processed_row_count": processed_rows,
        "duplicate_rows_detected": duplicate_rows_detected,
        "duplicate_rows_removed": duplicate_rows_removed,
        "invalid_rows_detected": sum(invalid_rows.values()),
        "invalid_rows_by_reason": dict(invalid_rows),
        "invalid_rows_removed": sum(invalid_rows.values()),
        "missing_values_in_source": dict(missing),
        "source_event_counts": dict(source_event_counts),
        "event_counts": dict(processed_event_counts),
        "unique_visitors": len(visitors),
        "unique_products": len(items),
        "transaction_event_count": processed_event_counts.get("transaction", 0),
        "distinct_transaction_ids": len(transaction_ids),
        "timestamp_range_ms": {"min": min_ts, "max": max_ts},
        "event_item_ids": items,
        "transaction_ids_sample_size": len(transaction_ids),
    }


def process_item_properties() -> dict:
    original_rows = 0
    processed_rows = 0
    invalid_rows = Counter()
    properties: Counter[str] = Counter()
    items: set[int] = set()
    min_ts: int | None = None
    max_ts: int | None = None
    missing = Counter()

    PROCESSED_ITEM_PROPERTIES.parent.mkdir(parents=True, exist_ok=True)

    with PROCESSED_ITEM_PROPERTIES.open("w", newline="", encoding="utf-8") as dst:
        writer = csv.DictWriter(dst, fieldnames=ITEM_PROPERTIES_OUTPUT_FIELDS)
        writer.writeheader()

        for source_path in (RAW_ITEM_PART1, RAW_ITEM_PART2):
            with source_path.open(newline="", encoding="utf-8", errors="replace") as src:
                reader = csv.DictReader(src)
                for row in reader:
                    original_rows += 1
                    if original_rows % 2_000_000 == 0:
                        print(f"  item_properties: {original_rows:,} rows read...", file=sys.stderr)

                    for col in ("timestamp", "itemid", "property", "value"):
                        if not str(row.get(col, "")).strip():
                            missing[col] += 1

                    valid, reason = validate_item_property_row(row)
                    if not valid:
                        invalid_rows[reason or "invalid"] += 1
                        continue

                    ts = int(row["timestamp"])
                    derived = ms_to_derived(ts)
                    min_ts = ts if min_ts is None else min(min_ts, ts)
                    max_ts = ts if max_ts is None else max(max_ts, ts)

                    item_id = int(row["itemid"])
                    items.add(item_id)
                    prop = row["property"].strip()
                    properties[prop] += 1

                    writer.writerow(
                        {
                            "timestamp": ts,
                            "itemid": item_id,
                            "property": prop,
                            "value": row["value"].strip(),
                            "datetime": derived["datetime"],
                            "date": derived["date"],
                        }
                    )
                    processed_rows += 1

    return {
        "source_files": [RAW_ITEM_PART1.name, RAW_ITEM_PART2.name],
        "source_size_bytes": file_size_bytes(RAW_ITEM_PART1) + file_size_bytes(RAW_ITEM_PART2),
        "original_row_count": original_rows,
        "processed_row_count": processed_rows,
        "invalid_rows_detected": sum(invalid_rows.values()),
        "invalid_rows_by_reason": dict(invalid_rows),
        "invalid_rows_removed": sum(invalid_rows.values()),
        "missing_values_in_source": dict(missing),
        "unique_items": len(items),
        "unique_properties": len(properties),
        "property_distribution_top_20": [
            {"property": name, "count": count} for name, count in properties.most_common(20)
        ],
        "timestamp_range_ms": {"min": min_ts, "max": max_ts},
        "property_item_ids": items,
    }


def process_category_tree() -> dict:
    rows: list[dict[str, str]] = []
    id_counter: Counter[str] = Counter()
    invalid_rows = Counter()
    category_ids: set[str] = set()
    parent_ids: set[str] = set()
    root_count = 0
    original_rows = 0

    with RAW_CATEGORY.open(newline="", encoding="utf-8", errors="replace") as src:
        reader = csv.DictReader(src)
        for row in reader:
            original_rows += 1
            cid = row.get("categoryid", "").strip()
            pid = row.get("parentid", "").strip()

            if not cid:
                invalid_rows["missing_categoryid"] += 1
                continue

            id_counter[cid] += 1
            if id_counter[cid] > 1:
                invalid_rows["duplicate_categoryid"] += 1
                continue

            category_ids.add(cid)
            if pid:
                parent_ids.add(pid)
            else:
                root_count += 1

            rows.append({"categoryid": cid, "parentid": pid})

    parents_not_in_tree = sorted(parent_ids - category_ids)

    PROCESSED_CATEGORY.parent.mkdir(parents=True, exist_ok=True)
    with PROCESSED_CATEGORY.open("w", newline="", encoding="utf-8") as dst:
        writer = csv.DictWriter(dst, fieldnames=CATEGORY_OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    return {
        "source_file": RAW_CATEGORY.name,
        "source_size_bytes": file_size_bytes(RAW_CATEGORY),
        "original_row_count": original_rows,
        "processed_row_count": len(rows),
        "invalid_rows_detected": sum(invalid_rows.values()),
        "invalid_rows_by_reason": dict(invalid_rows),
        "invalid_rows_removed": sum(invalid_rows.values()),
        "category_count": len(category_ids),
        "root_category_count": root_count,
        "parent_child_links": len(rows) - root_count,
        "parent_ids_not_in_categoryid_set": {
            "count": len(parents_not_in_tree),
            "sample": parents_not_in_tree[:10],
        },
        "category_ids": category_ids,
    }


def build_quality_report(
    events_stats: dict,
    item_stats: dict,
    category_stats: dict,
) -> dict:
    event_items: set[int] = events_stats.pop("event_item_ids")
    property_items: set[int] = item_stats.pop("property_item_ids")
    tree_ids: set[str] = category_stats.pop("category_ids")

    category_ids_in_properties: set[str] = set()
    for path in (RAW_ITEM_PART1, RAW_ITEM_PART2):
        with path.open(newline="", encoding="utf-8", errors="replace") as handle:
            for row in csv.DictReader(handle):
                if row.get("property", "").strip() == "categoryid":
                    category_ids_in_properties.add(row.get("value", "").strip())

    def fmt_ts(ms_min: int | None, ms_max: int | None) -> dict:
        def f(ms: int | None) -> str | None:
            if ms is None:
                return None
            return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )

        return {"min_ms": ms_min, "max_ms": ms_max, "min_utc": f(ms_min), "max_utc": f(ms_max)}

    return {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "notes": {
            "timestamps": "All epoch millisecond timestamps are interpreted as UTC.",
            "events": "Exact duplicate rows (full row key match) are removed in processed events only.",
            "transactions": "Multiple event rows may share the same transactionid (multi-item orders).",
        },
        "missing_values": {
            "events_source": events_stats.get("missing_values_in_source", {}),
            "item_properties_source": item_stats.get("missing_values_in_source", {}),
            "category_tree_source": {"parentid_empty_for_roots": category_stats.get("root_category_count", 0)},
        },
        "duplicates": {
            "events_exact_duplicates_detected": events_stats["duplicate_rows_detected"],
            "events_exact_duplicates_removed": events_stats["duplicate_rows_removed"],
            "item_properties_exact_duplicates_in_source": 0,
        },
        "invalid_records": {
            "events": events_stats.get("invalid_rows_by_reason", {}),
            "item_properties": item_stats.get("invalid_rows_by_reason", {}),
            "category_tree": category_stats.get("invalid_rows_by_reason", {}),
        },
        "timestamp_ranges": {
            "events": fmt_ts(
                events_stats["timestamp_range_ms"]["min"],
                events_stats["timestamp_range_ms"]["max"],
            ),
            "item_properties": fmt_ts(
                item_stats["timestamp_range_ms"]["min"],
                item_stats["timestamp_range_ms"]["max"],
            ),
        },
        "event_distribution": {
            "source_raw_counts": events_stats.get("source_event_counts", {}),
            "processed_events_counts": events_stats.get("event_counts", {}),
        },
        "cross_file_overlap": {
            "event_unique_products": len(event_items),
            "property_unique_products": len(property_items),
            "event_products_in_properties": len(event_items & property_items),
            "event_products_not_in_properties": len(event_items - property_items),
            "property_products_without_events": len(property_items - event_items),
            "category_ids_in_item_properties": len(category_ids_in_properties),
            "category_ids_in_properties_not_in_tree": len(category_ids_in_properties - tree_ids),
            "category_ids_in_tree_not_in_properties": len(tree_ids - category_ids_in_properties),
        },
        "category_relationship_issues": category_stats.get("parent_ids_not_in_categoryid_set", {}),
    }


def build_processing_summary(
    started_at: float,
    events_stats: dict,
    item_stats: dict,
    category_stats: dict,
) -> dict:
    duration = round(time.perf_counter() - started_at, 3)
    return {
        "processing_timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "processing_duration_seconds": duration,
        "source_files": {
            "events": RAW_EVENTS.name,
            "item_properties": [RAW_ITEM_PART1.name, RAW_ITEM_PART2.name],
            "category_tree": RAW_CATEGORY.name,
        },
        "original_row_counts": {
            "events": events_stats["original_row_count"],
            "item_properties": item_stats["original_row_count"],
            "category_tree": category_stats["original_row_count"],
        },
        "processed_row_counts": {
            "events": events_stats["processed_row_count"],
            "item_properties": item_stats["processed_row_count"],
            "category_tree": category_stats["processed_row_count"],
        },
        "duplicate_rows_detected": events_stats["duplicate_rows_detected"],
        "duplicate_rows_removed": events_stats["duplicate_rows_removed"],
        "invalid_rows_detected": {
            "events": events_stats["invalid_rows_detected"],
            "item_properties": item_stats["invalid_rows_detected"],
            "category_tree": category_stats["invalid_rows_detected"],
        },
        "invalid_rows_removed": {
            "events": events_stats["invalid_rows_removed"],
            "item_properties": item_stats["invalid_rows_removed"],
            "category_tree": category_stats["invalid_rows_removed"],
        },
        "unique_visitors": events_stats["unique_visitors"],
        "unique_products_in_events": events_stats["unique_products"],
        "event_counts": events_stats["event_counts"],
        "transaction_event_count": events_stats["transaction_event_count"],
        "distinct_transaction_ids": events_stats["distinct_transaction_ids"],
        "item_property_row_count": item_stats["processed_row_count"],
        "category_count": category_stats["category_count"],
        "output_files": {
            "events": str(PROCESSED_EVENTS.relative_to(PROCESSED_DIR.parent.parent)),
            "item_properties": str(PROCESSED_ITEM_PROPERTIES.relative_to(PROCESSED_DIR.parent.parent)),
            "category_tree": str(PROCESSED_CATEGORY.relative_to(PROCESSED_DIR.parent.parent)),
        },
    }


def main() -> None:
    started = time.perf_counter()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    for path in (RAW_EVENTS, RAW_ITEM_PART1, RAW_ITEM_PART2, RAW_CATEGORY):
        if not path.is_file():
            raise SystemExit(f"Missing raw file: {path}")

    print("Processing events...", file=sys.stderr)
    events_stats = process_events()

    print("Processing item properties (chunked stream)...", file=sys.stderr)
    item_stats = process_item_properties()

    print("Processing category tree...", file=sys.stderr)
    category_stats = process_category_tree()

    quality = build_quality_report(events_stats, item_stats, category_stats)
    summary = build_processing_summary(started, events_stats, item_stats, category_stats)

    PROCESSING_SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    DATA_QUALITY_REPORT.write_text(json.dumps(quality, indent=2), encoding="utf-8")

    print("\nProcessing complete.", file=sys.stderr)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
