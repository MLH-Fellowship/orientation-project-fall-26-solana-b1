"""
FastAPI application entrypoint.

Run with:
    uvicorn app.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import Base, engine
from app.error_handling import spawn_exception_handlers
from app.logging import configure_logging
from app.rate_limit import limiter
from app.routes import auth, chat, health
from app.middleware.logger import log_request

Base.metadata.create_all(bind=engine)

configure_logging(settings)
app = FastAPI(title=settings.app_name)
spawn_exception_handlers(app)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(log_request)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router)
app.include_router(chat.router)
