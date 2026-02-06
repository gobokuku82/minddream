"""Application Configuration

pydantic-settings 기반 환경 설정
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # === App ===
    APP_NAME: str = "Dream Agent V2"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production

    # === Server ===
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # === Database ===
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/dream_agent"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # === Redis (Optional) ===
    REDIS_URL: Optional[str] = None

    # === LLM ===
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    DEFAULT_LLM_PROVIDER: str = "openai"  # openai, anthropic
    DEFAULT_LLM_MODEL: str = "gpt-4o"

    # === Session ===
    SESSION_TIMEOUT_SEC: int = 3600  # 1 hour
    SESSION_MAX_TURNS: int = 100

    # === HITL ===
    HITL_TIMEOUT_SEC: int = 300  # 5 minutes
    HITL_MAX_RETRIES: int = 3

    # === Execution ===
    EXECUTION_TIMEOUT_SEC: int = 300
    EXECUTION_MAX_RETRIES: int = 3
    EXECUTION_MAX_PARALLEL: int = 5

    # === Logging ===
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json, text

    # === CORS ===
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]


# Singleton
settings = Settings()
