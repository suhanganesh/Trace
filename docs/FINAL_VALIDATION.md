# Trace — Phase 7 Final Validation

This document summarizes the validation strategy for the **compact MongoDB** Trace deployment after end-to-end manual verification.

---

## Architecture status

| Layer | Status | Notes |
|-------|--------|-------|
| Raw dataset (`data/raw/`) | Authoritative, local | Not stored in Atlas M0 |
| Processed dataset (`data/processed/`) | Authoritative, local | Full events + item properties + categories |
| Rollup artifacts (`data/mongodb_free_tier/`) | Derived | Built from 100% of processed events |
| MongoDB (`retailrocket_analytics`) | Compact analytical projections | Sized for Atlas **512 MB** M0 |
| FastAPI backend | Serves rollups + light aggregations | No raw `events` / `item_properties` collections required |
| React frontend | Consumes aggregated API JSON | No CSV processing in browser |

---

## Full dataset (local processed files)

Authoritative counts from `data/processed/processing_summary.json`:

| Metric | Count |
|--------|------:|
| Processed events | 2,755,641 |
| Item-property rows | 20,275,902 |
| Categories | 1,669 |
| Unique visitors | 1,407,580 |
| Unique products (in events) | 235,061 |
| View events | 2,664,218 |
| Add-to-cart events | 68,966 |
| Transaction events | 22,457 |

Duplicate events removed during processing: **460** (raw CSV unchanged).

---

## MongoDB compact storage (Atlas analytical layer)

Typical deployed document counts (your successful import):

| Collection | Documents | Role |
|------------|----------:|------|
| `analytics_global` | 1 | Overview, funnel, behavior, report peaks |
| `product_metrics` | 235,061 | Per-product views / add-to-cart / transactions |
| `product_metadata` | 185,246 | Latest `categoryid` / `available` for products with property history |
| `time_series_daily` | 139 | Daily aggregates |
| `time_series_hourly` | 3,312 | Hourly aggregates |
| `category_tree` | 1,669 | Category hierarchy |

MongoDB stores **analytical projections**, not the full 2.76M-event or 20M-row property history. The complete dataset remains in local processed CSVs because Atlas M0 cannot hold full raw collections with indexes.

---

## Automated validation (manual commands)

Run from project root (`C:\Users\xxtri\Desktop\Trace`):

### 1. Rollup artifact validation (no MongoDB)

```powershell
python scripts/validate_mongodb_rollups.py
```

**Validates:** artifact files exist, line counts vs manifest, `rollup_validation.json` has `"validation_passed": true`, `analytics_global.json` matches `processing_summary.json`.

**Output:** `data/mongodb_free_tier/rollup_validation_run.json`

### 2. MongoDB deployment validation (read-only)

```powershell
python scripts/validate_mongodb_deployment.py
```

**Validates:** `MONGODB_DEPLOYMENT_MODE=compact`, ping, compact collections + counts, required indexes, `analytics_global.overview` vs processing summary.

**Optional API check:** with uvicorn running on port 8000, compares `/api/overview` to summary and MongoDB.

**Output:** `data/mongodb_free_tier/deployment_validation_run.json`

Skip API if backend is down:

```powershell
python scripts/validate_mongodb_deployment.py --skip-api
```

### 3. Backend API smoke tests (requires MongoDB + compact import)

Install test dependency once: `pip install pytest` (see `requirements.txt`).

With MongoDB reachable via `.env`:

```powershell
cd backend
pytest tests/test_api_smoke.py -v
```

**Validates:** all `/api/*` endpoints return expected shapes; overview totals match `processing_summary.json`; report includes all sections.

---

## Validation status checklist

Fill in after you run the commands:

| Check | Tool | Pass? | Date |
|-------|------|-------|------|
| Rollup artifacts vs summary | `validate_mongodb_rollups.py` | | |
| `rollup_validation.json` | same | | |
| MongoDB compact collections | `validate_mongodb_deployment.py` | | |
| MongoDB overview vs summary | same | | |
| API overview vs summary | same (uvicorn running) | | |
| API smoke tests | `pytest tests/test_api_smoke.py` | | |
| Frontend manual checklist | `docs/FRONTEND_VALIDATION.md` | | |

---

## Backend endpoint validation (expected)

| Endpoint | Compact dependency |
|----------|-------------------|
| `/api/health` | Ping only |
| `/api/overview` | `analytics_global` |
| `/api/funnel` | `analytics_global` |
| `/api/behavior` | `analytics_global` |
| `/api/products` | `product_metrics` |
| `/api/products/{id}` | `product_metrics` + `product_metadata` |
| `/api/time-series` | `time_series_daily` / `time_series_hourly` |
| `/api/report` | Composed; high-view/low-conversion uses Python thresholds on `product_metrics` (Atlas-compatible) |
| `/api/dataset-info` | `processing_summary.json` + compact collection counts |

---

## Frontend manual validation

See **`docs/FRONTEND_VALIDATION.md`** — no browser automation in repo; checklist covers Overview, Behavior, Products, Time Analysis, Report, Dataset.

---

## Known warnings

- **Legacy MongoDB collections:** If `events` / `item_properties` exist from an old full import, they are unused but consume Atlas quota.
- **Dataset page UI copy:** Schema blurb still mentions legacy collection names; API distinguishes full vs compact storage correctly.
- **Product metadata count < product_metrics:** Only products with `categoryid` / `available` rows appear in `product_metadata`.
- **Report endpoint weight:** `/api/report` composes multiple reads; high-view/low-conversion loads cohort docs from MongoDB into Python (by design for M0 compatibility).
- **Rollup build RAM:** Visitor map during offline build can use hundreds of MB during the event pass.

---

## Known limitations

- Historical batch analytics only (not real-time streaming).
- Atlas M0 storage cap; full facts remain local.
- No product display names in source data (IDs only).
- `/api/dataset-info` requires MongoDB connection even though counts are file-backed.
- Legacy `scripts/import_to_mongodb.py` is not wired to the current API (local full-storage experiment only).

---

## Legacy dependency audit (backend runtime)

No runtime access to MongoDB collections named `events` or `item_properties`. Remaining references are field names, user-facing copy, or unused `_events` parameters:

- `backend/app/routes/dataset.py` — processed CSV row counts (`item_properties` key in JSON summary)
- `backend/app/analytics/products.py` — 404 message text mentions “events”
- `backend/app/analytics/report.py` — generic “events” wording in findings
- `backend/app/analytics/{overview,funnel,behavior,time_series}.py` — unused optional `_events` parameters

Intentionally preserved: `scripts/import_to_mongodb.py` (not used by compact API).

---

## Secrets and Git ignore findings

| Item | Status |
|------|--------|
| `.env` ignored | Yes (`.gitignore`) |
| `frontend/.env` ignored | Yes |
| `data/raw/` ignored | Yes |
| `data/processed/` ignored | Yes |
| `data/mongodb_free_tier/` ignored | **No** — generated rollups may be committed unless you add a ignore rule |
| MongoDB URI in source | **No** — only `.env.example` placeholder |
| Credentials in docs | **No** |

Do not commit real `.env` files or Atlas credentials.

---

## Recommended execution order

```powershell
cd C:\Users\xxtri\Desktop\Trace

python scripts/validate_mongodb_rollups.py

python scripts/validate_mongodb_deployment.py

cd backend
pytest tests/test_api_smoke.py -v
```

Then complete **`docs/FRONTEND_VALIDATION.md`** in the browser while uvicorn and Vite are running.

---

## Phase 7 completion criteria

- [ ] All three automated validation commands exit code 0
- [ ] Frontend manual checklist signed off
- [ ] Atlas storage size reviewed in Atlas UI (optional but recommended)
- [ ] Academic demo path documented in root `README.md`
