from app.error_handling import spawn_exception_handlers
from app.main import app
from app.schemas import ErrorResponse
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

client = TestClient(app, raise_server_exceptions=False)


def assert_error_response(response, status_code: int) -> ErrorResponse:
    assert response.status_code == status_code
    body = response.json()
    assert set(body) == {"error"}
    assert {"code", "message"}.issubset(body["error"])
    error = ErrorResponse.model_validate(body)
    assert error.error.code
    assert error.error.message
    return error


def test_validation_error_uses_error_shape():
    response = client.post("/api/conversations", json={"title": []})

    error = assert_error_response(response, 422)
    assert error.error.details
    assert {"loc", "msg", "type"}.issubset(error.error.details[0])


def test_missing_conversation_uses_error_shape():
    test_app = FastAPI()
    spawn_exception_handlers(test_app)

    @test_app.get("/missing")
    async def missing():
        raise HTTPException(status_code=404, detail="Conversation not found")

    response = TestClient(test_app).get("/missing")

    error = assert_error_response(response, 404)
    assert error.error.message == "Conversation not found"


def test_unknown_route_uses_error_shape():
    response = client.get("/api/no-such-route")

    error = assert_error_response(response, 404)
    assert error.error.message == "Not Found"


def test_unhandled_exception_uses_error_shape():
    test_app = FastAPI()
    spawn_exception_handlers(test_app)

    @test_app.get("/boom")
    async def boom():
        raise RuntimeError("secret diagnostic")

    response = TestClient(test_app, raise_server_exceptions=False).get("/boom")

    error = assert_error_response(response, 500)
    assert "internal" in error.error.message.lower()
    assert "secret diagnostic" not in response.text
