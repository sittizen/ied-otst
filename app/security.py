from __future__ import annotations

from datetime import datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerificationError, VerifyMismatchError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Session as DbSession
from app.models import User

password_hasher = PasswordHasher()


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    return str(password_hasher.hash(password))


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bool(password_hasher.verify(password_hash, password))
    except (VerifyMismatchError, InvalidHash, VerificationError):
        return False


def create_session(db: Session, user: User) -> DbSession:
    now = datetime.utcnow()
    sess = DbSession(
        user_id=user.id,
        expires_at=now + timedelta(seconds=settings.session_ttl_seconds),
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess


def revoke_session(db: Session, session_id: str) -> None:
    now = datetime.utcnow()
    sess = db.get(DbSession, session_id)
    if not sess or sess.revoked_at is not None:
        return
    sess.revoked_at = now
    db.add(sess)
    db.commit()


def get_user_for_session(db: Session, session_id: str) -> User | None:
    if not session_id:
        return None
    now = datetime.utcnow()
    stmt = (
        select(User)
        .join(DbSession, DbSession.user_id == User.id)
        .where(DbSession.id == session_id)
        .where(DbSession.revoked_at.is_(None))
        .where(DbSession.expires_at > now)
    )
    return db.execute(stmt).scalars().first()
