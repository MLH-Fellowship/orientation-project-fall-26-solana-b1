import logging
import time

from fastapi import Request


logger = logging.getLogger("app.request")


async def log_request(request: Request, call_next):
    start_time = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        process_time = time.perf_counter() - start_time
        logger.exception(
            "method=%s path=%s status_code=%s, duration_ms=%.2f",
            request.method,
            request.url.path,
            500,
            process_time * 1000,
        )
        raise
    process_time = time.perf_counter() - start_time
    logger.info(
        "method=%s path=%s status_code=%s, duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        process_time * 1000,
    )
    return response
