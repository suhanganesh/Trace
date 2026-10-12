# Trace — MongoDB Analytics (Compact Mode)

This document describes how dashboard metrics are produced when `MONGODB_DEPLOYMENT_MODE=compact` (default). Metrics are computed from **100% of processed events** during offline rollup build; the API reads compact collections instead of scanning millions of event documents.

## Data sources

| Layer | Location | Role |
|-------|----------|------|
| Authoritative facts | `data/processed/events.csv`, `item_properties.csv`, `category_tree.csv` | Full dataset; unchanged by rollup build |
| Rollup artifacts | `data/mongodb_free_tier/` | MongoDB-ready JSON/JSONL |
| Serving store | MongoDB collections listed in `MONGODB_ARCHITECTURE.md` | Low-latency reads for FastAPI |

## Rollup build (`build_mongodb_rollups.py`)

### Event stream (all 2,755,641 rows)

Single pass over `events.csv` (chunked CSV read, not full in-memory load):

1. **Visitor aggregation** — per `visitorid`: event totals, views, add_to_cart, transactions, boolean stage flags.  
2. **Product aggregation** — per `itemid`: views, add_to_cart, transactions.  
3. **Time aggregation** — daily and hourly buckets using processed `date` / `hour` (UTC).  
4. **Global document** — overview, funnel, behavior (including activity buckets from `ACTIVITY_BOUNDARIES` in `dataset_utils.py`), report peaks.

### Item properties stream (~20.3M rows)

Only rows where `property` is `categoryid` or `available`, and `itemid` appears in the event product set. Keep **latest timestamp** per property; no historical EAV in MongoDB.

### Category tree

All 1,669 categories copied to `category_tree.jsonl`.

### Validation

`rollup_validation.json` compares rollup totals to `processing_summary.json` (events, event types, uniques, transactions, category count, date range when present).

## API mapping (compact)

| Endpoint | MongoDB source | Notes |
|----------|----------------|-------|
| `/api/overview` | `analytics_global.overview` | No aggregation at request time |
| `/api/funnel` | `analytics_global.funnel` | Visitor-based stages (not event counts) |
| `/api/behavior` | `analytics_global.behavior` | Buckets + top 15 precomputed |
| `/api/products` | `product_metrics` | `$sort` + `$limit` on indexed fields |
| `/api/products/{id}` | `product_metrics` + `product_metadata` | 404 if no metrics row |
| `/api/time-series` | `time_series_daily` or `time_series_hourly` | `$match` on `date` when filtered |
| `/api/report` | Composes global + product_metrics aggregations + time series | High-view/low-conversion via `$setWindowFields` on `product_metrics` |
| `/api/dataset-info` | `processing_summary.json` + compact collection counts | Distinguishes full dataset vs MongoDB storage |

## Visitor funnel methodology

Stages count **unique visitors** with at least one event of each type:

1. View  
2. Add to cart  
3. Transaction  

Percentages in the API are relative to view visitors; drop-off is between stages.

## Activity buckets

Same boundaries as the original behavior module (`ACTIVITY_BOUNDARIES`): visitors grouped by total event count into labeled buckets for the behavior chart.

## Product conversion

UI conversion = `transactions / views` per product (transaction **events**, not unique orders).

## High-view / low-conversion (report)

MongoDB aggregation on `product_metrics`:

- Cohort: products with ≥50 views  
- Top quartile by views  
- Conversion below cohort median  
- Requires MongoDB 5.0+ (`$setWindowFields`)

## Legacy note

The previous design aggregated directly on the `events` and `item_properties` collections after full import. That approach remains documented in git history and `import_to_mongodb.py` for local full-storage experiments; Atlas Free deployments should use compact rollups only.
