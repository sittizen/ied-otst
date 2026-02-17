from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import get_current_user
from app.models import AccountType, User
from app.schemas import GMRegisterRequest, LoginRequest, WhoAmIResponse
from app.security import (
    create_session,
    hash_password,
    normalize_email,
    revoke_session,
    verify_password,
)

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/gm/register", status_code=201, response_model=WhoAmIResponse)
def gm_register(payload: GMRegisterRequest, db: Session = Depends(get_db)) -> WhoAmIResponse:
    user = User(
        email=normalize_email(str(payload.email)),
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        account_type=AccountType.GM,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already exists") from e
    db.refresh(user)
    return WhoAmIResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        account_type=user.account_type,
    )


@router.post("/login", response_model=WhoAmIResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> WhoAmIResponse:
    email = normalize_email(str(payload.email))
    user = db.execute(select(User).where(User.email == email)).scalars().first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    sess = create_session(db, user)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=sess.id,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=settings.session_ttl_seconds,
        path="/",
    )
    return WhoAmIResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        account_type=user.account_type,
    )


@router.post("/logout")
def logout(
    response: Response,
    db: Session = Depends(get_db),
    session_id: str | None = Cookie(default=None, alias=settings.session_cookie_name),
) -> dict[str, str]:
    if session_id:
        revoke_session(db, session_id)

    response.delete_cookie(key=settings.session_cookie_name, path="/")
    return {"status": "ok"}


@router.get("/whoami", response_model=WhoAmIResponse)
def whoami(user: User = Depends(get_current_user)) -> WhoAmIResponse:
    return WhoAmIResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        account_type=user.account_type,
    )
