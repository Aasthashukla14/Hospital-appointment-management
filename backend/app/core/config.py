"""
Application configuration.

Loads settings from environment variables / .env file using pydantic-settings.
All configurable values used across the application must live here — never
hardcode secrets, DB URLs, or tunables anywhere else in the codebase.
"""
from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---------------------------------------------------------------
    # General
    # ---------------------------------------------------------------
    PROJECT_NAME: str = "Hospital Appointment Management System"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True

    # ---------------------------------------------------------------
    # Database
    # ---------------------------------------------------------------
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "hims_appointment_db"
    DATABASE_URL: str | None = None

    # SQLAlchemy engine tuning
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_ECHO: bool = False

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v: str | None, info) -> str:
        if isinstance(v, str) and v:
            return v
        data = info.data
        return str(
            PostgresDsn.build(
                scheme="postgresql+psycopg2",
                username=data.get("POSTGRES_USER"),
                password=data.get("POSTGRES_PASSWORD"),
                host=data.get("POSTGRES_SERVER"),
                port=data.get("POSTGRES_PORT"),
                path=data.get("POSTGRES_DB"),
            )
        )

    # ---------------------------------------------------------------
    # JWT / Security
    # ---------------------------------------------------------------
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_super_secret_key_value"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # ---------------------------------------------------------------
    # CORS
    # ---------------------------------------------------------------
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # ---------------------------------------------------------------
    # Pagination defaults
    # ---------------------------------------------------------------
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # ---------------------------------------------------------------
    # Business rules
    # ---------------------------------------------------------------
    DEFAULT_APPOINTMENT_DURATION_MINUTES: int = 30

    # ---------------------------------------------------------------
    # Logging
    # ---------------------------------------------------------------
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — settings are read once per process."""
    return Settings()


settings = get_settings()
