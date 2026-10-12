# Trace — Data Processing

This document describes how RetailRocket raw CSV files under `data/raw/` are validated, cleaned, and written to `data/processed/` for MongoDB import (Phase 3).

Raw files are **never modified**.

## Raw dataset

| File | Role |
|------|------|
| `events.csv` | User interaction stream (`view`, `addtocart`, `transaction`) |
| `item_properties_part1.csv` | Item attribute history (part 1, EAV rows) |
| `item_properties_part2.csv` | Item attribute history (part 2, same schema) |
| `category_tree.csv` | Category hierarchy (`categoryid`, `parentid`) |

Phase 1 inspection confirmed ~2.76M events, ~20.3M property rows, and 1,669 categories.

## Pipeline architecture

```text
Raw CSV (data/raw/)
        ↓
Inspection (inspect_dataset.py — read-only)
        ↓
Validation (process_dataset.py)
        ↓
Cleaning (exact duplicate removal for events only)
        ↓
Derived fields (UTC timestamps from epoch ms)
        ↓
Processed CSV (data/processed/)
        ↓
MongoDB (Phase 3 — import_to_mongodb.py)
```

## Scripts

### `scripts/inspect_dataset.py`

Read-only report of file sizes, row counts, columns, missing values, duplicates, event distribution, timestamp ranges, entity counts, and cross-file overlap. Optional JSON export via `--json-out`.

### `scripts/process_dataset.py`

Production pipeline that writes:

- `data/processed/events.csv`
- `data/processed/item_properties.csv`
- `data/processed/category_tree.csv`
- `data/processed/processing_summary.json`
- `data/processed/data_quality_report.json`

Uses streaming CSV I/O (no full in-memory load of item properties).

### `scripts/dataset_utils.py`

Shared paths, constants, and UTC timestamp helpers.

## Duplicate handling (events)

Exact duplicates are rows with the same:

`(timestamp, visitorid, event, itemid, transactionid)`

The raw dataset contains duplicate rows. The processor:

1. Counts each duplicate occurrence after the first.
2. Reports counts in `processing_summary.json` and `data_quality_report.json`.
3. Removes duplicate rows from **processed** `events.csv` only (keeps first occurrence).

Raw `data/raw/events.csv` is unchanged.

## Timestamp handling

Source timestamps are **Unix epoch milliseconds**. They are interpreted as **UTC** (not local time).

**Events** — preserved column `timestamp`, plus derived:

- `datetime` (ISO-8601 UTC with `Z`)
- `date`, `year`, `month`, `day`, `hour`, `day_of_week`

**Item properties** — preserved `timestamp`, plus `datetime` and `date`.

## Event types

Values are kept as in the source: `view`, `addtocart`, `transaction` (no renaming).

## Transaction handling

- `transactionid` is only present for `transaction` events in the source.
- Empty transaction IDs remain empty in CSV output.
- Multiple event rows may share one `transactionid` (multi-item orders); the processor does not collapse them.

## Item properties

Part 1 and part 2 are streamed sequentially into a single `item_properties.csv`. The EAV shape is preserved (`property`, `value`). Invalid rows (bad timestamp, missing property/value, etc.) are counted and skipped; counts appear in the JSON reports.

## Category tree

Processed file keeps `categoryid` and `parentid`. Root categories retain an empty `parentid` (no invented parent IDs). Duplicate or missing `categoryid` rows are rejected and reported.

## Validation

| Dataset | Checks |
|---------|--------|
| Events | Valid ms timestamp, integer visitor/item IDs, known event type, transaction ID rules |
| Item properties | Valid timestamp, item ID, non-empty property and value |
| Category tree | Non-empty unique `categoryid` |

Validation failures are **reported** in JSON; they are not silently ignored.

## Manual execution

From the project root:

```powershell
python scripts/inspect_dataset.py
python scripts/process_dataset.py
```

Optional inspection JSON:

```powershell
python scripts/inspect_dataset.py --json-out data/processed/inspection_report.json
```

Processing item properties (~20M rows) may take several minutes depending on disk speed.

## Expected results (verify after processing)

Values come from your run; Phase 1 baselines for comparison:

| Metric | Expected (approx.) |
|--------|-------------------|
| Raw events rows | 2,756,101 |
| Duplicate rows removed | 460 |
| Processed events rows | 2,755,641 |
| Combined item property rows | 20,275,902 (if none invalid) |
| Category rows | 1,669 |

Check `data/processed/processing_summary.json` for computed counts and duration.

## Limitations

- Cross-file overlap in `inspect_dataset.py` loads unique item ID sets into memory (~hundreds of thousands of integers — acceptable on a laptop).
- Event deduplication keeps a key set in memory for ~2.76M keys during `process_dataset.py`.
- Item properties are not deduplicated (Phase 1 found zero exact duplicates on the full key).
