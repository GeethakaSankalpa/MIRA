import pytest
from sqlalchemy import text
from app.db.postgres import engine

pytestmark = pytest.mark.integration


def test_log_and_fetch_recent_queries(client):
    # Clean only test-generated query logs (safer than deleting everything)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM query_logs WHERE source LIKE 'test%';"))

    payload = {
        "query_text": "Explain Edmonds-Karp",
        "source": "test_suite",
        "metadata_json": {"topic": "max-flow"},
    }

    resp = client.post("/queries/log", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["query_text"] == payload["query_text"]
    assert data["source"] == payload["source"]

    resp2 = client.get("/queries/recent?limit=5")
    assert resp2.status_code == 200
    rows = resp2.json()
    assert len(rows) >= 1
    assert rows[0]["query_text"] == payload["query_text"]