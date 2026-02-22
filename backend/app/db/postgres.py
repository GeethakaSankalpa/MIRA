import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base  # <-- moved here

logger = logging.getLogger(__name__)

engine = create_engine(settings.POSTGRES_DSN, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db() -> None:
    """
    Create tables if they do not exist.
    IMPORTANT: Ensure models are imported BEFORE calling this.
    """
    logger.info("Initializing Postgres tables (create_all if needed)")
    Base.metadata.create_all(bind=engine)