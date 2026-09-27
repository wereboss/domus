from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.db.base import configure_sqlite_engine

# Ensure data directory exists
settings.LOGISTICS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

LOGISTICS_DATABASE_URL = f"sqlite:///{settings.LOGISTICS_DB_PATH.resolve()}"

logistics_engine = create_engine(
    LOGISTICS_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
configure_sqlite_engine(logistics_engine)

LogisticsSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=logistics_engine
)

def get_logistics_db():
    """Dependency that yields a Logistics database session."""
    db = LogisticsSessionLocal()
    try:
        yield db
    finally:
        db.close()
