from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """One place for all app settings.

    How it works:
    - Reads from environment variables or a .env file in the project root.
    - Keeps DB URL, JWT secret, token lifetime, and CORS in one spot so it's easy to change per environment.
    - Use ENV to switch between development/testing/production.
    Key vars you’ll likely touch:
      - DATABASE_URL: connection string for the DB
      - JWT_SECRET_KEY: used to sign access tokens (don’t use the default in prod)
      - ACCESS_TOKEN_EXPIRE_MINUTES: how long access tokens live
      - CORS_ORIGINS: list of allowed frontends (comma-separated in env)
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
