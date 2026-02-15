from __future__ import annotations

import hashlib
import secrets
from collections.abc import Sequence
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import AccountType, Invite, Lobby, LobbyMember, LobbyMemberStatus, User
from app.schemas import (
    EmailInviteCreateRequest,
    EmailInviteCreateResponse,
    LobbyCreateRequest,
    LobbyDetailResponse,
    LobbyMemberResponse,
)
from app.security import normalize_email

router = APIRouter(prefix="/api/lobbies", tags=["lobbies"])


def _to_lobby_detail_response(lobby: Lobby, members: Sequence[LobbyMember]) -> LobbyDetailResponse:
    dm_count = sum(1 for member in members if member.is_dm)
    if dm_count != 1:
        raise HTTPException(status_code=500, detail="Lobby DM invariant violated")

    return LobbyDetailResponse(
        id=lobby.id,
        name=lobby.name,
        created_by_user_id=lobby.created_by_user_id,
        members=[
            LobbyMemberResponse(
                user_id=member.user_id,
                target_email=member.target_email,
                status=member.status,
                is_dm=member.is_dm,
            )
            for member in members
        ],
    )


@router.post("", status_code=201, response_model=LobbyDetailResponse)
def create_lobby(
    payload: LobbyCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LobbyDetailResponse:
    if user.account_type != AccountType.GM:
        raise HTTPException(status_code=403, detail="Only GMs can create lobbies")

    lobby = Lobby(name=payload.name, created_by_user_id=user.id)
    db.add(lobby)
    db.flush()

    dm_member = LobbyMember(
        lobby_id=lobby.id,
        user_id=user.id,
        target_email=None,
        status=LobbyMemberStatus.ACTIVE,
        is_dm=True,
    )
    db.add(dm_member)
    db.commit()

    db.refresh(lobby)
    db.refresh(dm_member)
    return _to_lobby_detail_response(lobby, [dm_member])


@router.get("/{lobby_id}", response_model=LobbyDetailResponse)
def get_lobby_details(
    lobby_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LobbyDetailResponse:
    lobby = db.get(Lobby, lobby_id)
    if not lobby:
        raise HTTPException(status_code=404, detail="Lobby not found")

    membership_stmt = select(LobbyMember).where(
        LobbyMember.lobby_id == lobby_id,
        LobbyMember.user_id == user.id,
    )
    membership = db.execute(membership_stmt).scalars().first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this lobby")

    members_stmt = select(LobbyMember).where(LobbyMember.lobby_id == lobby_id)
    members = db.execute(members_stmt).scalars().all()

    return _to_lobby_detail_response(lobby, members)


@router.post("/{lobby_id}/invites/email", status_code=201, response_model=EmailInviteCreateResponse)
def create_email_invite(
    lobby_id: str,
    payload: EmailInviteCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmailInviteCreateResponse:
    lobby = db.get(Lobby, lobby_id)
    if not lobby:
        raise HTTPException(status_code=404, detail="Lobby not found")

    dm_membership_stmt = select(LobbyMember).where(
        LobbyMember.lobby_id == lobby_id,
        LobbyMember.user_id == user.id,
        LobbyMember.is_dm.is_(True),
    )
    dm_membership = db.execute(dm_membership_stmt).scalars().first()
    if not dm_membership:
        raise HTTPException(status_code=403, detail="Only the lobby DM can create invites")

    target_email = normalize_email(str(payload.target_email))
    existing_user = db.execute(select(User).where(User.email == target_email)).scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail=(
                "Target email already belongs to an existing user. "
                "Use user_id invites for existing users."
            ),
        )

    member_stmt = select(LobbyMember).where(
        LobbyMember.lobby_id == lobby_id,
        LobbyMember.target_email == target_email,
    )
    member = db.execute(member_stmt).scalars().first()
    if member:
        member.status = LobbyMemberStatus.INVITED
        member.user_id = None
        member.is_dm = False
    else:
        member = LobbyMember(
            lobby_id=lobby_id,
            user_id=None,
            target_email=target_email,
            status=LobbyMemberStatus.INVITED,
            is_dm=False,
        )
        db.add(member)

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    invite = Invite(
        lobby_id=lobby_id,
        created_by_user_id=user.id,
        target_email=target_email,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(days=7),
        used_at=None,
    )
    db.add(invite)
    db.commit()

    base_url = str(request.base_url).rstrip("/")
    invite_url = f"{base_url}/api/invites/accept?token={raw_token}"
    return EmailInviteCreateResponse(invite_url=invite_url, expires_in_seconds=7 * 24 * 60 * 60)
