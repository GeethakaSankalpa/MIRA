from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.db.neo4j import neo4j_client
from app.db.postgres import engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    # Neo4j check
    neo4j_ok = False
    try:
        with neo4j_client.driver.session() as session:
            session.run("RETURN 1").single()
        neo4j_ok = True
    except Exception:
        neo4j_ok = False

    # Postgres check
    pg_ok = False
    try:
        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))
        pg_ok = True
    except Exception:
        pg_ok = False

    # Qdrant check (optional in Phase 1)
    # Keep it simple: if no QDRANT_URL set, mark as "disabled"
    qdrant_status = "disabled" if not settings.QDRANT_URL else "unknown"

    status = "ok" if (neo4j_ok and pg_ok) else "degraded"

    return {
        "status": status,
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "dependencies": {
            "neo4j": "ok" if neo4j_ok else "down",
            "postgres": "ok" if pg_ok else "down",
            "qdrant": qdrant_status,
        },
    }