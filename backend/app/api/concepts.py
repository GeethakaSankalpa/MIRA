from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.db.neo4j import neo4j_client
from app.models.concept import ConceptCreate, ConceptRead
from app.models.concept_evolution import ConceptEvolveRequest, ConceptHistoryResponse
from app.services.concept_service import ConceptService

router = APIRouter(prefix="/concepts", tags=["concepts"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_concept(payload: ConceptCreate, db: Session = Depends(get_db)):
    """
    Creates Concept v1 in Neo4j AND stores embedding in Postgres.
    """
    service = ConceptService(neo4j_client.driver, pg_db=db)
    concept_id = service.create_concept(payload)
    return {"concept_id": concept_id, "version": 1}


@router.get("/{concept_id}", response_model=ConceptRead)
def get_concept(concept_id: str):
    """
    Reads the active concept from Neo4j.
    """
    service = ConceptService(neo4j_client.driver)
    concept = service.get_active_concept(concept_id)
    if concept is None:
        raise HTTPException(status_code=404, detail="Concept not found")
    return concept


@router.post("/{concept_id}/evolve", status_code=status.HTTP_201_CREATED)
def evolve_concept(concept_id: str, payload: ConceptEvolveRequest, db: Session = Depends(get_db)):
    """
    Evolves concept in Neo4j (creates new version) AND stores new embedding in Postgres.
    """
    service = ConceptService(neo4j_client.driver, pg_db=db)
    new_version = service.evolve_concept(concept_id, payload)
    if new_version == -1:
        raise HTTPException(status_code=404, detail="Active concept not found")
    return {"concept_id": concept_id, "version": new_version}


@router.get("/{concept_id}/history", response_model=ConceptHistoryResponse)
def concept_history(concept_id: str):
    """
    Reads version history from Neo4j.
    """
    service = ConceptService(neo4j_client.driver)
    history = service.get_concept_history(concept_id)
    if len(history.versions) == 0:
        raise HTTPException(status_code=404, detail="Concept not found")
    return history