#!/usr/bin/env python3
"""
Read-only validation of compact MongoDB deployment and API/overview consistency.

Does NOT modify MongoDB.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _SCRIPTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from dataset_utils import ANALYTICS_IMPORT_REPORT, PROCESSING_SUMMARY, ROLLUP_MANIFEST

COMPACT_COLLECTIONS = (
    "analytics_global",
    "product_metrics",
    "product_metadata",
    "time_series_daily",
    "time_series_hourly",
    "category_tree",
)

EXPECTED_INDEXES: dict[str, list[str]] = {
    "product_metrics": [
        "idx_item_id_unique",
        "idx_views_desc",
        "idx_add_to_cart_desc",
        "idx_transactions_desc",
    ],
    "product_metadata": ["idx_item_id_unique"],
    "time_series_daily": ["idx_date"],
    "time_series_hourly": ["idx_date_hour"],
    "category_tree": ["idx_categoryid_unique"],
}


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_processing_summary() -> dict[str, Any]:
    if not PROCESSING_SUMMARY.is_file():
        raise SystemExit(f"Missing {PROCESSING_SUMMARY}")
    return json.loads(PROCESSING_SUMMARY.read_text(encoding="utf-8"))


def expected_overview_from_summary(summary: dict[str, Any]) -> dict[str, int]:
    event_counts = summary.get("event_counts", {})
    return {
        "total_events": int(summary["processed_row_counts"]["events"]),
        "unique_visitors": int(summary["unique_visitors"]),
        "unique_products": int(summary["unique_products_in_events"]),
        "total_views": int(event_counts["view"]),
        "total_add_to_cart": int(event_counts["addtocart"]),
        "total_transactions": int(summary["transaction_event_count"]),
    }


def fetch_api_overview(base_url: str) -> dict[str, Any] | None:
    url = f"{base_url.rstrip('/')}/api/overview"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    parser = argparse.ArgumentParser(description="Validate compact MongoDB deployment (read-only).")
    parser.add_argument(
        "--api-base-url",
        default=os.environ.get("TRACE_API_BASE_URL", "http://127.0.0.1:8000"),
        help="Optional running API base URL for /api/overview cross-check",
    )
    parser.add_argument(
        "--skip-api",
        action="store_true",
        help="Skip HTTP overview consistency check",
    )
    args = parser.parse_args()

    deployment_mode = os.environ.get("MONGODB_DEPLOYMENT_MODE", "compact").strip().lower()
    mongodb_uri = os.environ.get("MONGODB_URI", "").strip()
    database_name = os.environ.get("MONGODB_DATABASE", "retailrocket_analytics").strip()

    report: dict[str, Any] = {
        "deployment_mode_env": deployment_mode,
        "database": database_name,
        "passed": True,
        "errors": [],
        "warnings": [],
        "collection_counts": {},
        "indexes": {},
        "overview_consistency": {},
        "api_overview_consistency": {},
    }

    if deployment_mode != "compact":
        report["warnings"].append(
            f"MONGODB_DEPLOYMENT_MODE is '{deployment_mode}', expected 'compact' for this validation."
        )

    if not mongodb_uri:
        raise SystemExit("MONGODB_URI is not set in environment or .env")

    summary = load_processing_summary()
    expected_overview = expected_overview_from_summary(summary)
    expected_counts: dict[str, int | None] = {"analytics_global": 1}

    if ROLLUP_MANIFEST.is_file():
        manifest = json.loads(ROLLUP_MANIFEST.read_text(encoding="utf-8"))
        artifact = manifest.get("artifact_counts", {})
        expected_counts.update(
            {
                "product_metrics": artifact.get("product_metrics"),
                "product_metadata": artifact.get("product_metadata"),
                "time_series_daily": artifact.get("time_series_daily"),
                "time_series_hourly": artifact.get("time_series_hourly"),
                "category_tree": artifact.get("category_tree"),
            }
        )
    elif ANALYTICS_IMPORT_REPORT.is_file():
        import_report = json.loads(ANALYTICS_IMPORT_REPORT.read_text(encoding="utf-8"))
        imported = import_report.get("documents_imported", {})
        expected_counts.update({k: imported.get(k) for k in COMPACT_COLLECTIONS if k in imported})

    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    except ImportError as exc:
        raise SystemExit("Install pymongo: pip install pymongo") from exc

    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10_000)
    try:
        client.admin.command("ping")
    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        raise SystemExit(f"MongoDB is not reachable: {exc}") from exc

    db = client[database_name]
    existing_names = set(db.list_collection_names())

    for legacy in ("events", "item_properties"):
        if legacy in existing_names:
            legacy_count = db[legacy].estimated_document_count()
            report["warnings"].append(
                f"Legacy collection '{legacy}' exists ({legacy_count:,} docs). "
                "Not required for compact mode; consumes Atlas quota if present."
            )

    mongo_overview: dict[str, int] | None = None
    for name in COMPACT_COLLECTIONS:
        if name not in existing_names:
            report["passed"] = False
            report["errors"].append(f"Missing compact collection: {name}")
            continue
        count = db[name].count_documents({})
        report["collection_counts"][name] = count
        expected = expected_counts.get(name)
        if expected is not None and count != expected:
            report["passed"] = False
            report["errors"].append(
                f"Document count mismatch for {name}: expected={expected}, actual={count}"
            )

        if name in EXPECTED_INDEXES:
            index_names = {idx["name"] for idx in db[name].list_indexes()}
            report["indexes"][name] = sorted(index_names)
            for required in EXPECTED_INDEXES[name]:
                if required not in index_names:
                    report["passed"] = False
                    report["errors"].append(f"Missing index {required} on {name}")

    global_doc = db["analytics_global"].find_one({}) if "analytics_global" in existing_names else None
    if global_doc:
        overview = global_doc.get("overview", {})
        mongo_overview = {
            "total_events": int(overview.get("total_events", 0)),
            "unique_visitors": int(overview.get("unique_visitors", 0)),
            "unique_products": int(overview.get("unique_products", 0)),
            "total_views": int(overview.get("total_views", 0)),
            "total_add_to_cart": int(overview.get("total_add_to_cart", 0)),
            "total_transactions": int(overview.get("total_transactions", 0)),
        }
        overview_checks = {}
        for key, expected in expected_overview.items():
            actual = mongo_overview.get(key)
            overview_checks[key] = {
                "expected_from_processing_summary": expected,
                "mongodb_analytics_global": actual,
                "match": actual == expected,
            }
            if actual != expected:
                report["passed"] = False
                report["errors"].append(
                    f"MongoDB overview mismatch for {key}: summary={expected}, mongo={actual}"
                )
        report["overview_consistency"] = overview_checks

    if not args.skip_api:
        api_overview = fetch_api_overview(args.api_base_url)
        if api_overview is None:
            report["warnings"].append(
                f"Could not fetch {args.api_base_url}/api/overview "
                "(start uvicorn to enable API consistency check)."
            )
        else:
            api_checks = {}
            for key, expected in expected_overview.items():
                actual = api_overview.get(key)
                api_checks[key] = {
                    "expected_from_processing_summary": expected,
                    "api_overview": actual,
                    "match": actual == expected,
                }
                if actual != expected:
                    report["passed"] = False
                    report["errors"].append(
                        f"API overview mismatch for {key}: summary={expected}, api={actual}"
                    )
            report["api_overview_consistency"] = api_checks
            if mongo_overview:
                api_mongo_checks = {}
                for key in expected_overview:
                    api_val = api_overview.get(key)
                    mongo_val = mongo_overview.get(key)
                    api_mongo_checks[key] = {
                        "api": api_val,
                        "mongodb": mongo_val,
                        "match": api_val == mongo_val,
                    }
                    if api_val != mongo_val:
                        report["passed"] = False
                        report["errors"].append(
                            f"API vs MongoDB mismatch for {key}: api={api_val}, mongo={mongo_val}"
                        )
                report["api_vs_mongodb_overview"] = api_mongo_checks

    client.close()

    out_path = PROJECT_ROOT / "data" / "mongodb_free_tier" / "deployment_validation_run.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
