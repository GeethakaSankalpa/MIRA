import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base import Base


class QueryLog(Base):
    """
    Stores 'signals' (user queries/requests) for later learning.
    """
    __tablename__ = "query_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_text: Mapped[str] = mapped_column(String(4000), nullable=False)
    source: Mapped[str] = mapped_column(String(200), nullable=False)  # endpoint/module/source
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)