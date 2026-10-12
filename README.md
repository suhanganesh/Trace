# Trace — E-Commerce Big Data Storage and Analytics Using MongoDB

**Trace** is an academic Big Data Analytics application that processes the **RetailRocket** e-commerce dataset, stores it in **MongoDB**, computes analytics with **aggregation pipelines**, exposes results through **FastAPI**, and visualizes them in a **React + Vite** dashboard.

Tagline: *E-commerce intelligence from large-scale event data.*

RetailRocket is the **dataset**. **Trace** is the application.

---

## 1. Project Overview

Trace demonstrates an end-to-end analytics pipeline for large-scale e-commerce **event data**:

1. Inspect and validate raw CSV files  
2. Process and clean data in Python (streaming/chunked)  
3. Build compact analytical rollups and import them into MongoDB (Atlas Free tier)  
4. Serve KPIs, funnels, products, and time trends from rollup collections  
5. Serve aggregated JSON via FastAPI  
6. Present insights in a modern React dashboard  

The system analyzes **historical** data. It does not provide real-time streaming analytics.

---

## 2. Problem Statement

Large e-commerce platforms generate millions of interaction events (views, cart actions, purchases). Storing, querying, and analyzing such volumes requires scalable processing and a database suited to flexible, document-oriented workloads.

Trace shows how a **MongoDB-centric** pipeline can ingest multi-million-row CSV exports, index them for analytical queries, and support an interactive dashboard without shipping raw records to the browser.

---

## 3. Objectives

- Process large CSV datasets efficiently without loading entire files into memory where avoidable  
- Detect and remove **exact duplicate** event rows (460 identified in Phase 1) while preserving raw data  
- Keep the **full processed dataset** local; store **compact analytical projections** in MongoDB for cloud free-tier limits  
- Use MongoDB for serving rollups and targeted aggregations (e.g. product rankings, report cohorts)  
- Analyze visitor behavior, product engagement, conversion, and temporal patterns  
- Expose analytics through a REST API (FastAPI)  
- Visualize results in **Trace** (React + Vite + Recharts)  

---

## 4. Dataset

**Source:** RetailRocket (local files under `data/raw/` — not modified by Trace).

| File | Role | Approx. scale |
|------|------|----------------|
| `events.csv` | User–item interactions | ~2.76M rows |
| `item_properties_part1.csv` | Item attributes (EAV) | ~11M rows |
| `item_properties_part2.csv` | Item attributes (EAV) | ~9.3M rows |
| `category_tree.csv` | Category hierarchy | 1,669 rows |

**Combined item properties:** ~20.3M rows. **Raw dataset size:** ~942 MB.

**Event types:** `view`, `addtocart`, `transaction` (stored as-is; not renamed in processing).

**Timestamps:** Unix epoch **milliseconds**, interpreted as **UTC**.

See Phase 1 inspection findings in project history and `docs/DATA_PROCESSING.md`.

---

## 5. Big Data Characteristics

| Dimension | How Trace demonstrates it |
|-----------|---------------------------|
| **Volume** | ~2.76M events, ~20.3M property rows, ~942 MB raw CSV |
| **Variety** | Event stream, timestamped EAV properties, hierarchical categories |
| **Velocity** | Historical batch dataset (May–Sep 2015), not live ingestion |
| **Veracity** | Schema inspection, validation, duplicate handling, quality JSON reports |
| **Value** | Engagement, conversion, product, and time-based insights via aggregation |

---

## 6. System Architecture

```text
RetailRocket CSV Dataset (data/raw/)
        │
        ▼
Python inspection & processing (scripts/)
        │
        ▼
Processed CSV (data/processed/) — authoritative full dataset
        │
        ▼
Rollup builder → data/mongodb_free_tier/
        │
        ▼
MongoDB compact collections (retailrocket_analytics)
        │
        ▼
FastAPI reads rollups + light aggregations (PyMongo)
        │
        ▼
FastAPI (Trace API)
        │
        ▼
React + Vite (Trace dashboard)
```

| Layer | Responsibility |
|-------|----------------|
| **Raw CSV** | Immutable source of truth |
| **Python** | Validation, deduplication, derived UTC date/time fields |
| **Processed CSV** | Authoritative cleaned facts (events, properties, categories) |
| **Rollup artifacts** | Offline aggregates from 100% of events |
| **MongoDB** | Analytical serving layer (compact collections on Atlas M0) |
| **FastAPI** | HTTP API, error handling, CORS |
| **React** | Visualization of **aggregated** API responses only |

---

## 7. Technology Stack

| Area | Technologies |
|------|----------------|
| Processing | Python 3, stdlib CSV (chunked), optional inspection scripts |
| Database | MongoDB, PyMongo |
| Backend | FastAPI, Uvicorn, Pydantic |
| Frontend | React 18, Vite, Tailwind CSS, Recharts, Lucide React |
| Config | `.env` (root + `frontend/.env`) |

No Docker, Redis, Kafka, or Kubernetes in this project.

---

## 8. Data Processing Pipeline

1. **`scripts/inspect_dataset.py`** — Read-only report on `data/raw/`  
2. **`scripts/process_dataset.py`** — Writes `data/processed/events.csv`, `item_properties.csv`, `category_tree.csv`, plus `processing_summary.json` and `data_quality_report.json`  
3. **Duplicate handling** — Exact duplicate **event** rows removed in processed output only (460 rows per Phase 1); raw files untouched  
4. **Derived fields** — `datetime`, `date`, `hour`, etc. (UTC) on events  

Details: `docs/DATA_PROCESSING.md`

---

## 9. MongoDB Design (compact — default)

**Database name:** `retailrocket_analytics`  
**Mode:** `MONGODB_DEPLOYMENT_MODE=compact` (see `.env.example`)

Full **events** and **item_properties** are **not** stored in Atlas Free tier (512 MB limit). They remain in `data/processed/`. MongoDB holds:

| Collection | Content |
|------------|---------|
| `analytics_global` | Single document: overview, funnel, behavior, report peaks |
| `product_metrics` | ~235K products with views / add-to-cart / transactions |
| `product_metadata` | Latest `categoryid` / `available` for event products |
| `time_series_daily` / `time_series_hourly` | Pre-aggregated time buckets |
| `category_tree` | 1,669 hierarchy rows |

**Legacy:** `scripts/import_to_mongodb.py` can still full-import to a local MongoDB instance with enough disk; the API targets compact collections.

Details: `docs/MONGODB_ARCHITECTURE.md`, `docs/MONGODB_ANALYTICS.md`

---

## 10. Backend API

Base URL (local): `http://127.0.0.1:8000`

Interactive docs: `/docs`

Details: `docs/BACKEND_API.md`

---

## 11. Frontend

Location: `frontend/`

Pages: Overview, Behavior, Products, Product detail, Time Analysis, Analytics Report, Dataset.

Details: `frontend/README.md`

---

## 12. Analytics (summary)

| Area | Metrics / views |
|------|------------------|
| **Overview** | Total events, unique visitors/products, views, add-to-cart, transactions, **visitor conversion rate**, event distribution |
| **Funnel** | **Unique visitors** with ≥1 view / addtocart / transaction (not raw event counts) |
| **Behavior** | Events per visitor, buckets, top visitors, repeat engagement |
| **Products** | Top-N by views / addtocart / transactions; conversion = transactions ÷ views; high-view / low-conversion cohort (from report logic) |
| **Time** | Daily/hourly series; optional date filters; peak day/hour from report |
| **Report** | Executive summary, findings derived from computed metrics |
| **Dataset** | Full counts from `processing_summary.json`; MongoDB storage counts labeled separately |

**Visitor conversion:** unique visitors with ≥1 `transaction` event ÷ all unique visitors.

**Product conversion (UI):** transaction event count ÷ view count for that product.

---

## 13. Project Structure

```text
Trace/
├── data/
│   ├── raw/              # RetailRocket CSV (read-only)
│   ├── processed/        # Generated CSV + JSON summaries (full dataset)
│   └── mongodb_free_tier/  # Compact rollup artifacts (generated)
├── scripts/              # inspect, process, build_mongodb_rollups, import_analytics_to_mongodb
├── backend/app/          # FastAPI + analytics modules
├── frontend/             # React dashboard
├── docs/                 # Architecture, API, academic notes
├── requirements.txt      # Python dependencies
└── .env.example          # Environment template
```

---

## 14. Installation

### Python (project root)

```powershell
pip install -r requirements.txt
```

Copy environment file:

```powershell
copy .env.example .env
```

Edit `.env`: set `MONGODB_URI`, `MONGODB_DATABASE`, `MONGODB_DEPLOYMENT_MODE=compact`, `FRONTEND_URL`.

### Node (frontend)

```powershell
cd frontend
copy .env.example .env
npm install
```

---

## 15. Manual Execution

Run steps in order. **`--drop`** on compact import only replaces the six analytical collections (never raw `events` / `item_properties` in MongoDB).

### 1. Inspect raw data (optional)

```powershell
python scripts/inspect_dataset.py
```

### 2. Process CSVs

```powershell
python scripts/process_dataset.py
```

### 3. Start MongoDB

Start your local MongoDB service manually.

### 4. Build compact rollups (offline, all events)

```powershell
python scripts/build_mongodb_rollups.py
```

Writes `data/mongodb_free_tier/` and `rollup_validation.json` (checks against `processing_summary.json`).

### 5. Import compact analytics into MongoDB

```powershell
python scripts/import_analytics_to_mongodb.py --drop
```

Without `--drop`: import aborts if compact collections already contain data.

### 6. Start API

```powershell
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 7. Start frontend

```powershell
cd frontend
npm run dev
```

Open: `http://127.0.0.1:5173`

Ensure `FRONTEND_URL` in root `.env` matches your browser origin (see `.env.example`; CORS allows both `127.0.0.1` and `localhost` for port 5173 when configured from either form).

---

## 16. API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/health` | API and MongoDB connectivity |
| `GET /api/overview` | Global KPIs and event distribution |
| `GET /api/funnel` | Visitor-based funnel |
| `GET /api/behavior` | Visitor activity and top visitors |
| `GET /api/products` | Product rankings (`metric`, `limit`) |
| `GET /api/products/{item_id}` | Single-product metrics + latest properties |
| `GET /api/time-series` | Daily/hourly series (`granularity`, `start_date`, `end_date`) |
| `GET /api/report` | Full analytical report + key findings |
| `GET /api/dataset-info` | Dataset/processing metadata |

---

## 17. Academic Significance

Trace illustrates a complete **Big Data analytics** workflow: large-file processing, document storage, indexed aggregation, API layer, and visualization— suitable for demonstrating MongoDB as an analytical engine rather than simple CRUD.

Supporting documents:

- `docs/ACADEMIC_EXPLANATION.md`
- `docs/VIVA_QUESTIONS.md`

---

## 18. Limitations

- Historical RetailRocket snapshot; not real-time streaming  
- MongoDB Atlas M0 storage cap — full event/property history stays local, not in cloud DB  
- Local or Atlas single-node (no sharded cluster)  
- Product **names** not in dataset—UI uses product IDs  
- Some category IDs in properties do not appear in `category_tree` (documented in processing quality report)  
- `/api/report` runs multiple aggregations—heavier than single-metric endpoints  
- Item properties are EAV rows, not a flat product catalog  
- Exact duplicate removal applies to **events** only (460 rows); item properties had no exact dupes in Phase 1  

---

## 19. Future Enhancements

Possible extensions (not implemented):

- Sharded MongoDB or cloud deployment  
- Stream ingestion (Kafka, change streams)  
- Authentication and multi-user access  
- Optional full raw import on self-hosted MongoDB for ad-hoc `$match` on every event  
- Richer product metadata or ML-based recommendations  

---

## License & data

Use RetailRocket data according to your course and dataset license terms. Trace application code is for academic demonstration.
