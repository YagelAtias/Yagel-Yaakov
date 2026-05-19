from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Centralized application settings.

    Configure via environment variables or a .env file at the project root.
    Key variables:
      - DATABASE_URL: SQLAlchemy URL for the database
      - JWT_SECRET_KEY: Secret for signing JWTs (required in non-dev)
      - ACCESS_TOKEN_EXPIRE_MINUTES: JWT access token lifetime
      - CORS_ORIGINS: Comma-separated list of allowed origins
      - ENV: one of [development, testing, production]
    """

    ENV: str = "development"

    # Default to the existing local SQLite file in the project root
    # e.g., sqlite:///C:/.../distress_engine.db
    @staticmethod
    def _default_sqlite_url() -> str:
        # backend/app/core/settings.py -> up 4 levels to project root
        p = Path(__file__).resolve()
        for _ in range(4):
            p = p.parent
        db_path = p / "distress_engine.db"
        return f"sqlite:///{db_path}"

    DATABASE_URL: str = _default_sqlite_url.__func__()  # type: ignore[attr-defined]

    # Security
    JWT_SECRET_KEY: str = "dev-secret-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours by default

    # CORS
    # Provide as a comma-separated list in ENV (e.g., "http://localhost:5173,http://127.0.0.1:5173")
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
