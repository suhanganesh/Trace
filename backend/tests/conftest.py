from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSING_SUMMARY_PATH = PROJECT_ROOT / "data" / "processed" / "processing_summary.json"


@pytest.fixture(scope="session")
def processing_summary() -> dict:
    if not PROCESSING_SUMMARY_PATH.is_file():
        pytest.skip(f"Missing {PROCESSING_SUMMARY_PATH}")
    return json.loads(PROCESSING_SUMMARY_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def client() -> TestClient:
    from app.main import app

    return TestClient(app)


@pytest.fixture(scope="session")
def require_mongodb(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code in (200, 503)
    payload = response.json()
    if payload.get("database") != "connected":
        pytest.skip("MongoDB is not connected; start Atlas/local MongoDB and verify MONGODB_URI.")
