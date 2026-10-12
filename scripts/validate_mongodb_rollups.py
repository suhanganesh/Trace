#!/usr/bin/env python3
"""
Validate compact rollup artifacts against processing_summary.json (read-only).

Does NOT rebuild rollups.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from build_mongodb_rollups import validate_rollups
from dataset_utils import (
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

ARTIFACT_FILES = {
    "analytics_global": ROLLUP_ANALYTICS_GLOBAL,
    "product_metrics": ROLLUP_PRODUCT_METRICS,
    "product_metadata": ROLLUP_PRODUCT_METADATA,
    "time_series_daily": ROLLUP_TIME_DAILY,
    "time_series_hourly": ROLLUP_TIME_HOURLY,
    "category_tree": ROLLUP_CATEGORY,
}


def count_jsonl_lines(path: Path) -> int:
    count = 0
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def main() -> None:
    report: dict[str, Any] = {
        "artifacts_present": {},
        "artifact_line_counts": {},
        "rollup_validation_file": {},
        "summary_cross_check": {},
        "passed": True,
        "errors": [],
    }

    if not PROCESSING_SUMMARY.is_file():
        raise SystemExit(f"Missing {PROCESSING_SUMMARY}")

    summary = json.loads(PROCESSING_SUMMARY.read_text(encoding="utf-8"))

    for name, path in ARTIFACT_FILES.items():
        exists = path.is_file()
        report["artifacts_present"][name] = exists
        if not exists:
            report["passed"] = False
            report["errors"].append(f"Missing artifact: {path}")
            continue
        if path.suffix == ".jsonl":
            report["artifact_line_counts"][name] = count_jsonl_lines(path)

    if not ROLLUP_VALIDATION.is_file():
        report["passed"] = False
        report["errors"].append(f"Missing {ROLLUP_VALIDATION}")
    else:
        rollup_validation = json.loads(ROLLUP_VALIDATION.read_text(encoding="utf-8"))
        report["rollup_validation_file"] = {
            "validation_passed": rollup_validation.get("validation_passed"),
        }
        if not rollup_validation.get("validation_passed"):
            report["passed"] = False
            report["errors"].append("rollup_validation.json reports validation_passed=false")

    if ROLLUP_MANIFEST.is_file():
        manifest = json.loads(ROLLUP_MANIFEST.read_text(encoding="utf-8"))
        expected_counts = manifest.get("artifact_counts", {})
        report["manifest_counts"] = expected_counts
        for name, path in ARTIFACT_FILES.items():
            if name == "analytics_global":
                expected = expected_counts.get("analytics_global_documents", 1)
                actual = 1 if ROLLUP_ANALYTICS_GLOBAL.is_file() else 0
            else:
                expected = expected_counts.get(name)
                actual = report["artifact_line_counts"].get(name)
            if expected is not None and actual is not None and expected != actual:
                report["passed"] = False
                report["errors"].append(
                    f"Artifact count mismatch for {name}: manifest={expected}, lines={actual}"
                )

    if ROLLUP_ANALYTICS_GLOBAL.is_file():
        analytics_global = json.loads(ROLLUP_ANALYTICS_GLOBAL.read_text(encoding="utf-8"))
        category_count = report["artifact_line_counts"].get(
            "category_tree",
            count_jsonl_lines(ROLLUP_CATEGORY) if ROLLUP_CATEGORY.is_file() else 0,
        )
        cross = validate_rollups(analytics_global, category_count=category_count)
        report["summary_cross_check"] = cross
        if not cross.get("validation_passed"):
            report["passed"] = False
            report["errors"].append("analytics_global.json does not match processing_summary.json")

    report["processing_summary_reference"] = {
        "total_events": summary.get("processed_row_counts", {}).get("events"),
        "unique_visitors": summary.get("unique_visitors"),
        "unique_products_in_events": summary.get("unique_products_in_events"),
        "views": summary.get("event_counts", {}).get("view"),
        "addtocart": summary.get("event_counts", {}).get("addtocart"),
        "transactions": summary.get("transaction_event_count"),
        "categories": summary.get("category_count")
        or summary.get("processed_row_counts", {}).get("category_tree"),
    }

    ROLLUP_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ROLLUP_DIR / "rollup_validation_run.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
