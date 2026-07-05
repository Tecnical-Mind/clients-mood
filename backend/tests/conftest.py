import os
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("ENCRYPTION_KEY", "PPY6ZIkpn-uSDb0KJ3wruAQMdcJ4L6ZLLDGpQ1UUv1M=")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("SMTP_HOST", "localhost")
os.environ.setdefault("SMTP_FROM_ADDRESS", "reports@test.local")
os.environ.setdefault("COOKIE_SECURE", "false")
os.environ.setdefault("DISABLE_SCHEDULER", "true")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models.user import User


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session):
    from fastapi.testclient import TestClient

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def test_user(db_session):
    user = User(id=uuid.uuid4(), email="user@example.com")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def auth_client(client, test_user):
    from app.security import create_session_jwt

    token = create_session_jwt(test_user.id)
    client.cookies.set("session", token)
    return client
