# Trace — One-command launcher (Windows)

Start the **FastAPI backend** and **React/Vite frontend** together from the project root.

## Prerequisites (one-time)

1. **Python 3** with dependencies:
   ```powershell
   cd C:\Users\xxtri\Desktop\Trace
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. **Node.js LTS** and frontend packages:
   ```powershell
   cd frontend
   copy .env.example .env
   npm install
   ```
3. **Root `.env`** (copy from `.env.example`):
   - `MONGODB_URI` — your Atlas connection string (keep secret; never commit)
   - `MONGODB_DATABASE=retailrocket_analytics`
   - `MONGODB_DEPLOYMENT_MODE=compact`
   - `FRONTEND_URL=http://127.0.0.1:5173`

Compact analytics must already be imported to Atlas (`import_analytics_to_mongodb.py`). The launcher does **not** run processing or import.

## Start Trace

From PowerShell (project root):

```powershell
cd C:\Users\xxtri\Desktop\Trace
.\run.ps1
```

Or double-click **`run.bat`** in Explorer (same behavior).

What happens:

1. Checks `.env`, Python, `uvicorn`, `npm`, and `frontend/node_modules`
2. Refuses to start if ports **8000** or **5173** are already in use
3. Pings MongoDB using the same backend code as the API (no credentials printed)
4. Opens two windows: **Trace Backend** and **Trace Frontend**
5. This launcher window waits; **Ctrl+C here** stops both child windows

| Service   | URL |
|-----------|-----|
| Dashboard | http://127.0.0.1:5173 |
| API       | http://127.0.0.1:8000 |
| OpenAPI   | http://127.0.0.1:8000/docs |

## Stop Trace

- Press **Ctrl+C** in the **launcher** window (recommended — stops backend and frontend hosts), or  
- Close the launcher window, or  
- Close each server window and press **Ctrl+C** inside them individually.

## MongoDB / 503 troubleshooting

If the launcher or `/api/health` shows **disconnected** or you saw **TLSV1_ALERT_INTERNAL_ERROR**:

1. **Do not** disable TLS or bypass certificate verification.
2. Confirm **Atlas → Network Access** allows your current public IP.
3. Confirm the cluster is **running** (not paused) in Atlas.
4. Verify **system date/time** on Windows.
5. Update packages: `pip install -U pymongo certifi`
6. Test ping without exposing the URI:
   ```powershell
   cd C:\Users\xxtri\Desktop\Trace\backend
   ..\.venv\Scripts\python.exe -c "from app.database.mongodb import ping_database; print('connected' if ping_database() else 'disconnected')"
   ```
7. Call health: `Invoke-RestMethod http://127.0.0.1:8000/api/health`

The UI may load while analytics endpoints return **503** until MongoDB connects.

## Other issues

| Symptom | Action |
|---------|--------|
| Execution policy blocks `run.ps1` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` or use `run.bat` |
| Port already in use | Stop old uvicorn/Vite or free ports 8000 / 5173 |
| `uvicorn` not found | `pip install -r requirements.txt` in project venv |
| Frontend blank / API errors | Set `frontend/.env` → `VITE_API_BASE_URL=http://127.0.0.1:8000` |
| CORS errors | Match `FRONTEND_URL` in root `.env` to browser origin (`127.0.0.1` vs `localhost`) |

## What the launcher does not do

- Does not run `process_dataset.py`, `build_mongodb_rollups.py`, or `import_analytics_to_mongodb.py`
- Does not modify MongoDB data or `.env` contents
- Does not print `MONGODB_URI` or passwords in the console
