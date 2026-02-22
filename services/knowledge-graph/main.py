from fastapi import FastAPI
from shared.schemas.concept import ConceptCreate
from db import get_session
import uuid
from datetime import datetime

app = FastAPI(title="MIRA Knowledge Graph Service")

@app.get("/health")
def health():
    return {"status": "alive"}

@app.post("/concepts")
def create_concept(concept: ConceptCreate):
    concept_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    query = """
    CREATE (c:Concept {
      concept_id: $concept_id,
      name: $name,
      description: $description,
      domain: $domain,
      version: 1,
      confidence: 0.5,
      created_at: $now,
      updated_at: $now,
      status: 'active'
    })
    RETURN c
    """

    with get_session() as session:
        session.run(query, **concept.dict(), concept_id=concept_id, now=now)

    return {"concept_id": concept_id, "version": 1}

@app.post("/concepts/{concept_id}/evolve")
def evolve_concept(concept_id: str, updated: ConceptCreate):
    new_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    query = """
    MATCH (old:Concept {concept_id: $concept_id, status: 'active'})
    SET old.status = 'deprecated'
    CREATE (new:Concept {
      concept_id: $new_id,
      name: $name,
      description: $description,
      domain: $domain,
      version: old.version + 1,
      confidence: old.confidence,
      created_at: old.created_at,
      updated_at: $now,
      status: 'active'
    })
    CREATE (new)-[:EVOLVED_FROM]->(old)
    RETURN new
    """

    with get_session() as session:
        session.run(
            query,
            concept_id=concept_id,
            new_id=new_id,
            name=updated.name,
            description=updated.description,
            domain=updated.domain,
            now=now
        )

    return {"new_concept_id": new_id}
