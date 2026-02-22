import pytest

pytestmark = pytest.mark.integration


def test_evolve_and_history(client, created_concepts):
    # Create v1
    payload_v1 = {
        "name": "Binary Search Tree",
        "description": "A tree where left < node < right.",
        "domain": "algorithms",
    }
    resp = client.post("/concepts", json=payload_v1)
    assert resp.status_code == 201

    concept_id = resp.json()["concept_id"]
    assert resp.json()["version"] == 1
    created_concepts.append(concept_id)

    # Evolve to v2
    payload_v2 = {
        "name": "Binary Search Tree",
        "description": "BST: left subtree keys < node key < right subtree keys.",
        "domain": "algorithms",
    }
    resp2 = client.post(f"/concepts/{concept_id}/evolve", json=payload_v2)
    assert resp2.status_code == 201
    assert resp2.json()["version"] == 2

    # Active concept should now be v2
    resp3 = client.get(f"/concepts/{concept_id}")
    assert resp3.status_code == 200
    data = resp3.json()
    assert data["version"] == 2
    assert data["status"] == "active"
    assert "BST" in data["description"]

    # History should show v2 then v1
    resp4 = client.get(f"/concepts/{concept_id}/history")
    assert resp4.status_code == 200
    hist = resp4.json()["versions"]

    assert len(hist) == 2
    assert hist[0]["version"] == 2
    assert hist[1]["version"] == 1
    assert hist[0]["status"] == "active"
    assert hist[1]["status"] == "deprecated"