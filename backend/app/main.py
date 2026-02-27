import logging

from fastapi import FastAPI

from app.api.concepts import router as concepts_router
from app.api.health import router as health_router
from app.api.queries import router as queries_router
from app.api.search import router as search_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import RequestIdMiddleware
from app.db.neo4j import neo4j_client
from app.db.postgres import init_db

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="MIRA API", version="0.1.0")

# Middleware + Routers
app.add_middleware(RequestIdMiddleware)
app.include_router(health_router)
app.include_router(concepts_router)
app.include_router(queries_router)
app.include_router(search_router)


@app.on_event("startup")
def on_startup() -> None:
    """
    Startup logic (CI-friendly, production-safe):
    - Always initialize Postgres tables (needed for query logs / embeddings)
    - Connect Neo4j ONLY if it is configured via env vars (full CI / local / prod)
      This allows minimal CI jobs to run without requiring Neo4j config.
    """
    # Import models before creating tables (SQLAlchemy metadata discovery)
    import app.models  # noqa: F401

    # Initialize Postgres tables
    init_db()

    # Connect Neo4j only if configured
    if settings.NEO4J_URI and settings.NEO4J_USER and settings.NEO4J_PASSWORD:
        neo4j_client.connect()
        logger.info("Neo4j connected on startup.")
    else:
        logger.info("Neo4j not configured; skipping Neo4j connection on startup.")

    logger.info("Startup complete")


@app.on_event("shutdown")
def on_shutdown() -> None:
    """
    Shutdown logic:
    - Close Neo4j connection if it was used
    """
    try:
        # Only attempt close if it was configured (and potentially connected)
        if settings.NEO4J_URI and settings.NEO4J_USER and settings.NEO4J_PASSWORD:
            neo4j_client.close()
            logger.info("Neo4j connection closed on shutdown.")
    finally:
        logger.info("Shutdown complete")


logger.info("MIRA API initialized")
