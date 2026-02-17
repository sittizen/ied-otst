from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class AccountType(enum.StrEnum):
    GM = "gm"
    PLAYER = "player"


class LobbyMemberStatus(enum.StrEnum):
    ACTIVE = "active"
    INVITED = "invited"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_type: Mapped[AccountType] = mapped_column(Enum(AccountType), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    sessions: Mapped[list[Session]] = relationship(back_populates="user")


Index("ix_users_email_unique", User.email, unique=True)


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User] = relationship(back_populates="sessions")


class Lobby(Base):
    __tablename__ = "lobbies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    created_by_user: Mapped[User] = relationship()
    members: Mapped[list[LobbyMember]] = relationship(back_populates="lobby")


class LobbyMember(Base):
    __tablename__ = "lobby_members"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lobby_id: Mapped[str] = mapped_column(String(36), ForeignKey("lobbies.id"), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, default=None)
    target_email: Mapped[str | None] = mapped_column(String(320), nullable=True, default=None)
    status: Mapped[LobbyMemberStatus] = mapped_column(
        Enum(LobbyMemberStatus), nullable=False, default=LobbyMemberStatus.ACTIVE
    )
    is_dm: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    lobby: Mapped[Lobby] = relationship(back_populates="members")
    user: Mapped[User | None] = relationship()


Index("ix_lobby_members_lobby_user_unique", LobbyMember.lobby_id, LobbyMember.user_id, unique=True)
Index(
    "ix_lobby_members_lobby_target_email_unique",
    LobbyMember.lobby_id,
    LobbyMember.target_email,
    unique=True,
)


class Invite(Base):
    __tablename__ = "invites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lobby_id: Mapped[str] = mapped_column(String(36), ForeignKey("lobbies.id"), nullable=False)
    created_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    target_email: Mapped[str] = mapped_column(String(320), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    lobby: Mapped[Lobby] = relationship()
    created_by_user: Mapped[User] = relationship()


Index("ix_invites_token_hash_unique", Invite.token_hash, unique=True)
