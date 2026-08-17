import os
import tempfile

import pytest
from app.db.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create a temporary file path for sqlite tests to avoid cluttering the repository root
db_fd, db_path = tempfile.mkstemp(suffix=".db", prefix="bondguard_test_")
os.close(db_fd)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def cleanup_temp_db():
    yield
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def seeded_db_session(db_session):
    # Seed all baseline data for tests
    from scripts.seed.seed_concentration_limits import (
        seed_limits as seed_concentration_limits,
    )
    from scripts.seed.seed_liquidity_assumptions import seed_assumptions
    from scripts.seed.seed_portfolio import seed_data as seed_portfolio_data
    from scripts.seed.seed_risk_limits import seed_limits as seed_risk_limits
    from scripts.seed.seed_stress_scenarios import (
        seed_scenarios as seed_stress_scenarios,
    )

    seed_portfolio_data(db_session)
    seed_stress_scenarios(db_session)
    seed_assumptions(db_session)
    seed_concentration_limits(db_session)
    seed_risk_limits(db_session)
    
    yield db_session

@pytest.fixture(scope="function")
def client(seeded_db_session):
    def override_get_db():
        try:
            yield seeded_db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def clean_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

