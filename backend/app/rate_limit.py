import jwt
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.routes.auth import decode_access_token


def client_key(request: Request) -> str:
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() == "bearer" and token:
        try:
            return f"user:{decode_access_token(token)}"
        except (jwt.InvalidTokenError, KeyError, TypeError):
            pass
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(
    key_func=client_key,
    headers_enabled=True,
    storage_uri=settings.rate_limit_storage_uri,
    key_style="endpoint",
)
