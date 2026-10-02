from fastapi.exceptions import RequestValidationError
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.schemas import ErrorDetail, ErrorResponse

"""
Uses the existing error handlers as template to create new ones as new exception types arise. Luckily, FastAPI makes all this very easy for us, and this was the method that felt the most pythonic to handle exceptions in a modular manner without cluttering up the main application. can you tell ive been doing more functional programming lately...
"""

def error_response(status_code: int, code:str,message:str,headers:dict[str,str] | None = None) -> JSONResponse:
    body = ErrorResponse(error=ErrorDetail(code=code,message=message))
    return JSONResponse(
            status_code=status_code,
            content=body.model_dump(),
            headers=headers
            )

async def validation_error_handler(request: Request, exc: RequestValidationError) -> error_response:
    return error_response(422,"VALIDATION ERROR", "Invalid Request!")

async def not_found_error_handler(request: Request, exc: StarletteHTTPException) -> error_response:
    code = "NOT FOUND" if exc.status_code == 404 else "HTTP_GENERIC_ERROR"
    return error_response(exc.status_code,code,str(exc.detail),exc.headers)
async def unhandled_exception_handler(request: Request, exc: Exception) -> error_response:
    return error_response(500, "UNHANDLED EXCEPTION","Internal Server Error/Unknown Exception")

#TODO: handle more errors

error_table = {
        RequestValidationError: validation_error_handler,
        StarletteHTTPException: not_found_error_handler,
        Exception: unhandled_exception_handler,
}

def spawn_exception_handlers(app: FastAPI) -> None:
    for exception_type, handler in error_table.items():
        app.add_exception_handler(exception_type, handler)
    
