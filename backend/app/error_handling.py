from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

"""
Uses the existing error handlers as template to create new ones as new exception types arise. Luckily, FastAPI makes all this very easy for us, and this was the method that felt the most pythonic to handle exceptions in a modular manner without messing with main.py too much.
"""

error_table = {
        validation_error_handler: RequestValidationError,
        not_found_error_handler : HTTPException,
        unhandled_exception_handler:Exception
}


async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
            status_code=422,
            content={
                "error":{
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid Request!"
                    }
                }
    )

async def not_found_error_handler(request: Request, exc: HTTPException):
    return JSONResponse(
            status_code=exc.status_code,
            content={
                "error":{
                    "code":"NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR_GENERIC",
                    "message":str(exc.detail)
                    }
                },
            headers=exc.headers
            )

async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
            status_code=exc.status_code,
            content={"error":
                     {
                         "code":"UNHANDLED_EXCEPTION",
                         "message": "Internal server error or unknown exception occured."

                    }
                }
        )


def spawn_exception_handlers(app: FastAPI) -> None:
    for exception_type,handler in error_table.items():
        app.add_exception_handler(exception_type,handler)
    
