import time
import logging
import logging.config

from pathlib import Path
from fastapi import Request


def configure_logging():
    config_path = (Path(__file__).resolve().parents[2]
                   / "configs"
                   / "logging"
                   / "logging.conf"
                   )
    logging.config.fileConfig(
            config_path,
            disable_existing_loggers=False
            )


logger = logging.getLogger("app.request")

async def log_request(request: Request, call_next):
    start_time = time.perf_counter()
    try: 
        response = await call_next(request)
    except Exception:
        process_time = time.perf_counter() - start_time
        logger.info(
                "method=%s path=%s status_code=%s, duration_ms=%.2f",
                request.method,
                request.url.path,
                500,
                process_time * 1000
                )
        raise
    process_time = time.perf_counter() - start_time
    logger.info(
            "method=%s path=%s status_code=%s, duration_ms=%.2f",
            request.method,
            request.url.path,
            response.status_code,
            process_time * 1000
            )
    return response

