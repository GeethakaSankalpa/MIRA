from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),  # try root .env first, then backend/.env if added later
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_ENV: str = "local"
    APP_NAME: str = "MIRA"
    LOG_LEVEL: str = "INFO"

    # Neo4j (optional by default; required only when Neo4j is used)
    NEO4J_URI: str | None = Field(default=None)
    NEO4J_USER: str | None = Field(default=None)
    NEO4J_PASSWORD: str | None = Field(default=None)

    # Postgres
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # Qdrant (optional)
    QDRANT_URL: str | None = None

    @property
    def POSTGRES_DSN(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    def require_neo4j(self) -> None:
        """
        Enforce Neo4j config only in code paths that actually need Neo4j.
        This enables a clean minimal CI job without Neo4j.
        """
        missing: list[str] = []
        if not self.NEO4J_URI:
            missing.append("NEO4J_URI")
        if not self.NEO4J_USER:
            missing.append("NEO4J_USER")
        if not self.NEO4J_PASSWORD:
            missing.append("NEO4J_PASSWORD")

        if missing:
            raise RuntimeError(
                f"Neo4j configuration missing: {', '.join(missing)}. "
                f"Provide these env vars or disable Neo4j-dependent features/tests."
            )


settings = Settings()
