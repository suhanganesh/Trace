"""Smoke tests for Trace compact-mode API (requires MongoDB + compact import)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def _expected_overview(processing_summary: dict) -> dict:
    event_counts = processing_summary.get("event_counts", {})
    return {
        "total_events": processing_summary["processed_row_counts"]["events"],
        "unique_visitors": processing_summary["unique_visitors"],
        "unique_products": processing_summary["unique_products_in_events"],
        "total_views": event_counts["view"],
        "total_add_to_cart": event_counts["addtocart"],
        "total_transactions": processing_summary["transaction_event_count"],
    }


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code in (200, 503)
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["database"] in ("connected", "disconnected")
    assert isinstance(data["database_name"], str)
    assert data["database_name"]


def test_overview(client: TestClient, require_mongodb: None, processing_summary: dict) -> None:
    response = client.get("/api/overview")
    assert response.status_code == 200
    data = response.json()
    expected = _expected_overview(processing_summary)

    for key in (
        "total_events",
        "unique_visitors",
        "unique_products",
        "total_views",
        "total_add_to_cart",
        "total_transactions",
        "visitor_conversion_rate",
        "date_range",
        "event_distribution",
    ):
        assert key in data

    assert data["total_events"] == expected["total_events"]
    assert data["unique_visitors"] == expected["unique_visitors"]
    assert data["unique_products"] == expected["unique_products"]
    assert data["total_views"] == expected["total_views"]
    assert data["total_add_to_cart"] == expected["total_add_to_cart"]
    assert data["total_transactions"] == expected["total_transactions"]
    assert data["total_events"] > 0
    assert isinstance(data["visitor_conversion_rate"], float)
    assert isinstance(data["event_distribution"], list)
    assert len(data["event_distribution"]) == 3


def test_funnel(client: TestClient, require_mongodb: None) -> None:
    response = client.get("/api/funnel")
    assert response.status_code == 200
    data = response.json()
    assert data["funnel_type"] == "visitor"
    assert "methodology" in data
    assert len(data["stages"]) == 3
    counts = [stage["count"] for stage in data["stages"]]
    assert counts[0] >= counts[1] >= counts[2]
    assert all(stage["count"] > 0 for stage in data["stages"])


def test_behavior(client: TestClient, require_mongodb: None) -> None:
    response = client.get("/api/behavior")
    assert response.status_code == 200
    data = response.json()
    summary = data["summary"]
    assert summary["total_visitors"] > 0
    assert summary["total_events"] > 0
    assert isinstance(data["activity_distribution"], list)
    assert len(data["activity_distribution"]) > 0
    assert len(data["top_visitors"]) <= 15
    assert "engagement_metrics" in data


def test_products_list(client: TestClient, require_mongodb: None) -> None:
    response = client.get("/api/products", params={"metric": "views", "limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["metric"] == "views"
    assert data["limit"] == 5
    assert len(data["products"]) == 5
    product = data["products"][0]
    assert product["rank"] == 1
    for key in ("item_id", "views", "add_to_cart", "transactions", "conversion_rate"):
        assert key in product
    assert product["views"] >= data["products"][1]["views"]


@pytest.fixture(scope="session")
def sample_item_id(client: TestClient, require_mongodb: None) -> int:
    response = client.get("/api/products", params={"metric": "views", "limit": 1})
    assert response.status_code == 200
    products = response.json()["products"]
    assert products
    return int(products[0]["item_id"])


def test_product_detail(
    client: TestClient,
    require_mongodb: None,
    sample_item_id: int,
) -> None:
    response = client.get(f"/api/products/{sample_item_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["item_id"] == sample_item_id
    assert data["views"] > 0
    assert "add_to_cart" in data
    assert "transactions" in data
    assert isinstance(data["conversion_rate"], float)
    assert isinstance(data["properties"], dict)


def test_product_detail_not_found(client: TestClient, require_mongodb: None) -> None:
    response = client.get("/api/products/999999999")
    assert response.status_code == 404


def test_time_series_daily(client: TestClient, require_mongodb: None) -> None:
    response = client.get("/api/time-series", params={"granularity": "daily"})
    assert response.status_code == 200
    data = response.json()
    assert data["granularity"] == "daily"
    assert len(data["series"]) > 0
    point = data["series"][0]
    for key in ("timestamp", "views", "addtocart", "transactions", "total_events"):
        assert key in point


def test_time_series_hourly(client: TestClient, require_mongodb: None) -> None:
    response = client.get("/api/time-series", params={"granularity": "hourly"})
    assert response.status_code == 200
    data = response.json()
    assert data["granularity"] == "hourly"
    assert len(data["series"]) > 0


def test_report(client: TestClient, require_mongodb: None) -> None:
    response = client.get("/api/report")
    assert response.status_code == 200
    data = response.json()
    for section in (
        "dataset_summary",
        "engagement",
        "conversion",
        "product_performance",
        "time_trends",
        "key_findings",
    ):
        assert section in data
    assert isinstance(data["key_findings"], list)
    assert len(data["key_findings"]) > 0
    perf = data["product_performance"]
    assert "top_viewed" in perf
    assert "top_purchased" in perf
    hv = perf["high_view_low_conversion"]
    assert "methodology" in hv
    assert "median_conversion_reference" in hv
    assert isinstance(hv["products"], list)


def test_dataset_info(client: TestClient, require_mongodb: None, processing_summary: dict) -> None:
    response = client.get("/api/dataset-info")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_name"] == "RetailRocket"
    assert data["processed_event_count"] == processing_summary["processed_row_counts"]["events"]
    assert data["category_count"] == processing_summary["processed_row_counts"]["category_tree"]
    assert data["unique_visitors"] == processing_summary["unique_visitors"]
    assert data["database_status"] == "connected"
    storage = data["processing_information"]["mongodb_analytical_storage"]
    assert storage["deployment_mode"] == "compact"
    assert storage["collections"]["analytics_global"] == 1
    assert storage["collections"]["product_metrics"] > 0
    assert "full_processed_dataset" in data["processing_information"]
