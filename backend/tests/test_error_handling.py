from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.error_handling import spawn_exception_handlers
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_validation_error_uses_error_shape():
    response = client.post("/api/conversations", json={"title": []})

    assert response.status_code == 422
    assert response.json() == {
        "error": {"code": "VALIDATION_ERROR", "message": "Invalid Request!"}
    }


def test_missing_conversation_uses_error_shape():
    response = client.get("/api/conversations/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "NOT_FOUND", "message": "Conversation not found"}
    }


def test_unknown_route_uses_error_shape():
    response = client.get("/api/no-such-route")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "NOT_FOUND", "message": "Not Found"}
    }


def test_unhandled_exception_uses_error_shape():
    test_app = FastAPI()
    spawn_exception_handlers(test_app)

    @test_app.get("/boom")
    async def boom():
        raise RuntimeError("secret diagnostic")

    response = TestClient(test_app, raise_server_exceptions=False).get("/boom")

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "UNHANDLED_EXCEPTION",
            "message": "Internal server error or unknown exception occured.",
        }
    }
    assert "secret diagnostic" not in response.text

