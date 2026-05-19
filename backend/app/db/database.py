import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from ..core.settings import get_settings

settings = get_settings()

# Build the SQLAlchemy engine using the configured DATABASE_URL.
# For SQLite, add one flag so it works nicely with FastAPI's worker model.
DATABASE_URL = settings.DATABASE_URL

is_sqlite = DATABASE_URL.startswith("sqlite:")

engine_kwargs = {}
if is_sqlite:
    # For SQLite, allow the same connection across threads for the dev server.
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)

# Session factory: create a new DB session per request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLAlchemy base class for all models
Base = declarative_base()

def get_db():
    """Return a fresh DB session for each request, and close it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
