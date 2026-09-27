from sqlalchemy import event
from sqlalchemy.orm import declarative_base

# Base classes for ORM models
LogisticsBase = declarative_base()
FinanceBase = declarative_base()

def configure_sqlite_engine(engine):
    """Configures SQLite engine for concurrent performance using WAL mode."""
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    return engine
