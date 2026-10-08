from fastapi.testclient import TestClient

from app.main import app
from app.schemas import ErrorResponse


def test_openapi_documents_routes_and_payloads():
    with TestClient(app) as client:
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert client.get("/docs").status_code == 200

    routes = [
        ("/api/health", "get"),
        ("/api/conversations", "get"),
        ("/api/conversations", "post"),
        ("/api/conversations/{conversation_id}", "get"),
        ("/api/conversations/{conversation_id}/usage", "get"),
        ("/api/conversations/{conversation_id}/messages", "post"),
    ]
    for path, method in routes:
        operation = schema["paths"][path][method]
        assert operation["description"]
        assert operation["summary"]
        assert operation["responses"]["200"]["content"]["application/json"]["schema"]

    models = schema["components"]["schemas"]
    assert models["MessageCreate"]["examples"][0]["content"]
    assert models["ConversationCreate"]["properties"]["title"]["examples"]
    assert models["MessageOut"]["properties"]["content"]["examples"]
    for path, method in [
        ("/api/conversations/{conversation_id}", "get"),
        ("/api/conversations/{conversation_id}/usage", "get"),
        ("/api/conversations/{conversation_id}/messages", "post"),
    ]:
        assert "404" in schema["paths"][path][method]["responses"]
        assert "422" in schema["paths"][path][method]["responses"]


def test_documented_validation_response_matches_invalid_message():
    with TestClient(app) as client:
        response = client.post("/api/conversations/missing/messages", json={"content": " "})
        assert response.status_code == 422
        error = ErrorResponse.model_validate(response.json())
        assert error.error.details[0]["loc"] == ["body", "content"]
        schema = client.get("/openapi.json").json()
    documented = schema["paths"]["/api/conversations/{conversation_id}/messages"]["post"][
        "responses"
    ]["422"]
    assert documented["content"]["application/json"]["schema"]["$ref"].endswith("/ErrorResponse")
