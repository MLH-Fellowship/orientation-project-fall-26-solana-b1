"""Tests for the centralized HTTP request logging middleware."""

import asyncio
import logging
from pathlib import Path
from unittest.mock import Mock

import pytest
from starlette.requests import Request
from starlette.responses import Response

from app.middleware import logger as request_logging


def make_request(method: str, path: str) -> Request:
    """Build the smallest ASGI request needed by the middleware."""
    return Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("testclient", 50000),
        }
    )


def test_configures_a_file_handler_for_request_logs():
    request_logging.configure_logging()

    file_handlers = [
        handler
        for handler in logging.getLogger("app").handlers
        if isinstance(handler, logging.FileHandler)
    ]

    assert len(file_handlers) == 1
    assert Path(file_handlers[0].baseFilename).name == "app.log"


def test_logs_method_path_status_and_duration(monkeypatch):
    log_info = Mock()
    monkeypatch.setattr(request_logging.logger, "info", log_info)

    async def endpoint(_: Request) -> Response:
        return Response(status_code=201)

    response = asyncio.run(
        request_logging.log_request(make_request("POST", "/api/messages"), endpoint)
    )

    assert response.status_code == 201
    message, method, path, status_code, duration_ms = log_info.call_args.args
    assert message == "method=%s path=%s status_code=%s, duration=%.2f"
    assert method == "POST"
    assert path == "/api/messages"
    assert status_code == 201
    assert duration_ms >= 0


def test_logs_500_and_reraises_unhandled_errors(monkeypatch):
    log_info = Mock()
    monkeypatch.setattr(request_logging.logger, "info", log_info)

    async def failing_endpoint(_: Request) -> Response:
        raise RuntimeError("unexpected failure")

    with pytest.raises(RuntimeError, match="unexpected failure"):
        asyncio.run(
            request_logging.log_request(
                make_request("GET", "/api/failing"), failing_endpoint
            )
        )

    message, method, path, status_code, duration_ms = log_info.call_args.args
    assert message == "method=%s path=%s status_code=%s, duration=%.2f"
    assert method == "GET"
    assert path == "/api/failing"
    assert status_code == 500
    assert duration_ms >= 0
