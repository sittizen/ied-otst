from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import User
from app.security import get_user_for_session


def get_current_user(
    db: Session = Depends(get_db),
    session_id: str | None = Cookie(default=None, alias=settings.session_cookie_name),
) -> User:
    user = get_user_for_session(db, session_id or "")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
