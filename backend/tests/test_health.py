def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["database"] == "healthy"
    assert data["academic_cycle"] == "2026-2027"
    assert "timestamp_utc" in data

def test_root_endpoint(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "AvedanSetu" in res.json()["service"] or "ReguFlow 360" in res.json()["service"]
