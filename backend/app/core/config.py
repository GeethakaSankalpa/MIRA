# import settings 
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

    # Neo4j
    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str

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
        # Uses psycopg driver with SQLAlchemy
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

settings = Settings()
