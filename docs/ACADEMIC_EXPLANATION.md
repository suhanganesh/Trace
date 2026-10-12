# Trace — Academic Explanation

This document supports viva, presentation, and project report discussions for **Trace — E-Commerce Big Data Storage and Analytics Using MongoDB**.

---

## 1. Why MongoDB?

RetailRocket data is semi-structured and high-volume:

- **Events** are repetitive documents (visitor, item, event type, timestamp).  
- **Item properties** are naturally **EAV** (entity–attribute–value) with time-varying rows.  
- **Categories** form a hierarchy without needing a rigid relational schema.

MongoDB stores each record as a **document**, which maps directly to CSV rows after import. A single database can hold millions of events and tens of millions of property rows while supporting analytical queries through the **aggregation framework**.

---

## 2. Why MongoDB aggregation?

Dashboard metrics (counts, uniques, funnels, top products, time buckets) require **grouping and summarizing** large collections. Doing this in Python or React would require loading huge result sets into application memory.

Trace uses **`$match`**, **`$group`**, **`$facet`**, **`$sort`**, **`$limit`**, and related stages so MongoDB performs the heavy work close to the data. FastAPI returns **small JSON summaries** (counts, top-N lists, daily totals)—never millions of raw events.

---

## 3. Why this dataset?

The RetailRocket files provide **realistic e-commerce scale** for an academic project:

- ~2.76 million interaction events  
- ~20.3 million item property records  
- ~942 MB on disk  

That volume is large enough to require serious processing and indexing, yet small enough to run on a laptop with local MongoDB.

---

## 4. Why process data before import?

Raw CSV is validated and enriched **before** MongoDB:

- **Schema checks** (timestamps, IDs, event types)  
- **Exact duplicate event removal** (460 rows) in processed output only—raw data preserved  
- **UTC-derived fields** (`date`, `hour`, etc.) to simplify time-series aggregations  
- **Quality reports** (`processing_summary.json`, `data_quality_report.json`) for traceability  

Importing clean, consistent documents reduces errors and speeds up repeated analytical queries.

---

## 5. Why indexes?

Without indexes, MongoDB would scan millions of documents for every dashboard request. Trace creates indexes aligned with query patterns—for example:

- `event`, `timestamp`, `visitorid`, `itemid`  
- Compounds such as `(event, timestamp)` and `(itemid, event)`  
- Property lookups on `(itemid, property, timestamp)`  

Indexes are built **after** bulk import to avoid index maintenance cost during load.

---

## 6. Why FastAPI?

FastAPI provides a lightweight REST layer with automatic OpenAPI docs, Pydantic response models, and clear error handling. It fits an academic architecture where **MongoDB is the analytics engine** and the API is a thin orchestration layer.

---

## 7. Why React?

Trace needs an interactive **analytics UI** (filters, charts, tables, report layout). React + Vite offers a modern component model; Recharts renders time series and distributions from API data. The frontend **does not** implement Big Data processing—it **visualizes** server-side results.

---

## 8. How does the project handle large data?

| Stage | Approach |
|-------|----------|
| Processing | Stream/chunk CSV reads; do not load 20M+ rows at once for the main pipeline |
| Full dataset | Remains in `data/processed/` as the authoritative fact store |
| Rollup build | Second streaming pass over all events; optional stream over 20M property rows for latest metadata |
| MongoDB (Atlas Free) | **Materialized summaries** only— avoids exceeding the 512 MB M0 quota |
| API | Read `analytics_global` + indexed sorts on `product_metrics`; no million-row scans |
| Frontend | Fetch aggregated endpoints; no CSV parsing in the browser |

### Atlas Free tier and separation of concerns

Cloud MongoDB M0 cannot hold ~2.76M events plus ~20.3M property documents with indexes. Trace therefore implements a **two-tier data architecture**:

1. **Local processed files** — complete, verifiable dataset (used by rollup builder and `processing_summary.json`).  
2. **MongoDB compact collections** — derived **analytical projections** for dashboard latency and hosting constraints.

This is standard **OLAP-style pre-aggregation**: facts are not discarded; they are summarized offline from 100% of rows, then served from summary tables implemented as MongoDB collections.

## 8b. Why still call MongoDB the analytics engine?

Even in compact mode, MongoDB provides indexed lookups, sorted top-N queries, date-filtered time series, and windowed aggregations (e.g. high-view / low-conversion on `product_metrics`). The difference is the **granularity stored**: summaries instead of raw events.

---

## 9. Why is raw data not sent to the frontend?

Transferring millions of events to the browser would be slow, memory-intensive, and unnecessary. All KPIs and charts are computed in MongoDB; the UI receives **pre-aggregated** numbers and small arrays (e.g., daily totals, top 25 products).

---

## 10. What makes this a Big Data project?

- **Volume:** Multi-million-row event and property datasets  
- **Processing:** Dedicated Python pipeline with validation and deduplication  
- **Storage:** Full facts local; MongoDB holds compact analytical collections for serving  
- **Query:** Offline rollups + MongoDB reads/aggregations on summaries  
- **Presentation:** Full-stack dashboard proving the pipeline end-to-end  

It is **batch/historical** Big Data analytics, not real-time stream processing.

---

## 11. Analytical methodology (important for viva)

### Events vs visitors

- **Event counts** count every row (views, carts, transactions).  
- **Visitor metrics** count **unique `visitorid`** values.  
- The **funnel** uses **unique visitors** per stage—not event totals.

### Conversion

- **Visitor conversion rate** = visitors with ≥1 transaction ÷ all unique visitors.  
- **Product conversion** (table) = transaction events ÷ views for that `itemid`.

### Transactions vs orders

Multiple `transaction` events can share one `transactionid` (multi-item orders). Trace counts **transaction events** (line items) unless explicitly aggregating distinct `transactionid`.

### Item properties

Properties are **timestamped EAV rows** in the full CSV. In compact MongoDB storage, product detail shows **latest** `categoryid` and `available` precomputed during rollup build—not 20M historical property documents in Atlas.

---

## 12. Limitations

- No distributed cluster or sharding  
- No live event ingestion  
- No product display names in source data  
- Category tree and property `categoryid` values are not perfectly aligned for all IDs  
- Report endpoint composes many aggregations (slower than `/api/overview`)  

---

## 13. Possible future improvements

- Full raw collections on self-hosted MongoDB for arbitrary ad-hoc pipelines  
- Scheduled rollup refresh / change streams  
- Authenticated API  
- Optional stream pipeline (Kafka) for true velocity demos  

These are extensions beyond the current Trace scope.

---

## Example aggregation concepts used

**Event totals by type:**

```javascript
db.events.aggregate([
  { $group: { _id: "$event", count: { $sum: 1 } } }
])
```

**Unique visitors:**

```javascript
db.events.aggregate([
  { $group: { _id: "$visitorid" } },
  { $count: "unique_visitors" }
])
```

**Daily views:**

```javascript
db.events.aggregate([
  { $match: { event: "view" } },
  { $group: { _id: "$date", views: { $sum: 1 } } },
  { $sort: { _id: 1 } }
])
```

In **compact mode**, equivalent metrics come from `analytics_global` and `product_metrics` rather than `db.events.aggregate(...)`. See `docs/MONGODB_ANALYTICS.md` for endpoint mapping. Legacy full-import pipeline examples still apply when using `import_to_mongodb.py` locally.
