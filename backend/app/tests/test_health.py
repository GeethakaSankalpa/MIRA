def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()

    # In minimal CI, Neo4j is intentionally not configured -> degraded is expected.
    assert data["status"] in ("ok", "degraded")
    assert "app" in data
