"""Password hashing and opaque browser sessions; separate from SDK API keys."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Response
from sqlalchemy.orm import Session

from app.core.backend_config import settings
from app.db.models import UserSession


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=131072, r=8, p=1,
                            maxmem=256 * 1024 * 1024)
    return f"scrypt$131072$8$1${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, n, r, p, salt, expected = stored.split("$")
        if algorithm != "scrypt":
            return False
        digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=int(n), r=int(r), p=int(p),
                                maxmem=256 * 1024 * 1024)
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError):
        return False


def session_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_session(db: Session, user_id: int, response: Response, previous: str | None = None) -> None:
    if previous:
        db.query(UserSession).filter_by(token_hash=session_digest(previous)).delete()
    token = secrets.token_urlsafe(32)
    lifetime = timedelta(hours=settings.SESSION_HOURS)
    # Opportunistically remove expired sessions, preventing unbounded accumulation.
    db.query(UserSession).filter(UserSession.expires_at <= datetime.now(timezone.utc)).delete()
    db.add(UserSession(token_hash=session_digest(token), user_id=user_id,
                       expires_at=datetime.now(timezone.utc) + lifetime))
    db.commit()
    response.set_cookie(settings.SESSION_COOKIE_NAME, token, httponly=True,
                        secure=settings.SESSION_COOKIE_SECURE, samesite="lax",
                        max_age=int(lifetime.total_seconds()), path="/")
