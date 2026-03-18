import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, bloom
from app.database import Base, get_db

# Test DB (SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

Base.metadata.create_all(bind=engine)

# Override DB dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# ---------------- TESTS ----------------

def test_shorten_url():
    response = client.post(
        "/api/shorten", 
        json={"longUrl": "https://www.example.com"}
    )
    assert response.status_code == 200

    data = response.json()
    assert "shortCode" in data
    assert len(data["shortCode"]) == 6

    # Bloom filter check
    assert bloom.might_exist(data["shortCode"])


def test_redirect_existing_url():
    post_resp = client.post(
        "/api/shorten", 
        json={"longUrl": "https://www.test-redirect.com"}
    )
    short_code = post_resp.json()["shortCode"]

    redirect_resp = client.get(
        f"/{short_code}", 
        follow_redirects=False
    )

    assert redirect_resp.status_code in [302, 307]
    assert redirect_resp.headers["location"] == "https://www.test-redirect.com"


def test_redirect_nonexistent_url():
    response = client.get("/invalid_code")
    assert response.status_code == 404