def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "timestamp" in data
    assert "database" in data["services"]
    assert data["services"]["database"]["status"] in ("up", "down")


def test_root_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "ok")


def test_health_version(client):
    response = client.get("/api/v1/health")
    data = response.json()
    assert "version" in data
    assert data["version"] == "0.8.0"


def test_health_details(client):
    response = client.get("/api/v1/health/details")
    assert response.status_code == 200
    data = response.json()
    assert "tables" in data
    assert "latency_ms" in data
