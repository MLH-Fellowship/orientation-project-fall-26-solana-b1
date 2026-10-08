from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import create_database_engine, get_db
from app.main import app
from app.models import User
from app.routes.auth import password_hasher


def migration_config(database_url):
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


@pytest.fixture
def auth_api(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'auth.db'}"
    command.upgrade(migration_config(database_url), "head")
    engine = create_database_engine(database_url)
    sessions = sessionmaker(bind=engine)

    def override_db():
        with sessions() as session:
            yield session

    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            yield client, sessions
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
        engine.dispose()


def test_signup_hashes_password_and_login_token_resolves_current_user(auth_api):
    client, sessions = auth_api

    response = client.post(
        "/api/auth/signup",
        json={"email": "Alex@Example.com", "password": "correct horse battery staple"},
    )

    assert response.status_code == 201
    assert response.json() == {"message": "Signup successful"}
    with sessions() as session:
        user = session.scalar(select(User))
        assert user.email == "alex@example.com"
        assert user.password_hash != "correct horse battery staple"
        assert password_hasher.verify("correct horse battery staple", user.password_hash)

    login = client.post(
        "/api/auth/login",
        json={"email": "alex@example.com", "password": "correct horse battery staple"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "alex@example.com"
    assert response.json()["id"] == user.id


def test_login_and_duplicate_signup(auth_api):
    client, _ = auth_api
    credentials = {"email": "alex@example.com", "password": "strong-password"}
    assert client.post("/api/auth/signup", json=credentials).status_code == 201

    duplicate = client.post(
        "/api/auth/signup",
        json={"email": "ALEX@example.com", "password": "another-password"},
    )
    assert duplicate.status_code == 409

    response = client.post("/api/auth/login", json=credentials)
    assert response.status_code == 200
    assert response.json()["access_token"]

    for invalid_credentials in [
        {**credentials, "password": "wrong-password"},
        {**credentials, "email": "missing@example.com"},
    ]:
        response = client.post("/api/auth/login", json=invalid_credentials)
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Basic abc"},
        {"Authorization": "Bearer not-a-token"},
    ],
)
def test_current_user_rejects_missing_or_invalid_token(auth_api, headers):
    client, _ = auth_api

    response = client.get("/api/auth/me", headers=headers)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_current_user_rejects_expired_token(auth_api):
    client, _ = auth_api
    credentials = {"email": "alex@example.com", "password": "strong-password"}
    assert client.post("/api/auth/signup", json=credentials).status_code == 201
    previous_expiry = settings.jwt_expire_minutes
    try:
        settings.jwt_expire_minutes = -1
        token = client.post("/api/auth/login", json=credentials).json()["access_token"]
    finally:
        settings.jwt_expire_minutes = previous_expiry

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_user_without_password_cannot_log_in(auth_api):
    client, sessions = auth_api
    with sessions() as session:
        session.add(User(email="old@example.com"))
        session.commit()

    response = client.post(
        "/api/auth/login", json={"email": "old@example.com", "password": "strong-password"}
    )

    assert response.status_code == 401
