import time

import pytest
from fastapi.testclient import TestClient


def test_live_endpoint(client: TestClient):
    response = client.get("/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


def test_ready_endpoint(client: TestClient):
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "unready_services" in data


def test_metrics_endpoint(client: TestClient):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")


def test_metrics_contains_prometheus_metrics(client: TestClient):
    response = client.get("/metrics")
    content = response.text
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content


def test_health_endpoint(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "services" in data


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "message" in data


def test_request_id_header_in_response(client: TestClient):
    response = client.get("/api/v1/health")
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0


def test_live_returns_within_100ms(client: TestClient):
    start = time.perf_counter()
    client.get("/live")
    elapsed = (time.perf_counter() - start) * 1000
    assert elapsed < 100


def test_ready_with_migration_check(client: TestClient):
    response = client.get("/ready")
    data = response.json()
    assert "migrations" in data["checks"]
