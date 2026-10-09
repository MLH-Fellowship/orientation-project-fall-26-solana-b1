"""Test usage through the API, Gemini SDK, and a migrated SQLite database."""

import json
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.database import create_database_engine
from app.models import Message


def create_conversation(client, title="Usage test"):
    response = client.post("/api/conversations", json={"title": title})
    assert response.status_code == 200
    return response.json()["id"]


def send_message(client, conversation_id, content="Hello"):
    response = client.post(
        f"/api/conversations/{conversation_id}/messages", json={"content": content}
    )
    assert response.status_code == 200
    return response.json()


def assert_usage(client, conversation_id, prompt, completion):
    response = client.get(f"/api/conversations/{conversation_id}/usage")
    assert response.status_code == 200
    assert response.json() == {
        "conversation_id": conversation_id,
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": prompt + completion,
    }


def test_usage_is_saved_summed_and_limited_to_one_conversation(migrated_api, gemini_response):
    client, sessions = migrated_api
    conversation_id = create_conversation(client)
    gemini_response("First reply", {"promptTokenCount": 12, "candidatesTokenCount": 4})
    first = send_message(client, conversation_id)
    assert (first["prompt_tokens"], first["completion_tokens"]) == (12, 4)
    assert_usage(client, conversation_id, 12, 4)

    route = gemini_response("Second reply", {"promptTokenCount": 20, "candidatesTokenCount": 6})
    second = send_message(client, conversation_id, "Next question")
    assert (second["prompt_tokens"], second["completion_tokens"]) == (20, 6)
    assert json.loads(route.calls[0].request.body)["contents"] == [
        {"role": "user", "parts": [{"text": "Hello"}]},
        {"role": "model", "parts": [{"text": "First reply"}]},
        {"role": "user", "parts": [{"text": "Next question"}]},
    ]

    other_id = create_conversation(client)
    gemini_response("Other reply", {"promptTokenCount": 100, "candidatesTokenCount": 50})
    send_message(client, other_id)
    assert_usage(client, conversation_id, 32, 10)
    assert_usage(client, other_id, 100, 50)

    response = client.get(f"/api/conversations/{conversation_id}")
    assert response.status_code == 200
    messages = {message["id"]: message for message in response.json()["messages"]}
    assert messages[first["id"]] == first
    assert messages[second["id"]] == second
    with sessions() as session:
        session.expire_all()
        saved = session.get(Message, first["id"])
        assert (saved.prompt_tokens, saved.completion_tokens) == (12, 4)
        users = session.query(Message).filter_by(role="user").all()
        assert all(m.prompt_tokens is None and m.completion_tokens is None for m in users)
    assert all(
        m["prompt_tokens"] is None and m["completion_tokens"] is None
        for m in messages.values()
        if m["role"] == "user"
    )


@pytest.mark.parametrize(
    "usage, expected",
    [
        (None, (None, None)),
        ({}, (None, None)),
        ({"promptTokenCount": 7}, (7, None)),
        ({"candidatesTokenCount": 3}, (None, 3)),
        ({"promptTokenCount": 0, "candidatesTokenCount": 0}, (0, 0)),
    ],
)
def test_missing_and_zero_counts(migrated_api, gemini_response, usage, expected):
    client, sessions = migrated_api
    conversation_id = create_conversation(client)
    gemini_response(usage=usage)
    message = send_message(client, conversation_id)
    assert (message["prompt_tokens"], message["completion_tokens"]) == expected
    with sessions() as session:
        saved = session.get(Message, message["id"])
        assert (saved.prompt_tokens, saved.completion_tokens) == expected
    assert_usage(client, conversation_id, expected[0] or 0, expected[1] or 0)
    gemini_response(usage={"promptTokenCount": 11, "candidatesTokenCount": 2})
    send_message(client, conversation_id, "Another question")
    assert_usage(client, conversation_id, (expected[0] or 0) + 11, (expected[1] or 0) + 2)


def test_empty_conversation_and_unknown_id(migrated_api, gemini_http):
    client, _ = migrated_api
    conversation_id = create_conversation(client)
    assert_usage(client, conversation_id, 0, 0)
    response = client.get("/api/conversations/missing/usage")
    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Conversation not found"
    assert len(gemini_http.calls) == 0


def test_title_tokens_and_api_total_are_excluded(migrated_api, gemini_response, gemini_http):
    client, _ = migrated_api
    conversation_id = create_conversation(client, title=None)
    gemini_response(
        "Hello back",
        {
            "promptTokenCount": 12,
            "candidatesTokenCount": 4,
            "totalTokenCount": 99,
            "thoughtsTokenCount": 83,
        },
    )
    gemini_response("A Short Test Title", {"promptTokenCount": 100, "candidatesTokenCount": 10})
    send_message(client, conversation_id)
    assert len(gemini_http.calls) == 2
    response = client.get(f"/api/conversations/{conversation_id}")
    assert response.json()["title"] == "A Short Test Title"
    assert_usage(client, conversation_id, 12, 4)


def test_gemini_error_keeps_saved_usage(migrated_api, gemini_response, gemini_http):
    client, sessions = migrated_api
    conversation_id = create_conversation(client)
    gemini_response(usage={"promptTokenCount": 12, "candidatesTokenCount": 4})
    send_message(client, conversation_id)
    gemini_http.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-test:generateContent",
        status=503,
        json={"error": {"code": 503, "message": "API unavailable", "status": "UNAVAILABLE"}},
    )
    response = client.post(
        f"/api/conversations/{conversation_id}/messages", json={"content": "Try again"}
    )
    assert response.status_code == 500
    assert_usage(client, conversation_id, 12, 4)
    with sessions() as session:
        assert session.query(Message).filter_by(conversation_id=conversation_id).count() == 2


def test_usage_migration_preserves_messages(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'migration.db'}"
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "20261008_0004")
    engine = create_database_engine(database_url)
    try:
        before = inspect(engine)
        original_columns = {column["name"] for column in before.get_columns("messages")}
        original_indexes = before.get_indexes("messages")
        original_foreign_keys = before.get_foreign_keys("messages")
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "INSERT INTO conversations (id, title) VALUES ('old', 'Old')"
            )
            connection.exec_driver_sql(
                "INSERT INTO messages (id, conversation_id, role, content) "
                "VALUES ('msg', 'old', 'assistant', 'Saved reply')"
            )

        command.upgrade(config, "head")
        command.check(config)
        columns = {column["name"]: column for column in inspect(engine).get_columns("messages")}
        assert set(columns) == original_columns | {"prompt_tokens", "completion_tokens"}
        for name in ("prompt_tokens", "completion_tokens"):
            assert columns[name]["nullable"]
            assert str(columns[name]["type"]) == "INTEGER"
        with engine.begin() as connection:
            assert connection.exec_driver_sql(
                "SELECT content, prompt_tokens, completion_tokens FROM messages WHERE id='msg'"
            ).one() == ("Saved reply", None, None)
            connection.exec_driver_sql(
                "UPDATE messages SET prompt_tokens=12, completion_tokens=4 WHERE id='msg'"
            )

        command.downgrade(config, "20261008_0004")
        after = inspect(engine)
        assert {column["name"] for column in after.get_columns("messages")} == original_columns
        assert after.get_indexes("messages") == original_indexes
        assert after.get_foreign_keys("messages") == original_foreign_keys
        with engine.connect() as connection:
            assert (
                connection.exec_driver_sql("SELECT content FROM messages").scalar() == "Saved reply"
            )
            assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
        command.upgrade(config, "head")
        with engine.connect() as connection:
            assert connection.exec_driver_sql(
                "SELECT content, prompt_tokens, completion_tokens FROM messages"
            ).one() == ("Saved reply", None, None)
    finally:
        engine.dispose()
