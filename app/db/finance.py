from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.db.base import configure_sqlite_engine

# Ensure data directory exists
settings.FINANCE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

FINANCE_DATABASE_URL = f"sqlite:///{settings.FINANCE_DB_PATH.resolve()}"

finance_engine = create_engine(
    FINANCE_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
configure_sqlite_engine(finance_engine)

FinanceSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=finance_engine
)

def get_finance_db():
    """Dependency that yields a Finance database session."""
    db = FinanceSessionLocal()
    try:
        yield db
    finally:
        db.close()
