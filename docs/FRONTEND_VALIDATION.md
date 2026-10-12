# Trace — Frontend Manual Validation Checklist

Use this checklist after the backend is running (`uvicorn`) and the frontend dev server is running (`npm run dev`). Open browser DevTools **Console** and **Network** while testing.

Base URL (default): `http://127.0.0.1:5173`

---

## Prerequisites

- [ ] `GET /api/health` returns `database: connected`
- [ ] Compact MongoDB import completed
- [ ] `FRONTEND_URL` / `VITE_API_BASE_URL` match your local origins

---

## Overview (`/overview`)

- [ ] KPI cards show non-zero Events, Visitors, Products, Views, Add to cart, Transactions
- [ ] Visitor conversion rate displays as a percentage
- [ ] Event distribution chart renders three segments (view, add to cart, transaction)
- [ ] Funnel chart renders three stages with counts
- [ ] Time series chart renders with daily (or loaded) data
- [ ] No failed `/api/overview`, `/api/funnel`, `/api/time-series`, or `/api/report` requests in Network tab
- [ ] No uncaught errors in Console

---

## Behavior (`/behavior`)

- [ ] Summary metrics load (avg events/views per visitor, repeat visitors, etc.)
- [ ] Activity bucket bar chart renders with labeled ranges
- [ ] Top visitors table shows up to 15 rows with event breakdown columns
- [ ] Engagement metrics section displays
- [ ] `/api/behavior` returns 200

---

## Products (`/products`)

- [ ] Top products table and chart load for default metric (views)
- [ ] Changing **Metric** (views / add to cart / transactions) refreshes rankings
- [ ] Changing **Limit** updates row count
- [ ] High-view / low-conversion section loads (from `/api/report`)
- [ ] Clicking a product opens product detail route
- [ ] `/api/products` returns 200 for each metric tested

---

## Product detail (`/products/{item_id}`)

- [ ] Views, add to cart, transactions, and conversion display
- [ ] Latest properties section shows `categoryid` / `available` when present
- [ ] Invalid ID shows error state; unknown product shows 404 messaging
- [ ] `/api/products/{item_id}` returns 200 for a known product

---

## Time Analysis (`/time-analysis`)

- [ ] Daily granularity loads a time series chart
- [ ] Hourly granularity loads and chart updates
- [ ] Date range or filter controls (if used) affect series without errors
- [ ] `/api/time-series` returns 200 for `daily` and `hourly`

---

## Analytics Report (`/report`)

- [ ] Full report page loads without 500 errors
- [ ] Dataset summary and engagement sections display
- [ ] Conversion / funnel section displays
- [ ] Product performance (top viewed, top purchased) displays
- [ ] High-view / low-conversion block shows methodology text and product list (may be empty if cohort filters yield none)
- [ ] Key findings cards render
- [ ] `/api/report` returns 200

---

## Dataset (`/dataset`)

- [ ] Cards show full processed counts (≈2.76M events, ≈20.3M property rows, 1,669 categories)
- [ ] Event type breakdown matches processing summary order of magnitude
- [ ] Database status badge shows **connected** when MongoDB is up
- [ ] Processing timestamp / duplicate removal info visible under pipeline section
- [ ] `/api/dataset-info` returns 200; `processing_information.mongodb_analytical_storage` shows compact collection counts (smaller than full CSV row counts)
- [ ] No misleading implication that MongoDB holds every raw event row

---

## Global

- [ ] Sidebar navigation works for all pages
- [ ] Refresh / reload control re-fetches API data without stale errors
- [ ] CORS errors absent when API and frontend URLs are configured correctly

---

## Sign-off

| Validator | Date | Result (Pass / Fail) | Notes |
|-----------|------|----------------------|-------|
|           |      |                      |       |
