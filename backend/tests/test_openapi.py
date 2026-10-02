from fastapi.testclient import TestClient

from app.main import app


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
    for path, method in routes[-2:]:
        assert "404" in schema["paths"][path][method]["responses"]
        assert "422" in schema["paths"][path][method]["responses"]
