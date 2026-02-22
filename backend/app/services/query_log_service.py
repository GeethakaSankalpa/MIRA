from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.models.query_log import QueryLog
from app.models.query_log_api import QueryLogCreate


class QueryLogService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def log_query(self, payload: QueryLogCreate) -> QueryLog:
        row = QueryLog(
            query_text=payload.query_text,
            source=payload.source,
            metadata_json=payload.metadata_json,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def recent(self, limit: int = 50) -> list[QueryLog]:
        stmt = select(QueryLog).order_by(desc(QueryLog.created_at)).limit(limit)
        return list(self.db.execute(stmt).scalars().all())