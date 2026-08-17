import os, tempfile
os.environ["DATABASE_URL"]="sqlite:///./test_lottery.db"
os.environ["JWT_SECRET_KEY"]="test-secret-key-that-is-long-enough"
import pytest
from fastapi.testclient import TestClient
from app.database import Base, engine
from app.main import app

@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine); Base.metadata.create_all(engine); yield
@pytest.fixture
def client(): return TestClient(app)

