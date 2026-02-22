from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.query_log_api import QueryLogCreate, QueryLogRead
from app.services.query_log_service import QueryLogService

router = APIRouter(prefix="/queries", tags=["queries"])


@router.post("/log", response_model=QueryLogRead, status_code=201)
def log_query(payload: QueryLogCreate, db: Session = Depends(get_db)):
    service = QueryLogService(db)
    row = service.log_query(payload)
    return QueryLogRead(
        id=str(row.id),
        query_text=row.query_text,
        source=row.source,
        created_at=row.created_at,
        metadata_json=row.metadata_json,
    )


@router.get("/recent", response_model=list[QueryLogRead])
def recent_queries(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    service = QueryLogService(db)
    rows = service.recent(limit=limit)
    return [
        QueryLogRead(
            id=str(r.id),
            query_text=r.query_text,
            source=r.source,
            created_at=r.created_at,
            metadata_json=r.metadata_json,
        )
        for r in rows
    ]