import pytest
from pathlib import Path
import tempfile
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import LogisticsBase, FinanceBase, configure_sqlite_engine
from app.db.logistics import get_logistics_db
from app.db.finance import get_finance_db
from app.main import app
from app.models.member import HouseholdMember
from app.auth.pin import hash_pin

@pytest.fixture(scope="session")
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

@pytest.fixture(scope="session")
def test_logistics_engine(temp_dir):
    db_path = temp_dir / "test_logistics.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    configure_sqlite_engine(engine)
    LogisticsBase.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(scope="session")
def test_finance_engine(temp_dir):
    db_path = temp_dir / "test_finance.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    configure_sqlite_engine(engine)
    FinanceBase.metadata.create_all(bind=engine)
    return engine

@pytest.fixture
def logistics_session(test_logistics_engine):
    SessionLocal = sessionmaker(bind=test_logistics_engine, autocommit=False, autoflush=False)
    session = SessionLocal()
    
    # Ensure default members exist
    if session.query(HouseholdMember).count() == 0:
        mom = HouseholdMember(name="Mom", pin_hash=hash_pin("1234"), avatar_color="#ec4899")
        dad = HouseholdMember(name="Dad", pin_hash=hash_pin("5678"), avatar_color="#3b82f6")
        session.add_all([mom, dad])
        session.commit()
        
    yield session
    session.close()

@pytest.fixture
def finance_session(test_finance_engine):
    SessionLocal = sessionmaker(bind=test_finance_engine, autocommit=False, autoflush=False)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def client(logistics_session, finance_session):
    def override_logistics():
        yield logistics_session
        
    def override_finance():
        yield finance_session

    app.dependency_overrides[get_logistics_db] = override_logistics
    app.dependency_overrides[get_finance_db] = override_finance

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
