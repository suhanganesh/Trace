# Trace Frontend

React dashboard for **Trace** — E-commerce Big Data Storage and Analytics Using MongoDB.

The frontend visualizes aggregated analytics from the Trace FastAPI backend. It never loads raw CSV files or full MongoDB collections.

## Stack

- React 18 + Vite
- Tailwind CSS
- Recharts
- Lucide React
- React Router

## Environment

Copy `.env.example` to `.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Manual startup

Backend must be running first (MongoDB + FastAPI):

```powershell
cd frontend
npm install
npm run dev
```

Default dev URL: [http://127.0.0.1:5173](http://127.0.0.1:5173)

## Pages

| Route | Description |
|-------|-------------|
| `/overview` | KPIs, distribution, funnel, daily activity, key observations |
| `/behavior` | Visitor activity buckets and engagement |
| `/products` | Product rankings and high-attention / low-conversion cohort |
| `/products/:itemId` | Single-product detail |
| `/time-analysis` | Daily/hourly time series with optional date filters |
| `/report` | Report-style analytical summary |
| `/dataset` | Dataset metadata and pipeline overview |

## API dependency

All metrics are fetched from:

- `/api/health`
- `/api/overview`
- `/api/funnel`
- `/api/behavior`
- `/api/products`
- `/api/products/{item_id}`
- `/api/time-series`
- `/api/report`
- `/api/dataset-info`

See `docs/BACKEND_API.md` in the project root for response shapes.
