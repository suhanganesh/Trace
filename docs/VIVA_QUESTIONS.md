# Trace — Viva Questions & Answers

Concise answers for project defense. Application name: **Trace**. Dataset: **RetailRocket**.

---

### 1. What is Trace?

Trace is a Big Data analytics application that processes RetailRocket e-commerce CSV files, stores them in MongoDB, runs aggregation-based analytics via FastAPI, and visualizes results in a React dashboard.

### 2. What is Big Data in your project?

Primarily **volume** (~2.76M events, ~20M property rows, ~942 MB raw data) and **variety** (events, EAV properties, category hierarchy), processed and queried at scale on MongoDB.

### 3. Is your system real-time?

No. The dataset contains **historical** timestamps (2015). Processing and import are **batch**; there is no live stream ingestion.

### 4. Why MongoDB instead of SQL?

Event and property rows fit a **document model**; flexible schema handles sparse fields (e.g. `transactionid` only on purchases). Aggregations express analytics without heavy JOINs across normalized tables the source files do not provide.

### 5. What is a document database?

Data is stored as JSON-like **documents** in **collections**, rather than fixed relational tables with foreign keys everywhere.

### 6. What collections does Trace use?

**Compact mode (default, Atlas Free):** `analytics_global`, `product_metrics`, `product_metadata`, `time_series_daily`, `time_series_hourly`, and `category_tree` in `retailrocket_analytics`. Full events and item properties stay in local `data/processed/` CSV files.

**Legacy full import (local MongoDB only):** `events`, `item_properties`, `category_tree`.

### 7. Why not store everything in one collection?

Events, properties, and categories have different shapes and access patterns. Combining them would duplicate data and complicate queries.

### 8. What is MongoDB aggregation?

A pipeline of stages (`$match`, `$group`, …) that transforms documents server-side. Trace uses it for KPIs, funnels, rankings, and time series.

### 9. What does `$match` do?

Filters documents (like `WHERE`), e.g. `{ event: "transaction" }` or date range on `date`.

### 10. What does `$group` do?

Groups documents by a key and computes aggregates (`$sum`, `$max`, etc.), e.g. count events per `itemid`.

### 11. What does `$facet` do?

Runs **multiple sub-pipelines** on the same input in one request. Trace uses it in `/api/overview` to compute totals, distributions, and uniques together.

### 12. Does Trace use `$lookup`?

Rarely—mainly for optional product property enrichment. Most analytics are on the `events` collection alone.

### 13. Why create indexes?

To avoid full collection scans on millions of documents. Indexes support filters on `event`, `timestamp`, `visitorid`, `itemid`, and product property lookups.

### 14. When are indexes created?

**After** bulk import, to reduce index maintenance during load (`import_to_mongodb.py`).

### 15. Why FastAPI?

Lightweight Python API, automatic OpenAPI docs, Pydantic schemas, and easy integration with PyMongo.

### 16. Why React?

Component-based UI for charts, tables, and navigation; consumes REST JSON from FastAPI.

### 17. Does the frontend process millions of records?

**No.** It only calls aggregated API endpoints (counts, top-N, daily buckets).

### 18. How are CSV files processed?

`process_dataset.py` streams files, validates rows, deduplicates exact event duplicates, adds UTC date/time fields, and writes `data/processed/*.csv` plus JSON summaries.

### 19. How many duplicate events were removed?

Phase 1 found **460** exact duplicate event rows. They are removed in **processed** output only; raw CSV is unchanged.

### 20. What are item properties?

**EAV** rows: `itemid`, `property`, `value`, `timestamp`—not a simple one-row-per-product table.

### 21. What is visitor conversion?

Unique visitors with at least one **transaction** event divided by **all unique visitors** (ratio, shown as percentage in UI).

### 22. How is the funnel defined?

**Unique visitors** with ≥1 view, ≥1 addtocart, and ≥1 transaction. Percentages are relative to view visitors. It is **not** a strict sequential path for every user.

### 23. What is product conversion in Trace?

For a product: **transaction event count ÷ view count** (line-item transactions, not unique orders).

### 24. What is the difference between transaction events and orders?

One **order** (`transactionid`) can have **multiple** transaction **events** (line items). Trace can count events or distinct `transactionid` separately.

### 25. Why use Python before MongoDB?

To validate schema, document quality, remove exact duplicates, and add derived time fields without altering raw data.

### 26. How is large import handled?

Chunked CSV read, batched `insert_many`, configurable `MONGODB_BATCH_SIZE`, progress logging.

### 27. MongoDB vs SQL for this project?

SQL excels at strict relational models; Trace’s exports are flat CSVs suited to **document storage + aggregation**. SQL could work but would require more ETL into normalized tables.

### 28. What happens if MongoDB is down?

API returns **503**; frontend shows a clear unavailable message without stack traces.

### 29. What are project limitations?

Local single-node MongoDB, historical data, no product names, heavier `/api/report`, imperfect category/property ID alignment, no authentication.

### 30. How could Trace scale further?

Sharding, replica sets, pre-aggregated collections, stream ingestion (Kafka), cloud deployment—documented as future work, not implemented.

---

## Quick demo flow (for presentation)

1. Show **Dataset** page — pipeline diagram and scale  
2. Show **Overview** — KPIs from MongoDB  
3. Show **Funnel** — visitor-based stages and methodology text  
4. Show **Products** — rankings and high-attention / low-conversion table  
5. Mention `processing_summary.json` and `mongodb_import_report.json` as evidence of processing and import  
