# Trace — Backend API

FastAPI backend for **Trace**. In **compact mode** (default), metrics are served from pre-aggregated MongoDB collections and lightweight aggregations on `product_metrics` / time series— not from raw event scans.

## Architecture

```text
React dashboard
      ↓ HTTP GET
Trace API (FastAPI, backend/app)
      ↓ PyMongo (compact collections)
MongoDB (retailrocket_analytics)
      ↓
Aggregated JSON
```

| Layer | Location | Role |
|-------|----------|------|
| Routes | `backend/app/routes/` | HTTP, query validation, dependencies |
| Analytics | `backend/app/analytics/` | Map MongoDB documents to Pydantic responses |
| Database | `backend/app/database/mongodb.py` | Collection accessors, `analytics_global` reader |
| Schemas | `backend/app/schemas/responses.py` | Response models (unchanged for frontend) |

## Environment variables

Configure in project root `.env` (see `.env.example`):

| Variable | Required | Description |
|----------|----------|-------------|
| `MONGODB_URI` | Yes | MongoDB connection string (e.g. Atlas) |
| `MONGODB_DATABASE` | No | Default `retailrocket_analytics` |
| `MONGODB_DEPLOYMENT_MODE` | No | Default `compact` — compact rollup collections |
| `API_HOST` | No | Default `127.0.0.1` |
| `API_PORT` | No | Default `8000` |
| `FRONTEND_URL` | No | CORS origin |

Credentials are never returned by the API.

## Prerequisites (compact)

1. `python scripts/process_dataset.py`  
2. `python scripts/build_mongodb_rollups.py`  
3. `python scripts/import_analytics_to_mongodb.py --drop`

## Manual startup

```powershell
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Endpoints

All routes prefixed with `/api`. Analytics routes use `require_compact_analytics` (503 if `analytics_global` is empty).

### `GET /api/health`

Service and database ping. **503** when MongoDB unreachable.

### `GET /api/overview`

Reads `analytics_global.overview`: totals, uniques, visitor conversion, event distribution, date range.

### `GET /api/funnel`

Reads `analytics_global.funnel`. **Visitor-based** stages (see response `methodology`).

### `GET /api/behavior`

Reads `analytics_global.behavior`: summary, activity buckets, top 15 visitors, engagement metrics.

### `GET /api/products`

| Param | Default | Description |
|-------|---------|-------------|
| `metric` | `views` | `views`, `addtocart`, `transactions` |
| `limit` | `10` | 1–100 |

`product_metrics`: `$sort` on `views`, `add_to_cart`, or `transactions`, then `$limit`.

### `GET /api/products/{item_id}`

`product_metrics` + `product_metadata`. **404** if no metrics document.

### `GET /api/time-series`

| Param | Description |
|-------|-------------|
| `granularity` | `daily` → `time_series_daily`; `hourly` → `time_series_hourly` |
| `start_date`, `end_date` | Optional `YYYY-MM-DD` filter on `date` |

### `GET /api/report`

Composes overview, funnel, behavior, product tops, high-view/low-conversion (`$setWindowFields` on `product_metrics`), and peaks from `analytics_global.report_meta`. **`key_findings`** derived from computed metrics only.

### `GET /api/dataset-info`

- **Full dataset** counts from `data/processed/processing_summary.json` (events, properties, categories, uniques).  
- **MongoDB analytical storage** document counts under `processing_information.mongodb_analytical_storage`.  
- Does not equate MongoDB document counts with full CSV row counts.

## Error handling

| Situation | Status |
|-----------|--------|
| MongoDB down | 503 |
| Compact analytics not imported | 503 |
| Invalid parameters | 422 |
| Product not found | 404 |

## Performance (compact)

- Overview / funnel / behavior: **O(1)** document read.  
- Product rankings: indexed sort + limit (no full 235K load in Python).  
- Report: several small reads + one windowed aggregation on `product_metrics`.  
- No request-time scans of `events` or `item_properties` collections.

## Index support

See `docs/MONGODB_ARCHITECTURE.md` (compact index list).

## Testing (manual)

1. `GET /api/health` — connected  
2. `GET /api/overview` — matches rollup validation / processing summary  
3. `GET /api/dataset-info` — `full_processed_dataset` vs `mongodb_analytical_storage`  
4. `GET /api/report` — key findings present  
5. Stop MongoDB → `/api/overview` returns **503**
