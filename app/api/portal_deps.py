from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.backend_config import settings
from app.core.security import session_digest
from app.db.models import User, UserSession
from app.db.session import get_db


def verify_origin(request: Request) -> None:
    """Cookie-authenticated writes are permitted only from configured browsers."""
    origin = request.headers.get("origin")
    if origin not in settings.ALLOWED_ORIGINS:
        raise HTTPException(403, "Request origin is not allowed")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    session = db.get(UserSession, session_digest(token)) if token else None
    if session:
        expires = session.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires > datetime.now(timezone.utc):
            user = db.get(User, session.user_id)
            if user:
                return user
    raise HTTPException(401, "Your session has expired. Please sign in again.")
