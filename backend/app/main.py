"""
FastAPI application entrypoint.

Run with:
    uvicorn app.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.logging import configure_logging
from app.routes import chat, health
from app.middleware.logger import log_request

Base.metadata.create_all(bind=engine)

configure_logging(settings)
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(log_request)

app.include_router(health.router, prefix="/api")
app.include_router(chat.router)
