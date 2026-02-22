import logging
import uuid
from datetime import datetime, timezone
from neo4j import Driver
from app.models.concept import ConceptCreate, ConceptRead
from app.models.concept_evolution import ConceptEvolveRequest, ConceptHistoryResponse, ConceptVersion
from sqlalchemy.orm import Session
from app.services.embedding_service import embed_text
from app.services.concept_embedding_service import ConceptEmbeddingService

logger = logging.getLogger(__name__)


class ConceptService:
    """
    Purpose:
    - Contains the business logic for concept creation and retrieval.
    - Keeps API routes thin and readable.
    """

    def __init__(self, driver: Driver, pg_db: Session | None = None) -> None:
        self.driver = driver
        self.pg_db = pg_db

    def create_concept(self, payload: ConceptCreate) -> str:
        concept_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        cypher = """
        CREATE (c:Concept {
            concept_id: $concept_id,
            name: $name,
            description: $description,
            domain: $domain,
            version: 1,
            confidence: 0.5,
            status: 'active',
            created_at: datetime($now),
            updated_at: datetime($now)
        })
        RETURN c.concept_id AS concept_id
        """

        with self.driver.session() as session:
            result = session.run(
                cypher,
                concept_id=concept_id,
                name=payload.name,
                description=payload.description,
                domain=payload.domain,
                now=now.isoformat(),
            )
            record = result.single()
            if not record:
                raise RuntimeError("Failed to create concept")

        if self.pg_db is not None:
            text = f"{payload.name}\n{payload.description}\nDomain: {payload.domain}"
            vector = embed_text(text)
            ConceptEmbeddingService(self.pg_db).upsert_embedding(
                concept_id=concept_id,
                version=1,
                name=payload.name,
                domain=payload.domain,
                status="active",
                vector=vector,
            )
        logger.info("Created concept concept_id=%s domain=%s", concept_id, payload.domain)
        return concept_id

    def get_active_concept(self, concept_id: str) -> ConceptRead | None:
        cypher = """
        MATCH (c:Concept {concept_id: $concept_id, status: 'active'})
        RETURN c
        LIMIT 1
        """
        with self.driver.session() as session:
            result = session.run(cypher, concept_id=concept_id)
            record = result.single()
            if not record:
                return None

            c = record["c"]
            return ConceptRead(
                concept_id=c["concept_id"],
                name=c["name"],
                description=c["description"],
                domain=c["domain"],
                version=int(c["version"]),
                confidence=float(c["confidence"]),
                status=c["status"],
                created_at=c["created_at"].to_native(),
                updated_at=c["updated_at"].to_native(),
            )
        
    def evolve_concept(self, concept_id: str, payload: ConceptEvolveRequest) -> int:
        """
        Create a new version of an existing concept.

        Rules:
        - find active node (concept_id + status=active)
        - create new node with version+1
        - mark old as deprecated
        - link new -> old with EVOLVED_FROM
        """
        cypher = """
        MATCH (old:Concept {concept_id: $concept_id, status: 'active'})
        WITH old
        CREATE (new:Concept {
            concept_id: old.concept_id,
            name: $name,
            description: $description,
            domain: $domain,
            version: old.version + 1,
            confidence: old.confidence,
            status: 'active',
            created_at: old.created_at,
            updated_at: datetime($now)
        })
        SET old.status = 'deprecated'
        CREATE (new)-[:EVOLVED_FROM]->(old)
        RETURN new.version AS new_version
        """

        now = datetime.now(timezone.utc).isoformat()

        with self.driver.session() as session:
            result = session.run(
                cypher,
                concept_id=concept_id,
                name=payload.name,
                description=payload.description,
                domain=payload.domain,
                now=now,
            )
            record = result.single()
            if not record:
                # no active concept found
                return -1

            new_version = int(record["new_version"])


        if self.pg_db is not None and new_version != -1:
            # Deprecate all previous embeddings for this concept_id
            # (simple approach: mark existing rows deprecated)
            from sqlalchemy import update
            from app.models.concept_embedding import ConceptEmbedding

            self.pg_db.execute(
                update(ConceptEmbedding)
                .where(ConceptEmbedding.concept_id == concept_id)
                .values(status="deprecated")
            )
            self.pg_db.commit()

            text = f"{payload.name}\n{payload.description}\nDomain: {payload.domain}"
            vector = embed_text(text)
            ConceptEmbeddingService(self.pg_db).upsert_embedding(
                concept_id=concept_id,
                version=new_version,
                name=payload.name,
                domain=payload.domain,
                status="active",
                vector=vector,
            )

        logger.info("Evolved concept concept_id=%s new_version=%s", concept_id, new_version)
        return new_version

    def get_concept_history(self, concept_id: str) -> ConceptHistoryResponse:
        """
        Return all versions newest -> oldest.
        We traverse backwards following EVOLVED_FROM edges.
        """
        cypher = """
        MATCH (latest:Concept {concept_id: $concept_id, status: 'active'})
        OPTIONAL MATCH path = (latest)-[:EVOLVED_FROM*0..]->(older:Concept)
        WITH nodes(path) AS ns
        UNWIND ns AS n
        WITH DISTINCT n
        RETURN n
        ORDER BY n.version DESC
        """

        versions: list[ConceptVersion] = []

        with self.driver.session() as session:
            result = session.run(cypher, concept_id=concept_id)
            records = list(result)

        for r in records:
            n = r["n"]
            versions.append(
                ConceptVersion(
                    concept_id=n["concept_id"],
                    name=n["name"],
                    description=n["description"],
                    domain=n["domain"],
                    version=int(n["version"]),
                    confidence=float(n["confidence"]),
                    status=n["status"],
                    created_at=n["created_at"].to_native(),
                    updated_at=n["updated_at"].to_native(),
                )
            )

        return ConceptHistoryResponse(versions=versions)