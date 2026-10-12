#!/usr/bin/env python3
"""
Import compact Trace analytics artifacts into MongoDB (Atlas free tier).

Only drops/imports compact collections — never events or item_properties.
"""

from __future__ import annotations

import argparse
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
    ANALYTICS_IMPORT_REPORT,
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

COMPACT_COLLECTIONS = (
    "analytics_global",
    "product_metrics",
    "product_metadata",
    "time_series_daily",
    "time_series_hourly",
    "category_tree",
)


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def insert_jsonl_batched(collection: Any, path: Path, batch_size: int) -> int:
    batch: list[dict[str, Any]] = []
    inserted = 0
    for doc in iter_jsonl(path):
        batch.append(doc)
        if len(batch) >= batch_size:
            result = collection.insert_many(batch, ordered=False)
            inserted += len(result.inserted_ids)
            batch.clear()
    if batch:
        result = collection.insert_many(batch, ordered=False)
        inserted += len(result.inserted_ids)
    return inserted


def create_compact_indexes(db: Any) -> list[dict[str, Any]]:
    plan = [
        ("product_metrics", "idx_item_id_unique", {"item_id": 1}, {"unique": True}),
        ("product_metrics", "idx_views_desc", {"views": -1}, {}),
        ("product_metrics", "idx_add_to_cart_desc", {"add_to_cart": -1}, {}),
        ("product_metrics", "idx_transactions_desc", {"transactions": -1}, {}),
        ("product_metadata", "idx_item_id_unique", {"item_id": 1}, {"unique": True}),
        ("time_series_daily", "idx_date", {"date": 1}, {}),
        ("time_series_hourly", "idx_date_hour", {"date": 1, "hour": 1}, {"unique": True}),
        ("category_tree", "idx_categoryid_unique", {"categoryid": 1}, {"unique": True}),
    ]
    created = []
    for coll_name, index_name, keys, options in plan:
        started = time.perf_counter()
        name = db[coll_name].create_index(list(keys.items()), name=index_name, **options)
        created.append(
            {
                "collection": coll_name,
                "index_name": name,
                "keys": keys,
                "duration_seconds": round(time.perf_counter() - started, 3),
            }
        )
    return created


def ensure_artifacts() -> dict[str, Any]:
    required = {
        "analytics_global": ROLLUP_ANALYTICS_GLOBAL,
        "product_metrics": ROLLUP_PRODUCT_METRICS,
        "product_metadata": ROLLUP_PRODUCT_METADATA,
        "time_series_daily": ROLLUP_TIME_DAILY,
        "time_series_hourly": ROLLUP_TIME_HOURLY,
        "category_tree": ROLLUP_CATEGORY,
    }
    missing = [name for name, path in required.items() if not path.is_file()]
    if missing:
        raise SystemExit(
            "Missing rollup artifacts: "
            + ", ".join(missing)
            + ". Run: python scripts/build_mongodb_rollups.py"
        )
    manifest = json.loads(ROLLUP_MANIFEST.read_text(encoding="utf-8")) if ROLLUP_MANIFEST.is_file() else {}
    return manifest


def main() -> None:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    parser = argparse.ArgumentParser(description="Import compact Trace analytics into MongoDB.")
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop compact collections before import (never drops events/item_properties).",
    )
    args = parser.parse_args()

    mongodb_uri = os.environ.get("MONGODB_URI", "").strip()
    database_name = os.environ.get("MONGODB_DATABASE", "retailrocket_analytics").strip()
    batch_size = int(os.environ.get("MONGODB_BATCH_SIZE", "10000"))
    if not mongodb_uri:
        raise SystemExit("MONGODB_URI is not set.")
    if batch_size < 100 or batch_size > 50_000:
        raise SystemExit("MONGODB_BATCH_SIZE must be between 100 and 50000.")

    manifest = ensure_artifacts()
    expected = manifest.get("artifact_counts", {})

    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    except ImportError as exc:
        raise SystemExit("Install pymongo: pip install pymongo") from exc

    report: dict[str, Any] = {
        "deployment_mode": "compact",
        "database": database_name,
        "collections": list(COMPACT_COLLECTIONS),
        "batch_size": batch_size,
        "import_started_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "documents_imported": {},
        "indexes_created": [],
        "validation": {},
        "errors": [],
    }
    started = time.perf_counter()

    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10_000)
    try:
        client.admin.command("ping")
    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        raise SystemExit(f"MongoDB is not reachable: {exc}") from exc

    db = client[database_name]

    existing = {name: db[name].estimated_document_count() for name in COMPACT_COLLECTIONS}
    if any(count > 0 for count in existing.values()):
        if not args.drop:
            raise SystemExit(
                f"Compact collections already contain data: {existing}. Re-run with --drop."
            )
        for name in COMPACT_COLLECTIONS:
            db[name].drop()

    global_doc = json.loads(ROLLUP_ANALYTICS_GLOBAL.read_text(encoding="utf-8"))
    db["analytics_global"].insert_one(global_doc)
    report["documents_imported"]["analytics_global"] = 1

    report["documents_imported"]["product_metrics"] = insert_jsonl_batched(
        db["product_metrics"], ROLLUP_PRODUCT_METRICS, batch_size
    )
    report["documents_imported"]["product_metadata"] = insert_jsonl_batched(
        db["product_metadata"], ROLLUP_PRODUCT_METADATA, batch_size
    )
    report["documents_imported"]["time_series_daily"] = insert_jsonl_batched(
        db["time_series_daily"], ROLLUP_TIME_DAILY, batch_size
    )
    report["documents_imported"]["time_series_hourly"] = insert_jsonl_batched(
        db["time_series_hourly"], ROLLUP_TIME_HOURLY, batch_size
    )
    report["documents_imported"]["category_tree"] = insert_jsonl_batched(
        db["category_tree"], ROLLUP_CATEGORY, batch_size
    )

    report["indexes_created"] = create_compact_indexes(db)

    count_checks = {}
    for name in COMPACT_COLLECTIONS:
        actual = db[name].count_documents({})
        expected_count = expected.get(name, expected.get("product_metrics") if name == "product_metrics" else None)
        if name == "analytics_global":
            expected_count = 1
        count_checks[name] = {"expected_from_manifest": expected_count, "actual": actual}
    report["validation"]["document_counts"] = count_checks
    if ROLLUP_VALIDATION.is_file():
        report["validation"]["rollup_validation"] = json.loads(
            ROLLUP_VALIDATION.read_text(encoding="utf-8")
        )

    report["import_finished_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report["duration_seconds"] = round(time.perf_counter() - started, 3)

    ROLLUP_DIR.mkdir(parents=True, exist_ok=True)
    ANALYTICS_IMPORT_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
