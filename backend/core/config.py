"""Application configuration loaded from environment / .env via Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings sourced from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # Application
    APP_NAME: str = "ResumeScreening"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/resume_db"

    # JWT
    JWT_SECRET_KEY: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # File upload
    MAX_UPLOAD_SIZE_MB: int = 20
    UPLOAD_DIR: str = "./uploads"
    ALLOWED_FILE_TYPES: list[str] = ["pdf", "docx", "txt"]

    # LLM routing (parsing). Groq online / Gemma via Ollama offline.
    LLM_MODE: str = "auto"  # auto | online | offline
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_TIMEOUT_SECONDS: int = 30
    LLM_HEALTHCHECK_TIMEOUT_SECONDS: float = 3.0
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma3:4b"

    # Embeddings. Default: in-process sentence-transformers (no external service).
    # Set EMBEDDING_PROVIDER=ollama for a fully-offline nomic-embed path.
    EMBEDDING_PROVIDER: str = "sentence_transformers"  # sentence_transformers | ollama
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_TIMEOUT_SECONDS: int = 30

    # Vector store
    VECTOR_STORE: str = "auto"  # pgvector | faiss | auto
    FAISS_INDEX_PATH: str = "./data/faiss_index"

    @field_validator("CORS_ORIGINS", "ALLOWED_FILE_TYPES", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        """Allow comma-separated strings in env vars for list-typed settings."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def is_production(self) -> bool:
        """Return True when running in a production environment."""
        return self.APP_ENV.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
