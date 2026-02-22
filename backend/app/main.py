import logging
from fastapi import FastAPI
from app.core.logging import setup_logging
from app.api.health import router as health_router
from app.api.concepts import router as concepts_router
from app.db.neo4j import neo4j_client
from app.db.postgres import init_db
from app.api.queries import router as queries_router
from app.api.search import router as search_router
from app.core.middleware import RequestIdMiddleware

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="MIRA API", version="0.1.0")

app.add_middleware(RequestIdMiddleware)
app.include_router(health_router)
app.include_router(concepts_router)
app.include_router(queries_router)
app.include_router(search_router)

@app.on_event("startup")
def on_startup() -> None:
    neo4j_client.connect()
    import app.models  # noqa: F401
    init_db()
    logger.info("Startup complete")


@app.on_event("shutdown")
def on_shutdown() -> None:
    neo4j_client.close()
    logger.info("Shutdown complete")

logger.info("MIRA API initialized")