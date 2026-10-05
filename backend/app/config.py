"""
Application configuration.

Loads settings from environment variables / a .env file. Add new
settings here as the project grows (e.g. rate limit thresholds,
alternate LLM providers, auth secrets).
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MLH LLM Fellowship Project"
    database_url: str = "sqlite:///./app.db"

    # LLM provider config. Fellows will extend this to support
    # multiple providers behind the abstract interface in app/llm/.
    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    system_prompt: str = ""

    # CORS - the Vite dev server default port
    frontend_origin: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("DATABASE_URL must not be empty")
        return value


settings = Settings()
