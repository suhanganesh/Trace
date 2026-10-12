#!/usr/bin/env python3
"""
Read-only inspection of RetailRocket raw CSV files under data/raw/.

Does not modify raw data.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from dataset_utils import (
    EVENT_TYPES,
    RAW_CATEGORY,
    RAW_DIR,
    RAW_EVENTS,
    RAW_ITEM_PART1,
    RAW_ITEM_PART2,
    event_row_key,
    file_size_bytes,
)

CHUNK_LOG_EVERY = 500_000


def _ts_range_fmt(ms_min: int | None, ms_max: int | None) -> dict[str, str | None]:
    def fmt(ms: int | None) -> str | None:
        if ms is None:
            return None
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )

    return {"min_ms": ms_min, "max_ms": ms_max, "min_utc": fmt(ms_min), "max_utc": fmt(ms_max)}


def inspect_events(path: Path) -> dict:
    rows = 0
    missing = Counter()
    event_counts: Counter[str] = Counter()
    dup_counter: Counter[tuple[str, ...]] = Counter()
    visitors: set[int] = set()
    items: set[int] = set()
    transaction_ids: set[str] = set()
    min_ts: int | None = None
    max_ts: int | None = None
    invalid_ts = 0
    invalid_visitorid = 0
    invalid_itemid = 0
    invalid_event = 0
    tx_events = 0
    tx_with_id = 0
    non_tx_with_id = 0

    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        for row in reader:
            rows += 1
            if rows % CHUNK_LOG_EVERY == 0:
                print(f"  events: {rows:,} rows scanned...", file=sys.stderr)

            for col in columns:
                if not str(row.get(col, "")).strip():
                    missing[col] += 1

            dup_counter[event_row_key(row)] += 1

            event = row.get("event", "").strip()
            event_counts[event] += 1
            if event not in EVENT_TYPES:
                invalid_event += 1
            if event == "transaction":
                tx_events += 1
                if row.get("transactionid", "").strip():
                    tx_with_id += 1
                else:
                    pass
            elif row.get("transactionid", "").strip():
                non_tx_with_id += 1

            try:
                visitors.add(int(row["visitorid"]))
            except (TypeError, ValueError, KeyError):
                invalid_visitorid += 1

            try:
                items.add(int(row["itemid"]))
            except (TypeError, ValueError, KeyError):
                invalid_itemid += 1

            tid = row.get("transactionid", "").strip()
            if tid:
                transaction_ids.add(tid)

            try:
                ts = int(row["timestamp"])
                min_ts = ts if min_ts is None else min(min_ts, ts)
                max_ts = ts if max_ts is None else max(max_ts, ts)
            except (TypeError, ValueError, KeyError):
                invalid_ts += 1

    exact_dup_rows = sum(count - 1 for count in dup_counter.values() if count > 1)
    dup_groups = sum(1 for count in dup_counter.values() if count > 1)

    return {
        "file": str(path.name),
        "size_bytes": file_size_bytes(path),
        "rows": rows,
        "columns": columns,
        "missing_values": dict(missing),
        "event_distribution": dict(event_counts),
        "timestamp_range": _ts_range_fmt(min_ts, max_ts),
        "unique_visitors": len(visitors),
        "unique_products": len(items),
        "transaction_event_count": tx_events,
        "distinct_transaction_ids": len(transaction_ids),
        "transaction_events_with_id": tx_with_id,
        "non_transaction_events_with_id": non_tx_with_id,
        "exact_duplicate_rows": exact_dup_rows,
        "duplicate_key_groups": dup_groups,
        "invalid_timestamp_rows": invalid_ts,
        "invalid_visitorid_rows": invalid_visitorid,
        "invalid_itemid_rows": invalid_itemid,
        "invalid_event_rows": invalid_event,
    }


def inspect_item_properties(paths: list[Path]) -> dict:
    rows = 0
    missing = Counter()
    properties: Counter[str] = Counter()
    items: set[int] = set()
    dup_counter: Counter[tuple[str, ...]] = Counter()
    min_ts: int | None = None
    max_ts: int | None = None
    invalid_ts = 0
    invalid_itemid = 0
    columns: list[str] = []

    for path in paths:
        with path.open(newline="", encoding="utf-8", errors="replace") as handle:
            reader = csv.DictReader(handle)
            columns = reader.fieldnames or []
            for row in reader:
                rows += 1
                if rows % 2_000_000 == 0:
                    print(f"  item_properties: {rows:,} rows scanned...", file=sys.stderr)

                for col in columns:
                    if not str(row.get(col, "")).strip():
                        missing[col] += 1

                dup_counter[
                    (
                        row.get("timestamp", "").strip(),
                        row.get("itemid", "").strip(),
                        row.get("property", "").strip(),
                        row.get("value", "").strip(),
                    )
                ] += 1

                properties[row.get("property", "").strip()] += 1

                try:
                    items.add(int(row["itemid"]))
                except (TypeError, ValueError, KeyError):
                    invalid_itemid += 1

                try:
                    ts = int(row["timestamp"])
                    min_ts = ts if min_ts is None else min(min_ts, ts)
                    max_ts = ts if max_ts is None else max(max_ts, ts)
                except (TypeError, ValueError, KeyError):
                    invalid_ts += 1

    exact_dup_rows = sum(count - 1 for count in dup_counter.values() if count > 1)
    top_properties = properties.most_common(20)

    return {
        "files": [p.name for p in paths],
        "total_size_bytes": sum(file_size_bytes(p) for p in paths),
        "rows": rows,
        "columns": columns,
        "missing_values": dict(missing),
        "unique_items": len(items),
        "unique_properties": len(properties),
        "property_distribution_top_20": [
            {"property": name, "count": count} for name, count in top_properties
        ],
        "timestamp_range": _ts_range_fmt(min_ts, max_ts),
        "exact_duplicate_rows": exact_dup_rows,
        "invalid_timestamp_rows": invalid_ts,
        "invalid_itemid_rows": invalid_itemid,
    }


def inspect_category_tree(path: Path) -> dict:
    rows = 0
    missing = Counter()
    category_ids: set[str] = set()
    parent_ids: set[str] = set()
    id_counter: Counter[str] = Counter()
    root_count = 0
    child_links = 0

    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        for row in reader:
            rows += 1
            for col in columns:
                if not str(row.get(col, "")).strip():
                    missing[col] += 1

            cid = row.get("categoryid", "").strip()
            pid = row.get("parentid", "").strip()
            id_counter[cid] += 1
            if cid:
                category_ids.add(cid)
            if pid:
                parent_ids.add(pid)
                child_links += 1
            else:
                root_count += 1

    duplicate_category_ids = sum(c - 1 for c in id_counter.values() if c > 1)
    parents_not_in_tree = sorted(parent_ids - category_ids)

    return {
        "file": str(path.name),
        "size_bytes": file_size_bytes(path),
        "rows": rows,
        "columns": columns,
        "missing_values": dict(missing),
        "category_count": len(category_ids),
        "unique_parent_ids": len(parent_ids),
        "root_category_count": root_count,
        "parent_child_links": child_links,
        "duplicate_categoryid_rows": duplicate_category_ids,
        "parent_ids_not_in_categoryid_set": {
            "count": len(parents_not_in_tree),
            "sample": parents_not_in_tree[:10],
        },
    }


def cross_file_checks(event_items: set[int], property_items: set[int], tree_ids: set[str]) -> dict:
    category_ids_in_properties: set[str] = set()
    for path in (RAW_ITEM_PART1, RAW_ITEM_PART2):
        with path.open(newline="", encoding="utf-8", errors="replace") as handle:
            for row in csv.DictReader(handle):
                if row.get("property", "").strip() == "categoryid":
                    category_ids_in_properties.add(row.get("value", "").strip())

    return {
        "event_unique_products": len(event_items),
        "property_unique_products": len(property_items),
        "event_products_in_properties": len(event_items & property_items),
        "event_products_not_in_properties": len(event_items - property_items),
        "property_products_without_events": len(property_items - event_items),
        "category_ids_in_item_properties": len(category_ids_in_properties),
        "category_ids_in_properties_not_in_tree": len(category_ids_in_properties - tree_ids),
        "category_ids_in_tree_not_in_properties": len(tree_ids - category_ids_in_properties),
    }


def collect_event_item_ids(path: Path) -> set[int]:
    items: set[int] = set()
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle):
            try:
                items.add(int(row["itemid"]))
            except (TypeError, ValueError, KeyError):
                continue
    return items


def collect_property_item_ids(paths: list[Path]) -> set[int]:
    items: set[int] = set()
    for path in paths:
        with path.open(newline="", encoding="utf-8", errors="replace") as handle:
            for row in csv.DictReader(handle):
                try:
                    items.add(int(row["itemid"]))
                except (TypeError, ValueError, KeyError):
                    continue
    return items


def collect_tree_ids(path: Path) -> set[str]:
    ids: set[str] = set()
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle):
            cid = row.get("categoryid", "").strip()
            if cid:
                ids.add(cid)
    return ids


def print_report(report: dict) -> None:
    print("=" * 60)
    print("TRACE — DATASET INSPECTION REPORT (data/raw/)")
    print("=" * 60)

    for key in ("events", "item_properties", "category_tree"):
        section = report[key]
        print(f"\n--- {key.upper().replace('_', ' ')} ---")
        print(json.dumps(section, indent=2, default=str))

    print("\n--- CROSS-FILE CHECKS ---")
    print(json.dumps(report["cross_file"], indent=2, default=str))
    print()


def run_inspection() -> dict:
    if not RAW_DIR.is_dir():
        raise SystemExit(f"Raw directory not found: {RAW_DIR}")

    required = [RAW_EVENTS, RAW_ITEM_PART1, RAW_ITEM_PART2, RAW_CATEGORY]
    missing_files = [str(p) for p in required if not p.is_file()]
    if missing_files:
        raise SystemExit(f"Missing raw files: {missing_files}")

    print("Inspecting events...", file=sys.stderr)
    events = inspect_events(RAW_EVENTS)
    print("Inspecting item properties...", file=sys.stderr)
    item_properties = inspect_item_properties([RAW_ITEM_PART1, RAW_ITEM_PART2])
    print("Inspecting category tree...", file=sys.stderr)
    category_tree = inspect_category_tree(RAW_CATEGORY)

    print("Cross-file checks (loading item id sets)...", file=sys.stderr)
    event_items = collect_event_item_ids(RAW_EVENTS)
    property_items = collect_property_item_ids([RAW_ITEM_PART1, RAW_ITEM_PART2])
    tree_ids = collect_tree_ids(RAW_CATEGORY)
    cross_file = cross_file_checks(event_items, property_items, tree_ids)

    return {
        "inspected_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "raw_directory": str(RAW_DIR),
        "events": events,
        "item_properties": item_properties,
        "category_tree": category_tree,
        "cross_file": cross_file,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Trace raw RetailRocket CSV files.")
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Optional path to write the full inspection report as JSON.",
    )
    args = parser.parse_args()

    report = run_inspection()
    print_report(report)

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Wrote JSON report to {args.json_out}")


if __name__ == "__main__":
    main()
