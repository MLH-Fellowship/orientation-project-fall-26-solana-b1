from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas import ErrorDetail, ErrorResponse


def error_response(
    status_code: int,
    code: str,
    message: str,
    headers: dict[str, str] | None = None,
    details: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    body = ErrorResponse(error=ErrorDetail(code=code, message=message, details=details))
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(body, exclude_none=True),
        headers=headers,
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return error_response(
        422,
        "VALIDATION ERROR",
        "Invalid Request!",
        details=exc.errors(),
    )


async def not_found_error_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    code = "NOT FOUND" if exc.status_code == 404 else "HTTP_GENERIC_ERROR"
    return error_response(exc.status_code, code, str(exc.detail), exc.headers)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_response(500, "UNHANDLED EXCEPTION", "Internal Server Error")


error_table = {
    RequestValidationError: validation_error_handler,
    StarletteHTTPException: not_found_error_handler,
    Exception: unhandled_exception_handler,
}


def spawn_exception_handlers(app: FastAPI) -> None:
    for exception_type, handler in error_table.items():
        app.add_exception_handler(exception_type, handler)
