import pytest
from sqlalchemy import text
from app.db.postgres import engine

pytestmark = pytest.mark.integration


def test_search_returns_best_match(client, monkeypatch, created_concepts):
    # Clear only embedding/search artifacts for test isolation.
    # (Concept cleanup handled by created_concepts fixture via Neo4j)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM concept_embeddings;"))
        conn.execute(text("DELETE FROM query_logs WHERE source IN ('search') OR source LIKE 'test%';"))

    # Monkeypatch embed_text so tests are deterministic
    def fake_embed_text(text_input: str) -> list[float]:
        # Two simple orthogonal vectors
        if "tree" in text_input.lower():
            return [1.0, 0.0]
        return [0.0, 1.0]

    # IMPORTANT: patch where embed_text is USED (ConceptService module), not where it is defined
    monkeypatch.setattr("app.services.concept_service.embed_text", fake_embed_text)

    # Create two concepts
    resp1 = client.post(
        "/concepts",
        json={
            "name": "AVL Tree",
            "description": "Self balancing tree",
            "domain": "algorithms",
        },
    )
    assert resp1.status_code == 201
    avl_id = resp1.json()["concept_id"]
    created_concepts.append(avl_id)

    resp2 = client.post(
        "/concepts",
        json={
            "name": "PostgreSQL",
            "description": "Database system",
            "domain": "databases",
        },
    )
    assert resp2.status_code == 201
    pg_id = resp2.json()["concept_id"]
    created_concepts.append(pg_id)

    # Search for "tree"
    resp = client.get("/search?query=tree&limit=2")
    assert resp.status_code == 200
    data = resp.json()

    assert data["query"] == "tree"
    assert len(data["results"]) >= 1
    assert data["results"][0]["concept_id"] == avl_id

    # Confirm a query log was written by /search
    logs = client.get("/queries/recent?limit=5").json()
    assert len(logs) >= 1
    assert logs[0]["source"] == "search"
    assert "matches" in logs[0]["metadata_json"]