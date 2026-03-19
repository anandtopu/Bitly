import pytest
from fastapi.testclient import TestClient
import fakeredis
from app.core import redis as app_redis
app_redis.redis_client = fakeredis.FakeRedis(decode_responses=True)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.main import app
from datetime import datetime, timezone, timedelta

# Avoid timezone issues with SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_create_short_url():
    response = client.post(
        "/api/v1/urls",
        json={"long_url": "https://www.google.com"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["long_url"] == "https://www.google.com/"
    assert "short_code" in data

def test_create_custom_alias():
    response = client.post(
        "/api/v1/urls",
        json={"long_url": "https://www.google.com", "custom_alias": "goog"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["short_code"] == "goog"

def test_custom_alias_collision():
    # First request
    client.post(
        "/api/v1/urls",
        json={"long_url": "https://www.example.com", "custom_alias": "dup"}
    )
    # Second identical alias request
    response = client.post(
        "/api/v1/urls",
        json={"long_url": "https://www.test.com", "custom_alias": "dup"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Custom alias already exists."

def test_redirect_to_long_url():
    # Create
    response = client.post(
        "/api/v1/urls",
        json={"long_url": "https://www.youtube.com", "custom_alias": "yt"}
    )
    assert response.status_code == 201
    
    # Redirect
    response = client.get("/yt", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "https://www.youtube.com/"

def test_redirect_not_found():
    response = client.get("/nonexistent", follow_redirects=False)
    assert response.status_code == 404

def test_expiration_date():
    # Create expired link
    past_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    response = client.post(
        "/api/v1/urls",
        json={"long_url": "https://www.example.com", "custom_alias": "exp", "expires_at": past_date}
    )
    assert response.status_code == 201
    
    # Try accessing
    response = client.get("/exp", follow_redirects=False)
    assert response.status_code == 404
