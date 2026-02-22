from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base


class ConceptEmbedding(Base):
    """
    Stores embeddings for concept versions.
    Keyed by (concept_id, version) because MIRA versioning is immutable.
    """
    __tablename__ = "concept_embeddings"
    __table_args__ = (
        UniqueConstraint("concept_id", "version", name="uq_concept_version_embedding"),
    )

    concept_id: Mapped[str] = mapped_column(String(64), primary_key=False, nullable=False)
    version: Mapped[int] = mapped_column(Integer, primary_key=False, nullable=False)

    # We keep some metadata for convenience (helps search results)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    domain: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # active/deprecated

    # JSONB stores array of floats
    vector: Mapped[list] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Not primary key; create SQLAlchemy surrogate by using composite unique constraint
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)