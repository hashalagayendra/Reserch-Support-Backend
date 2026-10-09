from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.portal_deps import get_current_user, verify_origin
from app.core.backend_config import settings
from app.core.security import hash_password, issue_session, session_digest, verify_password
from app.db.models import User, UserSession
from app.db.session import get_db
from app.schemas.portal import Credentials, UserResponse

router = APIRouter()
# Equal-cost password verification for unknown accounts.
_DUMMY_PASSWORD = hash_password("unused-comparison-password")


@router.post("/register", response_model=UserResponse, status_code=201,
             dependencies=[Depends(verify_origin)])
def register(data: Credentials, request: Request, response: Response, db: Session = Depends(get_db)):
    user = User(email=str(data.email), hashed_password=hash_password(data.password))
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "An account with this email already exists")
    issue_session(db, user.id, response, request.cookies.get(settings.SESSION_COOKIE_NAME))
    response.headers["Cache-Control"] = "no-store"
    return user


@router.post("/login", response_model=UserResponse, dependencies=[Depends(verify_origin)])
def login(data: Credentials, request: Request, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=str(data.email)).first()
    valid = verify_password(data.password, user.hashed_password if user else _DUMMY_PASSWORD)
    if not user or not valid:
        raise HTTPException(401, "Email or password is incorrect")
    issue_session(db, user.id, response, request.cookies.get(settings.SESSION_COOKIE_NAME))
    response.headers["Cache-Control"] = "no-store"
    return user


@router.get("/me", response_model=UserResponse)
def me(response: Response, user: User = Depends(get_current_user)):
    response.headers["Cache-Control"] = "no-store"
    return user


@router.post("/logout", status_code=204, dependencies=[Depends(verify_origin)])
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if token:
        db.query(UserSession).filter_by(token_hash=session_digest(token)).delete()
        db.commit()
    response.delete_cookie(settings.SESSION_COOKIE_NAME, path="/",
                           secure=settings.SESSION_COOKIE_SECURE, httponly=True, samesite="lax")
