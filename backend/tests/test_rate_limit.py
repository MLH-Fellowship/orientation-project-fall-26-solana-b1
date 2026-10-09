import asyncio

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app


@pytest.fixture
def rate_limit_api(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'rate-limit.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    sessions = sessionmaker(bind=engine)

    def override_db():
        with sessions() as session:
            yield session

    previous_limit = settings.message_rate_limit
    previous_overrides = app.dependency_overrides.copy()
    settings.message_rate_limit = "5/second"
    app.dependency_overrides[get_db] = override_db
    try:
        yield
    finally:
        settings.message_rate_limit = previous_limit
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
        engine.dispose()


def api_client(ip_address: str) -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app, client=(ip_address, 12345))
    return httpx.AsyncClient(transport=transport, base_url="http://test")


async def send_to_missing_conversation(client, headers=None):
    return await client.post(
        "/api/conversations/missing/messages",
        json={"content": "hello"},
        headers=headers,
    )


@pytest.mark.asyncio
async def test_ip_limit_response_isolation_and_recovery(rate_limit_api):
    async with api_client("192.0.2.1") as limited_client, api_client("192.0.2.2") as other_client:
        for _ in range(5):
            assert (await send_to_missing_conversation(limited_client)).status_code == 404

        blocked = await send_to_missing_conversation(limited_client)
        assert blocked.status_code == 429
        assert blocked.json() == {"error": "Rate limit exceeded: 5 per 1 second"}
        assert blocked.headers["x-ratelimit-limit"] == "5"
        assert blocked.headers["x-ratelimit-remaining"] == "0"
        assert int(blocked.headers["retry-after"]) >= 0

        assert (await send_to_missing_conversation(other_client)).status_code == 404

        await asyncio.sleep(int(blocked.headers["retry-after"]) + 0.1)
        assert (await send_to_missing_conversation(limited_client)).status_code == 404


@pytest.mark.asyncio
async def test_authenticated_users_have_separate_limits(rate_limit_api):
    async with api_client("192.0.2.3") as client:
        tokens = []
        for email in ("one@example.com", "two@example.com"):
            credentials = {"email": email, "password": "strong-password"}
            assert (await client.post("/api/auth/signup", json=credentials)).status_code == 201
            login = await client.post("/api/auth/login", json=credentials)
            assert login.status_code == 200
            tokens.append(login.json()["access_token"])

        first_user = {"Authorization": f"Bearer {tokens[0]}"}
        second_user = {"Authorization": f"Bearer {tokens[1]}"}
        for _ in range(5):
            response = await send_to_missing_conversation(client, first_user)
            assert response.status_code == 404

        assert (await send_to_missing_conversation(client, first_user)).status_code == 429
        assert (await send_to_missing_conversation(client, second_user)).status_code == 404


@pytest.mark.asyncio
async def test_invalid_token_uses_the_ip_limit(rate_limit_api):
    async with api_client("192.0.2.4") as client:
        invalid_token = {"Authorization": "Bearer invalid"}
        for _ in range(4):
            assert (await send_to_missing_conversation(client, invalid_token)).status_code == 404
        assert (await send_to_missing_conversation(client)).status_code == 404
        assert (await send_to_missing_conversation(client, invalid_token)).status_code == 429
