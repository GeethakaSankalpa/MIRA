import logging
from neo4j import GraphDatabase, Driver
from app.core.config import settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    """
    Purpose:
    - A single place to create and manage the Neo4j driver connection.
    - Keeps DB code out of API routes (clean architecture).
    """
    def __init__(self) -> None:
        self._driver: Driver | None = None

    def connect(self) -> None:
        if self._driver is None:
            logger.info("Connecting to Neo4j at %s", settings.NEO4J_URI)
            self._driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            )

    def close(self) -> None:
        if self._driver is not None:
            logger.info("Closing Neo4j connection")
            self._driver.close()
            self._driver = None

    @property
    def driver(self) -> Driver:
        if self._driver is None:
            raise RuntimeError("Neo4j driver is not connected. Call connect() first.")
        return self._driver


neo4j_client = Neo4jClient()