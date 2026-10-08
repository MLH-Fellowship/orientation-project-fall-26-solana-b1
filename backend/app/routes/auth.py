"""Authentication routes and dependencies."""

from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas import AuthCredentials, SignupOut, TokenOut, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)
password_hasher = PasswordHash.recommended()
dummy_hash = password_hasher.hash("not-a-real-password")


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def create_access_token(user: User) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode({"sub": user.id, "exp": expires_at}, settings.jwt_secret, algorithm="HS256")


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized()
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=["HS256"],
            options={"require": ["sub", "exp"]},
        )
        user = db.get(User, payload["sub"])
    except (InvalidTokenError, TypeError):
        raise unauthorized() from None
    if user is None:
        raise unauthorized()
    return user


@router.post(
    "/signup",
    response_model=SignupOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create an account",
    description="Create a user account. The user can then log in.",
)
def signup(payload: AuthCredentials, db: Session = Depends(get_db)):
    existing_user = db.scalar(select(User).where(func.lower(User.email) == payload.email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email is already registered"
        )

    user = User(email=payload.email, password_hash=password_hasher.hash(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email is already registered"
        ) from None
    return SignupOut()


@router.post(
    "/login",
    response_model=TokenOut,
    summary="Log in",
    description="Verify an email and password, then return a bearer token.",
)
def login(payload: AuthCredentials, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(func.lower(User.email) == payload.email))
    stored_hash = user.password_hash if user and user.password_hash else dummy_hash
    if not password_hasher.verify(payload.password, stored_hash) or user is None:
        raise unauthorized()
    return TokenOut(access_token=create_access_token(user))


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get the current user",
    description="Return the user identified by the bearer token.",
)
def current_user(user: Annotated[User, Depends(get_current_user)]):
    return user
