# backend/app/models/reasoning_chain_summary.py
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReasoningChainSummary(Base):
    """
    Postgres mirror record for reasoning chains (summary form).

    Neo4j remains the primary store for the actual reasoning graph.
    This table stores a compact representation for:
      - fast listing / reporting
      - reinforcement counters (use_count, strength)
      - evidence / audit trail
      - future analytics

    steps_summary is a JSON array like:
      [
        {"step": 1, "concept_id": "...", "note": "...", "score": 0.82},
        ...
      ]
    """

    __tablename__ = "reasoning_chain_summaries"

    # Stable chain id (string UUID) to align across Neo4j + Postgres
    chain_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # The query that produced this chain (what triggered reasoning)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Root concept id (stable concept root id as you requested)
    root_concept_id: Mapped[str] = mapped_column(String(128), nullable=False)

    # Optional: version string if available (can be None)
    root_concept_version: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Summary of the chain steps (not the full graph)
    steps_summary: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)

    # Outcome feedback (v1: boolean)
    outcome_success: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Reinforcement/influence metrics
    use_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    strength: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)