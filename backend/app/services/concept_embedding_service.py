from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.models.concept_embedding import ConceptEmbedding


class ConceptEmbeddingService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_embedding(
        self,
        *,
        concept_id: str,
        version: int,
        name: str,
        domain: str,
        status: str,
        vector: list[float],
    ) -> None:
        """
        MVP approach: delete existing (concept_id, version) then insert.
        Safe and simple for Phase 1 scale.
        """
        self.db.execute(
            delete(ConceptEmbedding).where(
                ConceptEmbedding.concept_id == concept_id,
                ConceptEmbedding.version == version,
            )
        )
        row = ConceptEmbedding(
            concept_id=concept_id,
            version=version,
            name=name,
            domain=domain,
            status=status,
            vector=vector,
        )
        self.db.add(row)
        self.db.commit()

    def list_active(self) -> list[ConceptEmbedding]:
        stmt = select(ConceptEmbedding).where(ConceptEmbedding.status == "active")
        return list(self.db.execute(stmt).scalars().all())
        