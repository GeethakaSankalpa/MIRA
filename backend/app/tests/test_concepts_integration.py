import pytest

pytestmark = pytest.mark.integration


def test_create_and_get_concept(client, created_concepts):
    payload = {
        "name": "Edmonds-Karp",
        "description": "Maximum flow algorithm using BFS to find augmenting paths.",
        "domain": "algorithms",
    }

    resp = client.post("/concepts", json=payload)
    assert resp.status_code == 201

    concept_id = resp.json()["concept_id"]
    created_concepts.append(concept_id)

    resp2 = client.get(f"/concepts/{concept_id}")
    assert resp2.status_code == 200

    data = resp2.json()
    assert data["concept_id"] == concept_id
    assert data["version"] == 1
    assert data["status"] == "active"