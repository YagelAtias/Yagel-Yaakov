import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from ..core.settings import get_settings

settings = get_settings()

# Create SQLAlchemy engine. For SQLite only, we need check_same_thread=False.
DATABASE_URL = settings.DATABASE_URL

is_sqlite = DATABASE_URL.startswith("sqlite:")

engine_kwargs = {}
if is_sqlite:
    # Using check_same_thread=False is required for SQLite with FastAPI async workers.
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)

# Factory to generate database sessions on demand
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All models will inherit from this Base class
Base = declarative_base()

def get_db():
    """Dependency generator that yields a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
